import logging
from fastapi import Request
from models.database import set_tenant_context, clear_tenant_context, get_master_db
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
    try:
        # Extract tenant context from authentication token
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
                if email:
                    master_db = next(get_master_db())
                    try:
                        user = master_db.query(MasterUser).filter(MasterUser.email == email).first()
                        if user and user.tenant_id:
                            # Check if tenant database exists before setting context
                            try:
                                tenant_session = tenant_db_manager.get_tenant_session(user.tenant_id)()
                                from sqlalchemy import text
                                tenant_session.execute(text("SELECT 1"))
                                tenant_session.close()
                                set_tenant_context(user.tenant_id)
                                logger.debug(f"Set tenant context to {user.tenant_id} for user {email}")
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
                    finally:
                        master_db.close()
        except jwt.InvalidTokenError:
            logger.debug("Invalid JWT token")
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
        response = await call_next(request)
        return response
    finally:
        clear_tenant_context() 