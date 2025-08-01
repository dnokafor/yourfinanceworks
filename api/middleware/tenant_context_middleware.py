import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from models.database import set_tenant_context, clear_tenant_context, get_master_db, get_tenant_context
from models.models import MasterUser
from services.tenant_database_manager import tenant_db_manager
import jwt
import os

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# Function-based middleware for tenant context
async def tenant_context_middleware(request: Request, call_next):
    clear_tenant_context()
    logger.info(f"Middleware processing: {request.method} {request.url.path}")
    logger.info(f"Authorization header: {'Present' if request.headers.get('Authorization') else 'Missing'}")
    
    # Skip tenant context for Slack endpoints
    if request.url.path.startswith("/api/v1/slack/"):
        logger.info(f"Skipping tenant context for Slack endpoint: {request.url.path}")
        return await call_next(request)
    
    # Skip tenant context for specific endpoints that don't need it or handle it manually
    skip_tenant_paths = [
        "/health", "/", "/docs", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/me",
        "/api/v1/auth/check-email-availability", "/api/v1/auth/request-password-reset",
        "/api/v1/auth/reset-password"
    ]
    
    if request.url.path in skip_tenant_paths:
        return await call_next(request)
    
    try:
        # Extract tenant context from authentication token
        try:
            authorization = request.headers.get("Authorization")
            header_tenant_id = request.headers.get("X-Tenant-ID")
            logger.info(f"Auth header: {authorization[:20] if authorization else 'None'}...")
            
            if not authorization or not authorization.startswith("Bearer "):
                logger.info("No valid Bearer token found")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication required. Please log in."}
                )
            
            logger.info("Processing Bearer token")
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            logger.info(f"Token payload email: {email}")
            
            if email:
                logger.info(f"Decoded email from token: {email}")
                master_db = next(get_master_db())
                try:
                    user = master_db.query(MasterUser).filter(MasterUser.email == email).first()
                    if user and user.tenant_id:
                        logger.info(f"User found: {user.email}, Tenant ID: {user.tenant_id}")
                        # Cross-check header_tenant_id if present
                        if header_tenant_id and str(header_tenant_id) != str(user.tenant_id):
                            logger.warning(f"Tenant ID header mismatch: header={header_tenant_id}, user={user.tenant_id}")
                            logger.warning(f"User email: {email}, User tenant_id: {user.tenant_id}")
                            return JSONResponse(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                content={"detail": "Invalid or expired token. Please log in again."}
                            )
                        # Check if tenant database exists before setting context
                        try:
                            tenant_session = tenant_db_manager.get_tenant_session(user.tenant_id)()
                            from sqlalchemy import text
                            tenant_session.execute(text("SELECT 1"))
                            tenant_session.close()
                            tenant_id = user.tenant_id
                            set_tenant_context(tenant_id)
                            logger.info(f"✅ Successfully set tenant context to {tenant_id} for user {email}")
                        except Exception as e:
                            logger.warning(f"Tenant database for tenant {user.tenant_id} does not exist or is inaccessible: {e}")
                            # Try to create the tenant database
                            from models.models import Tenant
                            tenant = master_db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
                            if tenant:
                                success = tenant_db_manager.create_tenant_database(user.tenant_id, tenant.name)
                                if success:
                                    logger.info(f"Successfully created tenant database for tenant {user.tenant_id}")
                                    set_tenant_context(user.tenant_id)
                                else:
                                    logger.error(f"Failed to create tenant database for tenant {user.tenant_id}")
                            else:
                                logger.error(f"Tenant {user.tenant_id} not found in master database")
                    else:
                        logger.warning(f"User not found or tenant_id missing for email: {email}")
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Invalid or expired token. Please log in again."}
                        )
                finally:
                    master_db.close()
                    logger.debug(f"Master DB session closed.")
            else:
                logger.debug("Email not found in JWT payload.")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token. Please log in again."}
                )

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token. Please log in again."}
            )
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        # Ensure tenant context is set before proceeding
        current_tenant = get_tenant_context()
        logger.info(f"Current tenant context before handler: {current_tenant}")
        
        logger.info(f"Calling next middleware/handler for {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    finally:
        # Don't clear tenant context here - let it persist for the request duration
        pass 