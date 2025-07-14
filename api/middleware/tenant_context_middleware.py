from fastapi import Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import jwt
import logging

from models.database import set_tenant_context, clear_tenant_context, get_master_db
from models.models import MasterUser
from services.tenant_database_manager import tenant_db_manager

logger = logging.getLogger(__name__)

# JWT settings - should match your auth configuration
import os
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically sets the tenant context based on the authenticated user.
    This ensures all database operations are routed to the correct tenant database.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
        
    async def dispatch(self, request: Request, call_next):
        # Clear any existing tenant context
        clear_tenant_context()
        
        try:
            # Extract tenant context from authenticated user
            await self._set_tenant_context_from_auth(request)
            
            # Process the request
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in tenant context middleware: {e}")
            # Continue without tenant context on error
            response = await call_next(request)
            return response
        
        finally:
            # Always clear context after request
            clear_tenant_context()
    
    async def _set_tenant_context_from_auth(self, request: Request):
        """Extract tenant context from authentication token"""
        try:
            # Get authorization header
            authorization = request.headers.get("Authorization")
            
            if not authorization or not authorization.startswith("Bearer "):
                logger.debug("No authorization header found")
                return
            
            # Extract token
            token = authorization.split(" ")[1]
            
            # Decode JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            
            if not email:
                logger.debug("No email found in token")
                return
            
            # Get user from master database
            master_db = next(get_master_db())
            try:
                user = master_db.query(MasterUser).filter(MasterUser.email == email).first()
                
                if user and user.tenant_id:
                    # Check if tenant database exists before setting context
                    if self._ensure_tenant_database_exists(user.tenant_id):
                        # Set tenant context
                        set_tenant_context(user.tenant_id)
                        logger.debug(f"Set tenant context to {user.tenant_id} for user {email}")
                    else:
                        logger.warning(f"Tenant database for tenant {user.tenant_id} does not exist. Skipping tenant context.")
                else:
                    logger.debug(f"User {email} not found or has no tenant_id")
                    
            finally:
                master_db.close()
                
        except jwt.InvalidTokenError:
            logger.debug("Invalid JWT token")
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
    
    def _ensure_tenant_database_exists(self, tenant_id: int) -> bool:
        """
        Check if tenant database exists and create it if it doesn't.
        Returns True if database exists or was created successfully.
        """
        try:
            # Try to get a connection to the tenant database
            tenant_session = tenant_db_manager.get_tenant_session(tenant_id)()
            
            # Test the connection with a simple query
            from sqlalchemy import text
            tenant_session.execute(text("SELECT 1"))
            tenant_session.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"Tenant database for tenant {tenant_id} does not exist or is inaccessible: {e}")
            
            # Try to create the tenant database
            try:
                logger.info(f"Attempting to create missing tenant database for tenant {tenant_id}")
                
                # Get tenant info from master database
                master_db = next(get_master_db())
                try:
                    from models.models import Tenant
                    tenant = master_db.query(Tenant).filter(Tenant.id == tenant_id).first()
                    
                    if tenant:
                        success = tenant_db_manager.create_tenant_database(tenant_id, tenant.name)
                        if success:
                            logger.info(f"Successfully created tenant database for tenant {tenant_id}")
                            return True
                        else:
                            logger.error(f"Failed to create tenant database for tenant {tenant_id}")
                            return False
                    else:
                        logger.error(f"Tenant {tenant_id} not found in master database")
                        return False
                        
                finally:
                    master_db.close()
                    
            except Exception as create_error:
                logger.error(f"Error creating tenant database for tenant {tenant_id}: {create_error}")
                return False
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the endpoint is public (doesn't require tenant context)"""
        public_endpoints = [
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/docs",
            "/openapi.json",
            "/",
            "/health",
            "/super-admin"  # Super admin endpoints don't need tenant context
        ]
        
        return any(path.startswith(endpoint) for endpoint in public_endpoints) 