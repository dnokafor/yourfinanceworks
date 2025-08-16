#!/usr/bin/env python3
"""
Test the PDF AI priority system inside the container
"""

import os
import sys
from types import SimpleNamespace

# Add the app directory to the path
sys.path.append('/app')

def test_priority_system():
    print("=== PDF AI Priority System Test (Inside Container) ===\n")
    
    # Simulate the exact logic from pdf_processor.py
    active_config = None
    config_source = "manual"
    
    # 1. Check if AI config is set up (simulate no AI config)
    ai_config = None  # Simulate no AI config in database
    
    if ai_config:
        active_config = ai_config
        config_source = "ai_config"
        print("✓ Using AI configuration from database")
    else:
        # 2. Check if env vars are set up
        env_model = os.getenv("LLM_MODEL_INVOICES") or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL")
        env_api_base = os.getenv("LLM_API_BASE") or os.getenv("OLLAMA_API_BASE")
        env_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        print("Environment variables check:")
        print(f"  LLM_MODEL_INVOICES: {os.getenv('LLM_MODEL_INVOICES')}")
        print(f"  LLM_MODEL: {os.getenv('LLM_MODEL')}")
        print(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
        print(f"  LLM_API_BASE: {os.getenv('LLM_API_BASE')}")
        print(f"  OLLAMA_API_BASE: {os.getenv('OLLAMA_API_BASE')}")
        print(f"  LLM_API_KEY: {'***' if os.getenv('LLM_API_KEY') else None}")
        print(f"  OPENAI_API_KEY: {'***' if os.getenv('OPENAI_API_KEY') else None}")
        print(f"  Final values - model: {env_model}, api_base: {env_api_base}, api_key: {'***' if env_api_key else None}")
        
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
            print(f"✓ Using AI configuration from environment variables: provider={provider_name}, model={env_model or 'gpt-oss:latest'}, api_base={env_api_base}")
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
            print("✗ No environment variables found, using manual fallback AI configuration")
    
    print(f"\n=== RESULT ===")
    print(f"Config Source: {config_source}")
    print(f"Provider: {active_config.provider_name}")
    print(f"Model: {active_config.model_name}")
    print(f"API Base: {active_config.provider_url}")
    print(f"Has API Key: {bool(active_config.api_key)}")
    print(f"Tested: {getattr(active_config, 'tested', False)}")
    
    if config_source == "env_vars":
        print("\n✅ SUCCESS: Environment variables are being used correctly!")
        print("The PDF upload feature will use the environment configuration.")
    elif config_source == "manual":
        print("\n❌ ISSUE: Falling back to manual configuration despite environment variables being set.")
        print("This suggests there might be an issue with the environment variable detection logic.")
    else:
        print(f"\n✅ SUCCESS: Using {config_source} configuration.")

if __name__ == "__main__":
    test_priority_system()