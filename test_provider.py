#!/usr/bin/env python3
"""Test script to debug AI provider selection."""

import os
from dotenv import load_dotenv
from chat.providers import get_provider

def main():
    print("🔍 Testing AI provider selection...")
    
    # Load environment variables
    load_dotenv()
    
    # Test environment variable
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY present: {bool(gemini_key)}")
    if gemini_key:
        print(f"Key starts with: {gemini_key[:10]}...")
    
    # Test provider creation
    provider = get_provider('gemini')
    print(f"Provider type: {type(provider).__name__}")
    print(f"Provider available: {provider.is_available()}")
    
    # Test actual API call
    if provider.is_available():
        print("Testing API call...")
        try:
            response = provider.call_ai_model("Hello! Can you tell me what 2+2 equals?")
            print(f"Response: {response}")
        except Exception as e:
            print(f"API call failed: {e}")
    else:
        print("Provider not available, skipping API test")

if __name__ == "__main__":
    main()
