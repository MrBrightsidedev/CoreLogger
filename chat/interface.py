"""Main chat interface for conversational AI interaction."""

import sys
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from chat.providers import AIProvider, get_provider
from chat.utils import (
    analyze_emotion, 
    calculate_importance, 
    extract_tags, 
    clean_ai_response,
    format_chat_display
)
from models.thought import ThoughtCreate
from services.logger import ThoughtLogger
from db.session import DatabaseManager


class ChatInterface:
    """Main chat interface for AI conversation."""
    
    def __init__(
        self, 
        provider: Optional[AIProvider] = None,
        provider_name: str = "mock",
        db_manager: Optional[DatabaseManager] = None,
        thought_logger: Optional[ThoughtLogger] = None,
        enable_history: bool = False,
        enable_streaming: bool = False
    ):
        self.console = Console()
        
        # Use provided provider or create one
        if provider:
            self.provider = provider
        else:
            self.provider = get_provider(provider_name)
            
        self.db_manager = db_manager
        self.thought_logger = thought_logger
        self.conversation_active = False
        
        # Conversation history for context
        self.enable_history = enable_history
        self.conversation_history: List[dict] = []
        self.max_history_length = 10  # Keep last 10 exchanges
        
        # Streaming support
        self.enable_streaming = enable_streaming
        
        # Display provider info
        provider_type = type(self.provider).__name__
        if provider_type == "MockProvider":
            self.console.print("💡 Using mock AI provider (no API key required)", style="yellow")
        else:
            self.console.print(f"🤖 Using {provider_type}", style="green")
        
        if self.enable_history:
            self.console.print("🧠 Conversation history enabled", style="blue")
        if self.enable_streaming:
            self.console.print("⚡ Streaming responses enabled", style="cyan")
    
    def log_thought_from_chat(
        self, 
        content: str, 
        category: str, 
        is_ai_response: bool = False
    ) -> None:
        """Log a chat message as a thought."""
        if not (self.db_manager and self.thought_logger):
            return  # Skip logging if no database connection
        
        try:
            with self.db_manager.get_session() as session:
                # Analyze the message
                emotion = analyze_emotion(content)
                importance = calculate_importance(content, is_ai_response)
                tags = extract_tags(content, is_ai_response)
                
                # Create thought
                thought = ThoughtCreate(
                    category=category,  # type: ignore
                    content=content,
                    tags=tags,
                    emotion=emotion,
                    importance=importance
                )
                
                # Log to database
                self.thought_logger.create_thought(session, thought)
                
        except Exception as e:
            # Don't let logging errors break the chat
            self.console.print(f"⚠️  Logging error: {e}", style="red dim")
    
    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        if not self.enable_history:
            return
        
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only the last N exchanges
        if len(self.conversation_history) > self.max_history_length * 2:  # *2 for user+assistant pairs
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
    
    def get_context_for_ai(self, current_prompt: str) -> str:
        """Get conversation context for AI providers that don't support message history."""
        if not self.enable_history or not self.conversation_history:
            return current_prompt
        
        # For providers that don't support message arrays, build context string
        context_parts = []
        for msg in self.conversation_history[-6:]:  # Last 6 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        context_parts.append(f"User: {current_prompt}")
        return "\n".join(context_parts)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        if self.enable_history:
            self.console.print("🧠 Conversation history cleared", style="yellow")
    
    def display_history(self) -> None:
        """Display conversation history."""
        if not self.enable_history:
            self.console.print("⚠️  Conversation history is disabled", style="yellow")
            return
        
        if not self.conversation_history:
            self.console.print("📝 No conversation history yet", style="dim")
            return
        
        history_text = Text()
        for i, msg in enumerate(self.conversation_history[-10:], 1):  # Show last 10
            role = "👤 You" if msg["role"] == "user" else "🤖 AI"
            timestamp = msg.get("timestamp", "")
            if timestamp:
                # Format timestamp nicely
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                    history_text.append(f"{role} ({time_str}):\n", style="bold")
                except:
                    history_text.append(f"{role}:\n", style="bold")
            else:
                history_text.append(f"{role}:\n", style="bold")
            
            content = msg["content"][:200] + ("..." if len(msg["content"]) > 200 else "")
            history_text.append(f"{content}\n\n")
        
        panel = Panel(history_text, title="Conversation History", border_style="magenta")
        self.console.print(panel)
    
    def get_streaming_response(self, prompt: str) -> str:
        """Get streaming AI response with real-time display."""
        from rich.live import Live
        from rich.text import Text
        
        self.console.print("🤔 AI is thinking...", style="dim")
        
        # Initialize response display
        response_text = Text()
        response_text.append("AI: ", style="bold green")
        
        full_response = ""
        
        try:
            with Live(response_text, console=self.console, refresh_per_second=10) as live:
                for chunk in self.provider.stream_ai_model(prompt):
                    if chunk:
                        full_response += chunk
                        # Update the displayed text
                        new_text = Text()
                        new_text.append("AI: ", style="bold green")
                        new_text.append(full_response)
                        live.update(new_text)
            
            # Final newline after streaming
            self.console.print()
            return clean_ai_response(full_response)
            
        except Exception as e:
            # Fall back to regular response
            self.console.print("\n⚠️ Streaming failed, using regular response", style="yellow")
            response = self.provider.call_ai_model(prompt)
            response = clean_ai_response(response)
            self.console.print(f"[bold green]AI[/bold green]: {response}")
            return response
    
    def display_welcome(self) -> None:
        """Display welcome message and instructions."""
        welcome_text = Text()
        welcome_text.append("🧠 CoreLogger Chat Interface\n", style="bold blue")
        welcome_text.append("Ask questions, have conversations, and log thoughts automatically!\n\n")
        welcome_text.append("Commands:\n", style="bold")
        welcome_text.append("  • Type your message and press Enter\n")
        welcome_text.append("  • '/quit' or '/exit' to end the conversation\n")
        welcome_text.append("  • '/help' for more commands\n")
        
        if self.db_manager and self.thought_logger:
            welcome_text.append("\n✅ Database logging enabled", style="green")
        else:
            welcome_text.append("\n⚠️  Database logging disabled", style="yellow")
        
        panel = Panel(welcome_text, title="Welcome", border_style="blue")
        self.console.print(panel)
        self.console.print()
    
    def display_help(self) -> None:
        """Display help information."""
        help_text = Text()
        help_text.append("Available Commands:\n", style="bold")
        help_text.append("  /quit, /exit    - End the conversation\n")
        help_text.append("  /help           - Show this help message\n")
        help_text.append("  /stats          - Show conversation statistics\n")
        help_text.append("  /clear          - Clear the screen\n")
        if self.enable_history:
            help_text.append("  /history        - Show conversation history\n")
            help_text.append("  /clear-history  - Clear conversation history\n")
        help_text.append("\nJust type your message to chat with the AI!", style="dim")
        
        panel = Panel(help_text, title="Help", border_style="yellow")
        self.console.print(panel)
    
    def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if command was processed."""
        command = user_input.lower().strip()
        
        if command in ["/quit", "/exit"]:
            self.console.print("👋 Goodbye! Your thoughts have been logged.", style="green")
            return True
        
        elif command == "/help":
            self.display_help()
            return True
        
        elif command == "/clear":
            self.console.clear()
            self.display_welcome()
            return True
        
        elif command == "/history":
            self.display_history()
            return True
        
        elif command == "/clear-history":
            self.clear_history()
            return True
        
        elif command == "/stats":
            self.display_stats()
            return True
        
        return False
    
    def display_stats(self) -> None:
        """Display conversation statistics."""
        if not (self.db_manager and self.thought_logger):
            self.console.print("⚠️  Statistics not available (database logging disabled)", style="yellow")
            return
        
        try:
            with self.db_manager.get_session() as session:
                # Get recent thoughts from this chat session (rough estimate)
                from models.thought import ThoughtQuery
                query = ThoughtQuery(
                    page=1,
                    size=50,
                    min_importance=None,
                    max_importance=None,
                    order_by="timestamp",
                    order_desc=True
                )
                response = self.thought_logger.list_thoughts(session, query)
                
                user_thoughts = len([t for t in response.thoughts if "user-input" in t.tags])
                ai_thoughts = len([t for t in response.thoughts if "ai-response" in t.tags])
                
                stats_text = Text()
                stats_text.append(f"Recent conversation activity:\n", style="bold")
                stats_text.append(f"  User messages: {user_thoughts}\n")
                stats_text.append(f"  AI responses: {ai_thoughts}\n")
                stats_text.append(f"  Total logged thoughts: {response.total}\n")
                
                panel = Panel(stats_text, title="Statistics", border_style="cyan")
                self.console.print(panel)
                
        except Exception as e:
            self.console.print(f"⚠️  Error retrieving statistics: {e}", style="red")
    
    def start_conversation(self) -> None:
        """Start the main conversation loop."""
        self.conversation_active = True
        self.display_welcome()
        
        try:
            while self.conversation_active:
                # Get user input
                try:
                    user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n👋 Conversation ended.")
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        if user_input.lower() in ["/quit", "/exit"]:
                            break
                        continue
                
                # Add user input to history
                self.add_to_history("user", user_input)
                
                # Log user message
                self.log_thought_from_chat(
                    content=user_input,
                    category="perception",
                    is_ai_response=False
                )
                
                # Get AI response
                try:
                    # Use context if history is enabled
                    prompt_to_use = user_input
                    if self.enable_history:
                        prompt_to_use = self.get_context_for_ai(user_input)
                    
                    if self.enable_streaming:
                        ai_response = self.get_streaming_response(prompt_to_use)
                    else:
                        self.console.print("🤔 AI is thinking...", style="dim")
                        ai_response = self.provider.call_ai_model(prompt_to_use)
                        ai_response = clean_ai_response(ai_response)
                        
                        # Display AI response
                        self.console.print(f"\n[bold green]AI[/bold green]: {ai_response}")
                    
                    # Add AI response to history
                    self.add_to_history("assistant", ai_response)
                    
                    # Log AI response
                    self.log_thought_from_chat(
                        content=ai_response,
                        category="reflection",
                        is_ai_response=True
                    )
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    self.console.print(f"\n[bold red]AI[/bold red]: {error_msg}")
                    
                    # Log the error
                    self.log_thought_from_chat(
                        content=f"AI Error: {str(e)}",
                        category="error",
                        is_ai_response=True
                    )
        
        except KeyboardInterrupt:
            self.console.print("\n\n👋 Conversation interrupted. Goodbye!")
        
        finally:
            self.conversation_active = False


def create_chat_interface(
    provider_name: str = "mock",
    database_url: Optional[str] = None,
    api_key: Optional[str] = None,
    enable_history: bool = False,
    enable_streaming: bool = False
) -> ChatInterface:
    """Factory function to create a chat interface with database connection."""
    
    # Set up database connection if URL provided
    db_manager = None
    thought_logger = None
    
    if database_url:
        try:
            db_manager = DatabaseManager(database_url)
            thought_logger = ThoughtLogger()
            
            # Test database connection
            with db_manager.get_session() as session:
                pass  # Just test the connection
                
        except Exception as e:
            print(f"⚠️  Database connection failed: {e}")
            print("💡 Continuing without database logging...")
            db_manager = None
            thought_logger = None
    
    # Create provider with API key if provided
    provider_kwargs = {}
    if api_key:
        provider_kwargs["api_key"] = api_key
    
    provider = get_provider(provider_name, **provider_kwargs)
    
    return ChatInterface(
        provider=provider,
        db_manager=db_manager,
        thought_logger=thought_logger,
        enable_history=enable_history,
        enable_streaming=enable_streaming
    )
