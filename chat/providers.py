"""AI provider interfaces for different chat models."""

import os
from abc import ABC, abstractmethod
from typing import Optional, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore
    CLAUDE_AVAILABLE = False


class AIProvider(ABC):
    """Abstract base class for AI model providers."""
    
    @abstractmethod
    def call_ai_model(self, prompt: str) -> str:
        """Call the AI model with a prompt and return the response."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (API key set, dependencies installed)."""
        pass
    
    def stream_ai_model(self, prompt: str):
        """Stream AI model response token by token. Override in subclasses that support streaming."""
        # Default implementation: yield the full response at once
        response = self.call_ai_model(prompt)
        yield response


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model: Optional[Any] = None
        
        if self.api_key and GEMINI_AVAILABLE and genai is not None:
            # Use getattr to avoid type checker issues with dynamic imports
            configure_func = getattr(genai, 'configure', None)
            model_class = getattr(genai, 'GenerativeModel', None)
            
            if configure_func and model_class:
                configure_func(api_key=self.api_key)
                # Use the current Gemini model name
                self.model = model_class('gemini-1.5-flash')
    
    def call_ai_model(self, prompt: str) -> str:
        """Call Gemini API with the given prompt."""
        if not self.is_available():
            raise RuntimeError("Gemini provider not available. Check API key and dependencies.")
        
        try:
            if self.model is None:
                raise RuntimeError("Gemini model not initialized")
            
            # Use getattr for dynamic method access
            generate_content = getattr(self.model, 'generate_content', None)
            if not generate_content:
                raise RuntimeError("generate_content method not available")
                
            response = generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")
    
    def stream_ai_model(self, prompt: str):
        """Stream Gemini API response token by token."""
        if not self.is_available():
            raise RuntimeError("Gemini provider not available. Check API key and dependencies.")
        
        try:
            if self.model is None:
                raise RuntimeError("Gemini model not initialized")
            
            # Use getattr for dynamic method access
            generate_content = getattr(self.model, 'generate_content', None)
            if not generate_content:
                raise RuntimeError("generate_content method not available")
            
            # Try streaming, fall back to regular if not supported
            try:
                response = generate_content(prompt, stream=True)
                current_text = ""
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        new_text = chunk.text
                        # Yield only the new part
                        if new_text.startswith(current_text):
                            yield new_text[len(current_text):]
                            current_text = new_text
                        else:
                            yield new_text
                            current_text = new_text
            except Exception:
                # Fall back to non-streaming
                response = generate_content(prompt)
                yield response.text.strip()
                
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return GEMINI_AVAILABLE and self.api_key is not None and self.model is not None


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model
        self.client: Optional[Any] = None
        
        if self.api_key and OPENAI_AVAILABLE and OpenAI is not None:
            self.client = OpenAI(api_key=self.api_key)
        
    def call_ai_model(self, prompt: str) -> str:
        """Call OpenAI API with the given prompt."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available. Check API key and dependencies.")
        
        try:
            if self.client is None:
                raise RuntimeError("OpenAI client not initialized")
                
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                raise RuntimeError("No response content received from OpenAI")
                
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
    def stream_ai_model(self, prompt: str):
        """Stream OpenAI API response token by token."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available. Check API key and dependencies.")
        
        try:
            if self.client is None:
                raise RuntimeError("OpenAI client not initialized")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return OPENAI_AVAILABLE and self.api_key is not None and self.client is not None


class MockProvider(AIProvider):
    """Mock provider for testing without API keys."""
    
    def call_ai_model(self, prompt: str) -> str:
        """Return a mock response."""
        responses = [
            "I understand your question. Let me think about that...",
            "That's an interesting point. Here's my perspective:",
            "Based on the information provided, I would say:",
            "Let me analyze that for you:",
            "That's a great question! My response is:"
        ]
        
        # Simple response based on prompt content
        if "capital" in prompt.lower():
            return "The capital of France is Paris, located in the north-central part of the country."
        elif "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello! I'm an AI assistant ready to help you with your questions."
        elif "?" in prompt:
            return f"{responses[0]} {prompt.split('?')[0]}? Let me provide some insights on that topic."
        else:
            return f"{responses[1]} {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
    
    def stream_ai_model(self, prompt: str):
        """Stream mock response word by word for demonstration."""
        import time
        response = self.call_ai_model(prompt)
        words = response.split()
        
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield f" {word}"
            time.sleep(0.05)  # Simulate streaming delay
    
    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True


class ClaudeProvider(AIProvider):
    """Anthropic Claude AI provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model
        self.client: Optional[Any] = None
        
        if self.api_key and CLAUDE_AVAILABLE and anthropic is not None:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Claude client: {e}")
                self.client = None
    
    def call_ai_model(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        if not self.client:
            return "❌ Claude API not available. Please check your API key and internet connection."
        
        try:
            # Claude API expects messages format
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract text from response
            if message.content and len(message.content) > 0:
                return message.content[0].text
            else:
                return "🤖 No response from Claude."
                
        except Exception as e:
            return f"❌ Claude API error: {str(e)}"
    
    def stream_ai_model(self, prompt: str):
        """Stream Claude API response token by token."""
        if not self.client:
            yield "❌ Claude API not available. Please check your API key and internet connection."
            return
        
        try:
            # Claude streaming API
            stream = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                        yield chunk.delta.text
                elif chunk.type == "content_block_start":
                    # Start of content block
                    continue
                elif chunk.type == "content_block_stop":
                    # End of content block
                    break
                    
        except Exception as e:
            yield f"❌ Claude streaming error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Claude provider is available."""
        return (
            CLAUDE_AVAILABLE and 
            self.api_key is not None and 
            self.client is not None
        )


def get_provider(provider_name: str, **kwargs) -> AIProvider:
    """Factory function to get an AI provider by name."""
    providers = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "mock": MockProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
    
    provider_class = providers[provider_name]
    provider = provider_class(**kwargs)
    
    if not provider.is_available():
        print(f"⚠️  {provider_name} provider not available, falling back to mock provider")
        return MockProvider()
    
    return provider
