import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import settings
from db import db_manager, init_database
from db.models import ThoughtModel
from models.thought import ThoughtCreate, ThoughtQuery, ThoughtUpdate
from services import thought_formatter
from services.logger import ThoughtLogger
from chat.interface import create_chat_interface
from services.nlp_analyzer import EnhancedThoughtScorer
from sqlalchemy import String

app = typer.Typer(
    name="corelogger",
    help="CoreLogger - Eidos OS Logging Module CLI",
    add_completion=True,  # Enable auto-completion
)
console = Console()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
)

# Auto-completion helpers
def complete_categories():
    """Return available thought categories for auto-completion."""
    return ["reflection", "idea", "todo", "goal", "observation", "insight", "question", "memory"]

def complete_providers():
    """Return available AI providers for auto-completion."""
    return ["gemini", "openai", "claude", "mock"]

def complete_emotions():
    """Return available emotions for auto-completion."""
    return ["happy", "sad", "excited", "anxious", "calm", "frustrated", "motivated", "confused", "confident", "neutral"]

def complete_export_formats():
    """Return available export formats for auto-completion."""
    return ["json", "csv"]


@app.command()
def chat(
    model: str = typer.Option(
        "mock", 
        "--model", 
        "-m", 
        help="AI model provider",
        autocompletion=complete_providers
    ),
    no_logging: bool = typer.Option(
        False, 
        "--no-logging", 
        help="Disable database logging for this chat session"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for the selected AI provider (overrides environment variables)"
    ),
    history: bool = typer.Option(
        False,
        "--history",
        help="Enable conversation memory/history for contextual responses"
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        help="Enable real-time streaming responses (token-by-token)"
    )
):
    """Start an interactive chat session with an AI model.
    
    This command starts a conversational interface where you can chat with an AI model.
    Each message (both yours and the AI's) will be automatically logged as thoughts
    in the CoreLogger database for later analysis and retrieval.
    
    Examples:
        corelogger chat                    # Use mock AI (no API key needed)
        corelogger chat --model gemini     # Use Google Gemini (requires API key)
        corelogger chat --model openai     # Use OpenAI GPT (requires API key)
        corelogger chat --no-logging       # Chat without logging to database
    """
    console.print("🚀 Starting CoreLogger Chat Interface...\n")
    
    # Determine database URL
    database_url = None if no_logging else db_manager.database_url
    
    try:
        # Provide API key hint if needed
        if model != "mock" and not api_key:
            env_var = "GEMINI_API_KEY" if model == "gemini" else "OPENAI_API_KEY"
            console.print(f"💡 [dim]Tip: Set {env_var} environment variable or use --api-key flag[/dim]")
        
        # Create and start chat interface
        chat_interface = create_chat_interface(
            provider_name=model,
            database_url=database_url,
            api_key=api_key,
            enable_history=history,
            enable_streaming=stream
        )
        
        chat_interface.start_conversation()
        
    except KeyboardInterrupt:
        console.print("\n👋 Chat session ended.")
    except Exception as e:
        console.print(f"[red]Error starting chat: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    database_url: Optional[str] = typer.Option(None, "--db", help="Database URL override"),
):
    """CoreLogger CLI - Log and manage AI thoughts and reflections."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("[dim]Verbose mode enabled[/dim]")
    
    if database_url:
        db_manager.database_url = database_url
        console.print(f"[dim]Using database: {database_url}[/dim]")
    
    # Initialize database if needed
    try:
        init_database()
    except Exception as e:
        console.print(f"[red]Error initializing database: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def log(
    content: str = typer.Argument(..., help="Content of the thought"),
    category: str = typer.Option(
        "reflection", 
        "--category", 
        "-c", 
        help="Category of thought",
        autocompletion=complete_categories
    ),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags for the thought"),
    emotion: Optional[str] = typer.Option(
        None, 
        "--emotion", 
        "-e", 
        help="Emotional state",
        autocompletion=complete_emotions
    ),
    importance: Optional[float] = typer.Option(
        None, 
        "--importance", 
        "-i", 
        min=0.0, 
        max=1.0, 
        help="Importance score (0.0-1.0)"
    ),
):
    """Log a new thought or reflection."""
    
    # Validate category - now more flexible
    valid_categories = complete_categories()
    if category not in valid_categories:
        console.print(f"[yellow]Warning: Uncommon category '{category}'. Valid options: {', '.join(valid_categories)}[/yellow]")
        if not Confirm.ask("Continue with this category?"):
            raise typer.Exit(1)
    
    try:
        thought_data = ThoughtCreate(
            category=category,  # type: ignore
            content=content,
            tags=tags or [],
            emotion=emotion,
            importance=importance,
        )
        
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.create_thought(session, thought_data)
        
        console.print("[green]Thought logged successfully![/green]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging thought: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def perception(
    content: str = typer.Argument(..., help="Perception content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    emotion: Optional[str] = typer.Option(None, "--emotion", "-e", help="Emotional state"),
    importance: Optional[float] = typer.Option(None, "--importance", "-i", min=0.0, max=1.0),
):
    """Log a perception thought."""
    
    try:
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.log_perception(
                session, content, tags=tags or [], emotion=emotion, importance=importance
            )
        
        console.print("[green]Perception logged![/green]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging perception: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def reflect(
    content: str = typer.Argument(..., help="Reflection content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    emotion: Optional[str] = typer.Option(None, "--emotion", "-e", help="Emotional state"),
    importance: Optional[float] = typer.Option(None, "--importance", "-i", min=0.0, max=1.0),
):
    """Log a reflection thought."""
    
    try:
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.log_reflection(
                session, content, tags=tags or [], emotion=emotion, importance=importance
            )
        
        console.print("[green]Reflection logged![/green]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging reflection: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def decide(
    content: str = typer.Argument(..., help="Decision content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    emotion: Optional[str] = typer.Option(None, "--emotion", "-e", help="Emotional state"),
    importance: Optional[float] = typer.Option(None, "--importance", "-i", min=0.0, max=1.0),
):
    """Log a decision thought."""
    
    try:
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.log_decision(
                session, content, tags=tags or [], emotion=emotion, importance=importance
            )
        
        console.print("[green]Decision logged![/green]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging decision: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def tick(
    content: str = typer.Argument(..., help="System tick content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    importance: Optional[float] = typer.Option(None, "--importance", "-i", min=0.0, max=1.0),
):
    """Log a system tick thought."""
    
    try:
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.log_tick(
                session, content, tags=tags or [], importance=importance
            )
        
        console.print("[green]System tick logged![/green]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging tick: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def error(
    content: str = typer.Argument(..., help="Error content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    importance: Optional[float] = typer.Option(None, "--importance", "-i", min=0.0, max=1.0),
):
    """Log an error thought."""
    
    try:
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.log_error(
                session, content, tags=tags or [], importance=importance
            )
        
        console.print("[red]Error logged![/red]")
        console.print(thought_formatter.format_thought(thought, detailed=True))
        
    except Exception as e:
        console.print(f"[red]Error logging error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_thoughts(
    category: Optional[str] = typer.Option(
        None, 
        "--category", 
        "-c", 
        help="Filter by category"
    ),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Filter by tags"),
    emotion: Optional[str] = typer.Option(None, "--emotion", "-e", help="Filter by emotion"),
    min_importance: Optional[float] = typer.Option(None, "--min-importance", min=0.0, max=1.0),
    max_importance: Optional[float] = typer.Option(None, "--max-importance", min=0.0, max=1.0),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search in content"),
    page: int = typer.Option(1, "--page", "-p", min=1, help="Page number"),
    page_size: int = typer.Option(10, "--size", min=1, max=100, help="Page size"),
    table: bool = typer.Option(False, "--table", help="Display as table"),
    stats: bool = typer.Option(False, "--stats", help="Show statistics"),
):
    """List thoughts with optional filtering."""
    
    # Validate category if provided
    if category is not None:
        valid_categories = ["perception", "reflection", "decision", "tick", "error"]
        if category not in valid_categories:
            console.print(f"[red]Invalid category. Must be one of: {', '.join(valid_categories)}[/red]")
            raise typer.Exit(1)
    
    try:
        query = ThoughtQuery(
            page=page,
            size=page_size,
            category=category,  # type: ignore
            tags=tags,
            emotion=emotion,
            min_importance=min_importance or 0.0,
            max_importance=max_importance or 1.0,
            search_term=search,
        )
        
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            response = logger.list_thoughts(session, query)
        
        if stats:
            console.print(thought_formatter.format_stats_summary(response))
        elif table:
            console.print(thought_formatter.format_thoughts_table(response))
        else:
            console.print(thought_formatter.format_thoughts_list(response))
        
    except Exception as e:
        console.print(f"[red]Error listing thoughts: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    thought_id: str = typer.Argument(..., help="Thought ID to display"),
):
    """Show a specific thought by ID."""
    
    try:
        thought_uuid = UUID(thought_id)
        
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.get_thought(session, thought_uuid)
        
        if thought:
            console.print(thought_formatter.format_thought(thought, detailed=True))
        else:
            console.print(f"[red]Thought with ID {thought_id} not found[/red]")
            raise typer.Exit(1)
        
    except ValueError:
        console.print(f"[red]Invalid UUID format: {thought_id}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error retrieving thought: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    thought_id: str = typer.Argument(..., help="Thought ID to update"),
    content: Optional[str] = typer.Option(None, "--content", help="New content"),
    category: Optional[str] = typer.Option(
        None, 
        "--category", 
        help="New category"
    ),
    add_tags: Optional[List[str]] = typer.Option(None, "--add-tag", help="Tags to add"),
    emotion: Optional[str] = typer.Option(None, "--emotion", help="New emotion"),
    importance: Optional[float] = typer.Option(None, "--importance", min=0.0, max=1.0),
):
    """Update an existing thought."""
    
    # Validate category if provided
    if category is not None:
        valid_categories = ["perception", "reflection", "decision", "tick", "error"]
        if category not in valid_categories:
            console.print(f"[red]Invalid category. Must be one of: {', '.join(valid_categories)}[/red]")
            raise typer.Exit(1)
    
    try:
        thought_uuid = UUID(thought_id)
        
        # Get current thought
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            current_thought = logger.get_thought(session, thought_uuid)
            if not current_thought:
                console.print(f"[red]Thought with ID {thought_id} not found[/red]")
                raise typer.Exit(1)
            
            # Prepare update data
            update_dict = {}
            
            if content is not None:
                update_dict["content"] = content
            if category is not None:
                update_dict["category"] = category  # type: ignore
            if add_tags is not None:
                # Merge with existing tags  
                existing_tags_set = set(current_thought.tags)
                new_tags_set = set(add_tags)
                combined_tags_set = existing_tags_set.union(new_tags_set)
                merged_tags = list(combined_tags_set)
                update_dict["tags"] = merged_tags
            if emotion is not None:
                update_dict["emotion"] = emotion
            if importance is not None:
                update_dict["importance"] = importance
            
            update_data = ThoughtUpdate(**update_dict)
            
            # Update thought
            updated_thought = logger.update_thought(session, thought_uuid, update_data)
            
            if updated_thought:
                console.print("[green]Thought updated successfully![/green]")
                console.print(thought_formatter.format_thought(updated_thought, detailed=True))
            else:
                console.print(f"[red]Failed to update thought {thought_id}[/red]")
                raise typer.Exit(1)
        
    except ValueError:
        console.print(f"[red]Invalid UUID format: {thought_id}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error updating thought: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    thought_id: str = typer.Argument(..., help="Thought ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a thought by ID."""
    
    try:
        thought_uuid = UUID(thought_id)
        
        # Show thought before deletion
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            thought = logger.get_thought(session, thought_uuid)
            if not thought:
                console.print(f"[red]Thought with ID {thought_id} not found[/red]")
                raise typer.Exit(1)
            
            console.print("Thought to be deleted:")
            console.print(thought_formatter.format_thought(thought, detailed=True))
            
            # Confirm deletion
            if not force:
                confirm = Prompt.ask(
                    "Are you sure you want to delete this thought?", 
                    choices=["y", "n"], 
                    default="n"
                )
                if confirm.lower() != "y":
                    console.print("[yellow]Deletion cancelled[/yellow]")
                    return
            
            # Delete thought
            success = logger.delete_thought(session, thought_uuid)
            
            if success:
                console.print("[green]Thought deleted successfully![/green]")
            else:
                console.print(f"[red]Failed to delete thought {thought_id}[/red]")
                raise typer.Exit(1)
        
    except ValueError:
        console.print(f"[red]Invalid UUID format: {thought_id}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error deleting thought: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    format_type: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format: json or csv"
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output filename (auto-generated if not provided)"
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category"
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tag"
    ),
    emotion: Optional[str] = typer.Option(
        None,
        "--emotion",
        "-e",
        help="Filter by emotion"
    ),
    days: Optional[int] = typer.Option(
        None,
        "--days",
        "-d",
        help="Export thoughts from last N days"
    ),
    stats: bool = typer.Option(
        False,
        "--stats",
        help="Show export statistics"
    )
):
    """Export thoughts to JSON or CSV format.
    
    Export all or filtered thoughts to a file for backup, analysis, or sharing.
    
    Examples:
        corelogger export                              # Export all to JSON
        corelogger export --format csv                 # Export all to CSV
        corelogger export --category reflection        # Export only reflections
        corelogger export --tag programming --days 7   # Export programming thoughts from last week
        corelogger export --output my_thoughts.json    # Export to specific file
    """
    from services.exporter import ThoughtExporter
    from datetime import timedelta
    
    console.print("📦 Exporting thoughts...\n")
    
    try:
        # Build query filters
        query_filters = ThoughtQuery(
            page=1, 
            size=10000,
            min_importance=0.0,
            max_importance=1.0,
            order_by="timestamp",
            order_desc=True
        )
        
        if category:
            query_filters.category = category
        if tag:
            query_filters.tag = tag
        if emotion:
            query_filters.emotion = emotion
        if days:
            query_filters.created_after = datetime.now() - timedelta(days=days)
        
        # Generate output filename if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = "json" if format_type.lower() == "json" else "csv"
            output = f"corelogger_export_{timestamp}.{extension}"
        
        # Initialize exporter
        exporter = ThoughtExporter()
        
        # Export thoughts - using synchronous approach
        with db_manager.get_session() as session:
            logger = ThoughtLogger()
            
            # Get thoughts using our synchronous logger
            thoughts_response = logger.get_thoughts(session, query_filters)
            thoughts = thoughts_response.thoughts if hasattr(thoughts_response, 'thoughts') else []
            
            if not thoughts:
                console.print("[yellow]No thoughts found matching the criteria[/yellow]")
                return
            
            # Simple export implementation
            import json
            import csv
            
            if format_type.lower() == "json":
                export_data = []
                for thought in thoughts:
                    export_data.append({
                        "id": str(thought.id),
                        "category": thought.category,
                        "content": thought.content,
                        "tags": thought.tags,
                        "emotion": thought.emotion,
                        "importance": thought.importance,
                        "timestamp": thought.timestamp.isoformat()
                    })
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
            elif format_type.lower() == "csv":
                with open(output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Category", "Content", "Tags", "Emotion", "Importance", "Timestamp"])
                    for thought in thoughts:
                        writer.writerow([
                            str(thought.id),
                            thought.category,
                            thought.content,
                            ",".join(thought.tags) if thought.tags else "",
                            thought.emotion or "",
                            thought.importance or "",
                            thought.timestamp.isoformat()
                        ])
            
            console.print(f"✅ [green]Exported {len(thoughts)} thoughts to {output}[/green]")
            
            # Show statistics if requested
            if stats and len(thoughts) > 0:
                console.print("\n📊 Export Statistics:")
                console.print(f"  Total thoughts: {len(thoughts)}")
                
                # Category breakdown
                categories = {}
                emotions = {}
                total_importance = 0
                importance_count = 0
                
                for thought in thoughts:
                    categories[thought.category] = categories.get(thought.category, 0) + 1
                    if thought.emotion:
                        emotions[thought.emotion] = emotions.get(thought.emotion, 0) + 1
                    if thought.importance:
                        total_importance += thought.importance
                        importance_count += 1
                
                if categories:
                    console.print("  Categories:")
                    for cat, count in categories.items():
                        console.print(f"    {cat}: {count}")
                
                if emotions:
                    console.print("  Emotions:")
                    for emotion, count in list(emotions.items())[:5]:
                        console.print(f"    {emotion}: {count}")
                
                if importance_count > 0:
                    avg_importance = total_importance / importance_count
                    console.print(f"  Average importance: {avg_importance:.2f}")
            
    except Exception as e:
        console.print(f"[red]Export error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """Start interactive mode for easier thought logging."""
    console.print("[bold blue]🧠 CoreLogger Interactive Mode[/bold blue]")
    console.print("Type 'help' for commands, 'quit' to exit\n")
    
    init_database()
    session = db_manager.SessionLocal()
    logger = ThoughtLogger()
    
    try:
        while True:
            command = Prompt.ask("[bold cyan]CoreLogger[/bold cyan]").strip().lower()
            
            if command in ['quit', 'exit', 'q']:
                console.print("👋 Goodbye!")
                break
            elif command == 'help':
                show_interactive_help()
            elif command == 'log':
                interactive_log_thought(session, logger)
            elif command == 'list':
                interactive_list_thoughts(session, logger)
            elif command == 'stats':
                interactive_show_stats(session, logger)
            elif command == 'nlp':
                interactive_nlp_analysis(session, logger)
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type 'help' for available commands")
                
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    finally:
        session.close()


def show_interactive_help():
    """Show help for interactive mode."""
    help_table = Table(title="Interactive Commands")
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description", style="white")
    
    help_table.add_row("log", "Log a new thought interactively")
    help_table.add_row("list", "Show recent thoughts")
    help_table.add_row("stats", "Show thought statistics")
    help_table.add_row("nlp", "Analyze a thought with NLP")
    help_table.add_row("help", "Show this help")
    help_table.add_row("quit/exit/q", "Exit interactive mode")
    
    console.print(help_table)


def interactive_log_thought(session, logger):
    """Interactive thought logging."""
    content = Prompt.ask("💭 What's on your mind?")
    if not content.strip():
        console.print("[red]Content cannot be empty[/red]")
        return
    
    categories = complete_categories()
    category = Prompt.ask(
        "📂 Category",
        choices=categories,
        default="reflection"
    )
    
    tags_input = Prompt.ask("🏷️  Tags (comma-separated)", default="")
    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
    
    if settings.enable_emotions:
        emotions = complete_emotions()
        emotion = Prompt.ask(
            "😊 Emotion",
            choices=emotions + ["none"],
            default="none"
        )
        emotion = emotion if emotion != "none" else None
    else:
        emotion = None
    
    importance_input = Prompt.ask("⭐ Importance (0.0-1.0, or 'auto')", default="auto")
    importance = None if importance_input == "auto" else float(importance_input)
    
    try:
        thought_data = ThoughtCreate(
            category=category,
            content=content,
            tags=tags,
            emotion=emotion,
            importance=importance
        )
        
        thought = logger.create_thought(session, thought_data)
        console.print(f"✅ [green]Thought logged with ID: {thought.id}[/green]")
        
        # Show NLP analysis if auto-importance was used
        if importance_input == "auto":
            nlp_analysis = logger.get_nlp_analysis(session, thought.id)
            if nlp_analysis:
                console.print(f"🎯 Auto-calculated importance: {nlp_analysis['importance_score']:.3f}")
                console.print(f"📝 Keywords: {', '.join(nlp_analysis['keywords'][:5])}")
                
    except Exception as e:
        console.print(f"[red]Error logging thought: {e}[/red]")


def interactive_list_thoughts(session, logger):
    """Interactive thought listing."""
    limit = int(Prompt.ask("📊 How many recent thoughts?", default="10"))
    
    query = ThoughtQuery(
        page=1, 
        size=limit,
        min_importance=0.0,
        max_importance=1.0,
        order_by="timestamp",
        order_desc=True
    )
    thoughts = logger.list_thoughts(session, query)
    
    if thoughts.thoughts:
        table = Table(title=f"Recent {limit} Thoughts")
        table.add_column("ID", style="dim")
        table.add_column("Category", style="cyan")
        table.add_column("Content", style="white")
        table.add_column("Importance", style="yellow")
        
        for thought in thoughts.thoughts:
            content_preview = thought.content[:50] + "..." if len(thought.content) > 50 else thought.content
            importance_str = f"{thought.importance:.2f}" if thought.importance else "N/A"
            table.add_row(
                str(thought.id)[:8],
                thought.category,
                content_preview,
                importance_str
            )
        
        console.print(table)
    else:
        console.print("[yellow]No thoughts found[/yellow]")


def interactive_show_stats(session, logger):
    """Interactive statistics display."""
    total = logger.count_thoughts(session)
    console.print(f"📊 Total thoughts: {total}")
    
    if total > 0:
        recent_query = ThoughtQuery(
            page=1, 
            size=5,
            min_importance=0.0,
            max_importance=1.0,
            order_by="timestamp",
            order_desc=True
        )
        recent = logger.list_thoughts(session, recent_query)
        
        console.print(f"📅 Most recent: {recent.thoughts[0].timestamp if recent.thoughts else 'None'}")
        
        # Show category distribution
        # This would require additional query methods in the logger
        console.print("📂 Categories: [dim]Feature coming soon...[/dim]")


def interactive_nlp_analysis(session, logger):
    """Interactive NLP analysis of a thought."""
    thought_id_input = Prompt.ask("🔍 Enter thought ID (first 8 characters)")
    
    try:
        # Find thought by partial ID
        thoughts = session.query(ThoughtModel)\
            .filter(ThoughtModel.id.cast(String).like(f"{thought_id_input}%"))\
            .all()
        
        if not thoughts:
            console.print("[red]No thought found with that ID[/red]")
            return
        
        if len(thoughts) > 1:
            console.print(f"[yellow]Multiple thoughts found ({len(thoughts)}), using first match[/yellow]")
        
        thought = thoughts[0]
        # The thought.id from database is already a UUID
        analysis = logger.get_nlp_analysis(session, thought.id)
        
        if analysis:
            console.print(Panel(f"[bold]NLP Analysis for Thought[/bold]\n\n"
                              f"📝 Content: {thought.content[:100]}...\n"
                              f"⭐ Importance: {analysis['importance_score']:.3f}\n"
                              f"🎭 Sentiment: {analysis['sentiment']} ({analysis['sentiment_score']:.2f})\n"
                              f"🔄 Novelty: {analysis['novelty_score']:.3f}\n"
                              f"🧩 Complexity: {analysis['complexity_score']:.3f}\n"
                              f"📊 Entropy: {analysis['entropy']:.2f}\n"
                              f"🔁 Repetition: {analysis['repetition_score']:.3f}\n"
                              f"📈 Words: {analysis['word_count']}\n"
                              f"🏷️  Keywords: {', '.join(analysis['keywords'][:8])}",
                              title="🧠 NLP Analysis"))
        else:
            console.print("[red]Could not generate NLP analysis[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def analyze(
    thought_id: str = typer.Argument(..., help="Thought ID to analyze"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed metrics")
):
    """Analyze a thought with enhanced NLP."""
    init_database()
    session = db_manager.SessionLocal()
    logger = ThoughtLogger()
    
    try:
        # Find thought by partial ID
        thoughts = session.query(ThoughtModel)\
            .filter(ThoughtModel.id.cast(String).like(f"{thought_id}%"))\
            .all()
        
        if not thoughts:
            console.print(f"[red]No thought found with ID starting with: {thought_id}[/red]")
            raise typer.Exit(1)
        
        if len(thoughts) > 1:
            console.print(f"[yellow]Multiple thoughts found ({len(thoughts)}), using first match[/yellow]")
        
        thought = thoughts[0]
        # Get analysis using the actual UUID from the database model
        analysis = logger.get_nlp_analysis(session, UUID(str(thought.id)))
        
        if analysis:
            # Basic analysis
            console.print(f"[bold blue]📝 Thought Analysis[/bold blue]")
            console.print(f"ID: {thought.id}")
            console.print(f"Content: {thought.content}")
            console.print(f"Category: {thought.category}")
            console.print(f"Created: {thought.timestamp}")
            console.print()
            
            # NLP Metrics
            console.print(f"[bold green]🧠 NLP Metrics[/bold green]")
            console.print(f"⭐ Importance Score: {analysis['importance_score']:.3f}")
            console.print(f"🎭 Sentiment: {analysis['sentiment']} ({analysis['sentiment_score']:.2f})")
            console.print(f"🔄 Novelty Score: {analysis['novelty_score']:.3f}")
            console.print(f"🧩 Complexity Score: {analysis['complexity_score']:.3f}")
            console.print(f"📊 Information Entropy: {analysis['entropy']:.2f}")
            console.print(f"🔁 Repetition Score: {analysis['repetition_score']:.3f}")
            console.print()
            
            # Content Statistics
            console.print(f"[bold yellow]📈 Content Statistics[/bold yellow]")
            console.print(f"Word Count: {analysis['word_count']}")
            console.print(f"Character Count: {analysis['char_count']}")
            console.print(f"Keywords: {', '.join(analysis['keywords'][:10])}")
            console.print()
            
            if detailed and 'importance_metrics' in analysis:
                console.print(f"[bold cyan]🔍 Detailed Importance Breakdown[/bold cyan]")
                metrics = analysis['importance_metrics']
                console.print(f"Length Factor: {metrics['length_factor']:.3f}")
                console.print(f"Complexity Factor: {metrics['complexity_factor']:.3f}")
                console.print(f"Novelty Factor: {metrics['novelty_factor']:.3f}")
                console.print(f"Sentiment Factor: {metrics['sentiment_factor']:.3f}")
                console.print(f"Entropy Factor: {metrics['entropy_factor']:.3f}")
                console.print()
                
                if analysis['keyword_density']:
                    console.print(f"[bold magenta]🏷️  Keyword Density[/bold magenta]")
                    for keyword, density in list(analysis['keyword_density'].items())[:5]:
                        console.print(f"{keyword}: {density:.3f}")
        else:
            console.print("[red]Could not generate NLP analysis[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


@app.command()
def recalculate_importance(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of thoughts to recalculate"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Recalculate importance scores using enhanced NLP analysis."""
    if not confirm:
        if not Confirm.ask(f"Recalculate importance scores for {limit or 'all'} thoughts?"):
            console.print("Cancelled.")
            raise typer.Exit(0)
    
    init_database()
    session = db_manager.SessionLocal()
    logger = ThoughtLogger()
    
    try:
        console.print("🔄 Recalculating importance scores...")
        updated_count = logger.recalculate_importance_bulk(session, limit)
        console.print(f"✅ [green]Updated {updated_count} thoughts[/green]")
        
    except Exception as e:
        console.print(f"[red]Recalculation error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    app()
