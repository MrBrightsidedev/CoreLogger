from datetime import datetime
from typing import List, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models.thought import Thought, ThoughtsListResponse


class ThoughtFormatter:
    """Service for formatting thoughts for display."""
    
    def __init__(self):
        self.console = Console()
    
    def format_thought(self, thought: Thought, detailed: bool = False) -> Union[str, Panel]:
        """Format a single thought for display."""
        
        # Format timestamp
        timestamp_str = thought.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create basic info
        info_parts = [
            f"ID: {thought.id}",
            f"Time: {timestamp_str}",
            f"Category: {thought.category.upper()}",
        ]
        
        if thought.importance is not None:
            info_parts.append(f"Importance: {thought.importance:.2f}")
        
        if thought.emotion:
            info_parts.append(f"Emotion: {thought.emotion}")
        
        if thought.tags:
            tags_str = ", ".join(thought.tags)
            info_parts.append(f"Tags: {tags_str}")
        
        # Create formatted output
        if detailed:
            # Detailed view with rich formatting
            panel_title = f"Thought - {thought.category.title()}"
            content_lines = [
                f"[bold]ID:[/bold] {thought.id}",
                f"[bold]Timestamp:[/bold] {timestamp_str}",
                f"[bold]Category:[/bold] {thought.category.upper()}",
            ]
            
            if thought.importance is not None:
                importance_color = self._get_importance_color(thought.importance)
                content_lines.append(
                    f"[bold]Importance:[/bold] [{importance_color}]{thought.importance:.2f}[/{importance_color}]"
                )
            
            if thought.emotion:
                content_lines.append(f"[bold]Emotion:[/bold] {thought.emotion}")
            
            if thought.tags:
                tags_str = ", ".join(f"[cyan]{tag}[/cyan]" for tag in thought.tags)
                content_lines.append(f"[bold]Tags:[/bold] {tags_str}")
            
            content_lines.append("")
            content_lines.append(f"[bold]Content:[/bold]")
            content_lines.append(thought.content)
            
            return Panel("\n".join(content_lines), title=panel_title, expand=False)
        else:
            # Simple text format
            info_str = " | ".join(info_parts)
            content_preview = self._truncate_content(thought.content, 100)
            return f"{info_str}\n{content_preview}\n{'-' * 80}"
    
    def format_thoughts_list(self, response: ThoughtsListResponse) -> str:
        """Format a list of thoughts for display."""
        
        if not response.thoughts:
            return "No thoughts found."
        
        # Create summary header
        summary = [
            f"Found {response.total} thoughts (Page {response.page}/{response.total_pages})",
            f"Showing {len(response.thoughts)} results",
            "=" * 80,
        ]
        
        # Format each thought
        formatted_thoughts = []
        for thought in response.thoughts:
            formatted_thoughts.append(self.format_thought(thought, detailed=False))
        
        return "\n".join(summary + formatted_thoughts)
    
    def format_thoughts_table(self, response: ThoughtsListResponse) -> Table:
        """Format thoughts as a rich table."""
        
        table = Table(title=f"Thoughts (Page {response.page}/{response.total_pages})")
        
        table.add_column("Time", style="dim", width=16)
        table.add_column("Category", style="bold", width=12)
        table.add_column("Content", width=50)
        table.add_column("Tags", style="cyan", width=20)
        table.add_column("Emotion", style="yellow", width=12)
        table.add_column("Importance", justify="center", width=10)
        
        for thought in response.thoughts:
            # Format timestamp
            time_str = thought.timestamp.strftime("%m-%d %H:%M:%S")
            
            # Format content preview
            content_preview = self._truncate_content(thought.content, 45)
            
            # Format tags
            tags_str = ", ".join(thought.tags[:3])  # Show first 3 tags
            if len(thought.tags) > 3:
                tags_str += "..."
            
            # Format importance with color
            importance_str = ""
            if thought.importance is not None:
                color = self._get_importance_color(thought.importance)
                importance_str = f"[{color}]{thought.importance:.2f}[/{color}]"
            
            table.add_row(
                time_str,
                thought.category.upper(),
                content_preview,
                tags_str or "-",
                thought.emotion or "-",
                importance_str or "-",
            )
        
        return table
    
    def format_stats_summary(self, response: ThoughtsListResponse) -> str:
        """Format basic statistics about thoughts."""
        
        if not response.thoughts:
            return "No thoughts to analyze."
        
        # Calculate statistics
        categories = {}
        emotions = {}
        total_importance = 0
        importance_count = 0
        
        for thought in response.thoughts:
            # Count categories
            categories[thought.category] = categories.get(thought.category, 0) + 1
            
            # Count emotions
            if thought.emotion:
                emotions[thought.emotion] = emotions.get(thought.emotion, 0) + 1
            
            # Sum importance
            if thought.importance is not None:
                total_importance += thought.importance
                importance_count += 1
        
        # Format statistics
        stats = [
            f"Total thoughts: {len(response.thoughts)}",
            "",
            "Categories:",
        ]
        
        for category, count in sorted(categories.items()):
            percentage = (count / len(response.thoughts)) * 100
            stats.append(f"  {category}: {count} ({percentage:.1f}%)")
        
        if emotions:
            stats.extend(["", "Emotions:"])
            for emotion, count in sorted(emotions.items()):
                percentage = (count / len(response.thoughts)) * 100
                stats.append(f"  {emotion}: {count} ({percentage:.1f}%)")
        
        if importance_count > 0:
            avg_importance = total_importance / importance_count
            stats.extend([
                "",
                f"Average importance: {avg_importance:.2f}",
                f"Thoughts with importance: {importance_count}/{len(response.thoughts)}",
            ])
        
        return "\n".join(stats)
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to specified length."""
        if len(content) <= max_length:
            return content
        return content[:max_length - 3] + "..."
    
    def _get_importance_color(self, importance: float) -> str:
        """Get color based on importance level."""
        if importance >= 0.8:
            return "red"
        elif importance >= 0.6:
            return "yellow"
        elif importance >= 0.4:
            return "green"
        else:
            return "dim"


# Global formatter instance
thought_formatter = ThoughtFormatter()
