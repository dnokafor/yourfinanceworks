#!/usr/bin/env python3
"""
Test script to check environment variables for LLM configuration
"""

import os

def test_env_vars():
    print("=== Environment Variables Test ===\n")
    
    env_vars = [
        "LLM_MODEL_INVOICES",
        "LLM_MODEL", 
        "OLLAMA_MODEL",
        "LLM_API_BASE",
        "OLLAMA_API_BASE",
        "LLM_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    print("Checking environment variables:")
    for var in env_vars:
        value = os.getenv(var)
        if "API_KEY" in var and value:
            print(f"  {var}: ***")
        else:
            print(f"  {var}: {value}")
    
    print("\nPriority logic test:")
    env_model = os.getenv("LLM_MODEL_INVOICES") or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL")
    env_api_base = os.getenv("LLM_API_BASE") or os.getenv("OLLAMA_API_BASE")
    env_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    print(f"  Final model: {env_model}")
    print(f"  Final api_base: {env_api_base}")
    print(f"  Final api_key: {'***' if env_api_key else None}")
    
    if env_model or env_api_base or env_api_key:
        print("  Result: Would use ENVIRONMENT VARIABLES")
        
        # Determine provider
        if env_api_base or os.getenv("OLLAMA_MODEL"):
            provider_name = "ollama"
        elif env_api_key:
            provider_name = "openai"
        else:
            provider_name = "ollama"
        
        print(f"  Provider: {provider_name}")
    else:
        print("  Result: Would use MANUAL FALLBACK")

if __name__ == "__main__":
    test_env_vars()