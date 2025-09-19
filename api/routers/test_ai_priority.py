from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
from types import SimpleNamespace
import logging

from models.database import get_db
from models.models import MasterUser
from models.models_per_tenant import AIConfig as AIConfigModel
from routers.auth import get_current_user

router = APIRouter(prefix="/test", tags=["testing"])
logger = logging.getLogger(__name__)

@router.get("/ai-priority")
async def test_ai_priority(
    db: Session = Depends(get_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """Test endpoint to check AI configuration priority system"""
    
    # Priority system: AI config → env vars → manual fallback
    active_config = None
    config_source = "manual"
    
    # 1. Check if AI config is set up and tested
    ai_config = db.query(AIConfigModel).filter(
        AIConfigModel.is_active == True,
        AIConfigModel.tested == True
    ).first()
    
    if ai_config:
        active_config = ai_config
        config_source = "ai_config"
        logger.info("Using AI configuration from database")
    else:
        # 2. Check if env vars are set up
        env_model = os.getenv("LLM_MODEL_INVOICES") or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL")
        env_api_base = os.getenv("LLM_API_BASE") or os.getenv("OLLAMA_API_BASE")
        env_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Debug logging
        logger.info(f"Environment variables check:")
        logger.info(f"  LLM_MODEL_INVOICES: {os.getenv('LLM_MODEL_INVOICES')}")
        logger.info(f"  LLM_MODEL: {os.getenv('LLM_MODEL')}")
        logger.info(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
        logger.info(f"  LLM_API_BASE: {os.getenv('LLM_API_BASE')}")
        logger.info(f"  OLLAMA_API_BASE: {os.getenv('OLLAMA_API_BASE')}")
        logger.info(f"  LLM_API_KEY: {'***' if os.getenv('LLM_API_KEY') else None}")
        logger.info(f"  OPENAI_API_KEY: {'***' if os.getenv('OPENAI_API_KEY') else None}")
        logger.info(f"  Final values - model: {env_model}, api_base: {env_api_base}, api_key: {'***' if env_api_key else None}")
        
        if env_model or env_api_base or env_api_key:
            # Determine provider from env vars
            if env_api_base or os.getenv("OLLAMA_MODEL"):
                provider_name = "ollama"
            elif env_api_key:
                provider_name = "openai"
            else:
                provider_name = "ollama"  # Default fallback
            
            active_config = SimpleNamespace(
                provider_name=provider_name,
                provider_url=env_api_base,
                api_key=env_api_key,
                model_name=env_model or "gpt-oss:latest",
                is_active=True,
                tested=True,
            )
            config_source = "env_vars"
            logger.info(f"Using AI configuration from environment variables: provider={provider_name}, model={env_model or 'gpt-oss:latest'}, api_base={env_api_base}")
        else:
            # 3. Manual fallback - use basic defaults
            active_config = SimpleNamespace(
                provider_name="ollama",
                provider_url="http://localhost:11434",
                api_key=None,
                model_name="gpt-oss:latest",
                is_active=True,
                tested=False,  # Mark as untested for manual config
            )
            config_source = "manual"
            logger.info("No environment variables found, using manual fallback AI configuration")
    
    return {
        "config_source": config_source,
        "config": {
            "provider_name": active_config.provider_name,
            "provider_url": active_config.provider_url,
            "model_name": active_config.model_name,
            "has_api_key": bool(active_config.api_key),
            "is_active": active_config.is_active,
            "tested": getattr(active_config, 'tested', False)
        },
        "environment_variables": {
            "LLM_MODEL_INVOICES": os.getenv("LLM_MODEL_INVOICES"),
            "LLM_MODEL": os.getenv("LLM_MODEL"),
            "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
            "LLM_API_BASE": os.getenv("LLM_API_BASE"),
            "OLLAMA_API_BASE": os.getenv("OLLAMA_API_BASE"),
            "LLM_API_KEY": "***" if os.getenv("LLM_API_KEY") else None,
            "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else None
        }
    }