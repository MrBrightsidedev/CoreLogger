"""
CoreLogger - Eidos OS Logging Module

A foundational logging and introspection module for advanced AI systems.
Provides CLI and REST API interfaces for logging thoughts, decisions,
reflections, and events with rich metadata support.
"""

__version__ = "0.1.0"
__author__ = "Eidos Development Team"
__email__ = "dev@eidos.ai"

from cli.main import app as cli_app
from main import app as api_app

# Main entry point for CLI
def main():
    """Main CLI entry point."""
    cli_app()

__all__ = [
    "main",
    "cli_app", 
    "api_app",
]
