# CoreLogger - AI Interaction Monitoring & Analysis System

## Overview

CoreLogger is a sophisticated AI conversation monitoring and analysis system designed for tracking, analyzing, and understanding AI interactions. Built with production-grade features, it provides comprehensive tools for capturing AI conversations, detecting emotions, and analyzing interaction patterns using advanced NLP techniques.

**Primary Focus**: Automatic monitoring and analysis of AI conversations with real-time emotion detection and comprehensive logging.

## Features

### Core Functionality
- **AI Interaction Monitoring**: Automatic logging of AI conversations with emotion detection
- **Real-time Chat Interface**: Interactive conversations with AI providers (Web + CLI)
- **Advanced NLP Analysis**: Sentiment analysis, novelty detection, complexity scoring
- **Web Dashboard**: Full-featured web interface for AI interaction monitoring
- **Conversation Analytics**: Comprehensive analysis of AI interaction patterns
- **CLI Export System**: Data export in JSON/CSV formats (CLI only)
- **Real-time Streaming**: Token-by-token AI responses with Rich console rendering

### AI Providers
- **Google Gemini** - Advanced language understanding
- **OpenAI GPT** - Industry-leading conversational AI  
- **Anthropic Claude** - Thoughtful and nuanced responses
- **Mock Provider** - Development and testing support

### Advanced NLP Features
- **Emotion Detection**: 9-category emotion classification for user messages and AI responses
- **Importance Scoring**: Multi-factor importance calculation using NLP metrics
- **Conversation Categorization**: Automatic classification (user-input, ai-response, conversation)
- **Sentiment Analysis**: Emotional tone and strength analysis
- **Complexity Scoring**: Text complexity based on vocabulary and structure
- **Keyword Extraction**: Automatic keyword identification and density analysis
- **Conversation Context**: Three-tier logging for complete interaction tracking

### Web Dashboard
- **Dark Theme Interface**: GitHub-style responsive design optimized for readability
- **AI Interaction Dashboard**: Overview of recent conversations and system statistics
- **Live Chat Interface**: Real-time AI conversation with automatic logging
- **Conversation History**: Browse and search through AI interaction logs
- **Emotion Analytics**: Visual representation of emotion patterns in conversations
- **Category Filtering**: Filter by user-input, ai-response, or complete conversations
- **Real-time Statistics**: Live updates of interaction counts and patterns

### CLI Features
- **Interactive AI Chat**: Full-featured chat with multiple AI providers
- **Automatic Logging**: All conversations automatically saved with metadata
- **Rich Formatting**: Beautiful console output with colors, tables, and progress indicators
- **Streaming Support**: Real-time AI response streaming
- **Conversation History**: Context-aware multi-turn conversations
- **Data Export**: Export conversations in JSON/CSV format
- **Manual Logging**: Traditional thought logging capabilities
- **NLP Analysis**: Analyze individual conversations with detailed metrics
- **Bulk Operations**: Recalculate importance scores for existing entries

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/CoreLogger.git
cd CoreLogger

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (for AI providers)
cp .env.example .env
# Edit .env with your API keys (optional - works with mock provider)

# Initialize database (automatic on first run)
python corelogger.py --help

# Start CLI chat
python corelogger.py chat --model gemini

# Start web interface
python main.py
Access the web dashboard at `http://localhost:8000/dashboard`

## Architecture

## Architecture
```

### Environment Configuration

Create a `.env` file with your API keys (optional - system works with mock providers):

```env
# AI Provider API Keys (Optional - works without for demo/testing)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (automatic)
DATABASE_URL=sqlite:///./corelogger.db

# Application Settings
LOG_LEVEL=INFO
```

## Usage Guide

### Command Line Interface

#### AI Chat (Primary Feature)
```bash
# Start interactive AI chat with Gemini
python corelogger.py chat --model gemini

# Use mock provider (no API key needed)
python corelogger.py chat --model mock

# Chat with conversation history and streaming
python corelogger.py chat --model gemini --history --stream
```

#### Manual Thought Logging (Traditional CLI Features)
```bash
# Log a simple thought manually
python corelogger.py log "Interesting observation about AI behavior"

# Log with metadata
python corelogger.py log "Planning new features" \
  --category idea \
  --tag development,ai \
  --emotion excited \
  --importance 0.8
```

#### View and Analyze Conversations
```bash
# List recent AI interactions
python corelogger.py list --page 1 --size 10

# Filter by emotion or category
python corelogger.py list --emotion happy --category ai-response
python corelogger.py list --search "interesting topic"

# Export conversation data
python corelogger.py export --format json --output my_conversations.json
python corelogger.py export --format csv --category conversation

# Analyze specific interactions with NLP
python corelogger.py analyze <conversation-id> --detailed
```

### Web Interface

#### Starting the Web Server
```bash
# Start the FastAPI web server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8000

# Access the dashboard
# http://localhost:8000/dashboard
```

#### Web Features
- **Dashboard**: Overview of recent AI interactions and statistics  
- **Live Chat**: Real-time AI conversation interface with automatic logging
- **Conversation History**: Browse through all AI interactions with filtering
- **Emotion Analytics**: Visual representation of conversation emotions
- **Dark Theme**: Optimized interface for extended usage
- **Real-time Updates**: Live statistics and conversation logging

**Note**: Export functionality will be added in future updates. Currently available through CLI only.

## Architecture

### Project Structure
```
CoreLogger/
├── cli/                    # Command-line interface
│   └── main.py            # CLI commands and AI chat interface
├── web/                    # Web interface
│   ├── main.py            # FastAPI server configuration
│   ├── routes.py          # Web routes and AI chat API
│   └── templates/         # Jinja2 HTML templates
├── chat/                   # AI chat system
│   ├── interface.py       # Chat interface management
│   └── providers/         # AI provider implementations
├── services/               # Core business logic
│   ├── logger.py          # Conversation logging service
│   ├── exporter.py        # Data export functionality (CLI)
│   ├── formatter.py       # Console output formatting
│   └── nlp_analyzer.py    # NLP analysis engine
├── db/                     # Database layer
│   ├── session.py         # Database session management
│   └── models.py          # SQLAlchemy models
├── models/                 # Pydantic data models
│   └── thought.py         # API data structures
├── corelogger.py          # CLI entry point
└── main.py                # Web server entry point
```

### Key Components

#### Emotion Detection Engine
CoreLogger automatically detects emotions in both user messages and AI responses:

```python
# 9-Category Emotion Classification:
# happy, excited, confident, frustrated, confused, 
# anxious, calm, sad, neutral

# Example detections:
"This is amazing!" → excited
"I'm not sure about this" → confused  
"That worked perfectly" → happy
"Let me think about it" → calm
```

#### AI Chat Integration
Real-time conversation with automatic logging:

```python
# Web Interface: /chat endpoint
# CLI Interface: python corelogger.py chat --model gemini

# All conversations automatically logged with:
# - User message (user-input category)
# - AI response (ai-response category) 
# - Complete conversation (conversation category)
# - Emotion detection for each message
# - Importance scoring and NLP analysis
```

#### AI Provider System
Extensible provider system with built-in fallbacks:

```python
# Currently supported:
# - Google Gemini (with API key)
# - Mock Provider (no API key needed)
# - Graceful fallback with helpful error messages

# Usage in CLI:
python corelogger.py chat --model gemini
python corelogger.py chat --model mock

# Usage in Web:
# Automatic provider selection based on available API keys
# User-friendly error messages when API keys are missing
```

#### Database Schema
Three-tier conversation logging system:

```python
# Database automatically stores:
class ThoughtModel:
    id: UUID                    # Unique identifier
    category: str              # user-input, ai-response, conversation
    content: str               # Message or conversation content
    tags: List[str]            # Automatic tags (chat, provider, etc.)
    emotion: str               # Detected emotion (9 categories)
    importance: float          # NLP-calculated importance score
    timestamp: datetime        # When the interaction occurred
```

## Current Capabilities

### Core Features (Fully Implemented)
- **AI Chat Interface** (CLI + Web)
- **Automatic Conversation Logging** 
- **9-Category Emotion Detection**
- **Dark Theme Web Dashboard**
- **Real-time Statistics**
- **NLP Analysis & Importance Scoring**
- **Data Export** (CLI only)
- **Rich Console Formatting**
- **Multiple AI Provider Support**

### Planned Features
- **Web Export Functionality**
- **Advanced Conversation Analytics**
- **Conversation Search & Filtering**
- **Data Visualization Charts**
- **OpenAI & Claude Provider Integration**

```

## Configuration

### Environment Variables
CoreLogger uses environment variables for configuration:

```env
# AI Provider API Keys (Optional)
GEMINI_API_KEY=your_gemini_api_key_here

# Database (Auto-configured)
DATABASE_URL=sqlite:///./corelogger.db

# Application Settings  
LOG_LEVEL=INFO
```

### Configuration Files
The system automatically handles:
- Database initialization
- Table creation
- Default settings
- Error handling and fallbacks

### API Key Setup
```bash
# Option 1: Environment variable
export GEMINI_API_KEY="your_key_here"

# Option 2: .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# Option 3: CLI parameter
python corelogger.py chat --model gemini --api-key "your_key_here"

# No API key needed for testing
python corelogger.py chat --model mock
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=corelogger

# Test specific components
pytest tests/test_logger.py
pytest tests/test_models.py
```

## � Quick Start Examples

### 1. Test the System (No API Key Needed)
```bash
# Clone and setup
git clone <repo-url>
cd CoreLogger
pip install -r requirements.txt

# Try the CLI with mock AI
python corelogger.py chat --model mock

# Start web dashboard
python main.py
# Visit http://localhost:8000/dashboard
```

### 2. Use with Gemini AI
```bash
# Set API key
export GEMINI_API_KEY="your_key_here"

# Chat in CLI
python corelogger.py chat --model gemini

# Use web interface with real AI
python main.py
# Visit http://localhost:8000/chat
```

### 3. Analyze Your Conversations
```bash
# View recent interactions
python corelogger.py list --size 5

# Export your data
python corelogger.py export --format json --output my_ai_conversations.json

# Analyze specific conversation
python corelogger.py analyze <conversation-id>
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests before committing
pytest

# Format code
black .
isort .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **FastAPI**: Modern Python web framework for the dashboard
- **Typer**: Beautiful CLI framework with Rich integration
- **Rich**: Rich text and beautiful console formatting
- **SQLAlchemy**: Database ORM for conversation storage
- **Google Generative AI**: Gemini AI model integration
- **Jinja2**: Template engine for web interface
- **Bootstrap**: Frontend framework for responsive design

## Support

For support, please open an issue on GitHub.

---

**CoreLogger** - Monitor and analyze your AI interactions with sophisticated emotion detection and NLP analysis.

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd CoreLogger
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python corelogger.py --help  # This will create the database
```

## Usage

### Command Line Interface

#### Basic Logging Commands

```bash
# Log a reflection (default category)
python corelogger.py log "I'm thinking about the nature of consciousness"

# Log with specific category and metadata
python corelogger.py log "I see a red car" --category perception --tag visual --emotion curious --importance 0.7

# Use convenience commands
python corelogger.py perception "The environment appears calm"
python corelogger.py reflect "This situation requires careful analysis" --emotion contemplative
python corelogger.py decide "I will proceed with option A" --importance 0.9
python corelogger.py tick "System checkpoint reached"
python corelogger.py error "Memory allocation failed" --tag system --importance 0.8
```

#### Listing and Searching

```bash
# List recent thoughts
python corelogger.py list

# List with filters
python corelogger.py list --category reflection --tag important
python corelogger.py list --emotion curious --min-importance 0.5
python corelogger.py list --search "consciousness" --page 1 --size 5

# Display as table
python corelogger.py list --table

# Show statistics
python corelogger.py list --stats
```

#### Thought Management

```bash
# Show specific thought
python corelogger.py show <thought-id>

# Update thought
python corelogger.py update <thought-id> --content "Updated content" --add-tag modified

# Delete thought (with confirmation)
python corelogger.py delete <thought-id>

# Force delete without confirmation
python corelogger.py delete <thought-id> --force
```

#### Interactive Mode

```bash
# Start interactive logging session
python corelogger.py interactive
```

### REST API

#### Starting the Server

```bash
# Start development server
python main.py

# Or with custom settings
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### API Endpoints

The API provides the following endpoints:

- `GET /api/v1/health` - Health check
- `POST /api/v1/thoughts` - Create a thought
- `GET /api/v1/thoughts` - List thoughts with filtering
- `GET /api/v1/thoughts/{id}` - Get specific thought
- `PUT /api/v1/thoughts/{id}` - Update thought
- `DELETE /api/v1/thoughts/{id}` - Delete thought

**Convenience endpoints:**
- `POST /api/v1/thoughts/perception` - Log perception
- `POST /api/v1/thoughts/reflection` - Log reflection
- `POST /api/v1/thoughts/decision` - Log decision
- `POST /api/v1/thoughts/tick` - Log system tick
- `POST /api/v1/thoughts/error` - Log error

#### API Examples

```bash
# Create a thought
curl -X POST "http://localhost:8000/api/v1/thoughts" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "reflection",
    "content": "API testing thoughts",
    "tags": ["api", "test"],
    "emotion": "focused",
    "importance": 0.8
  }'

# List thoughts with filters
curl "http://localhost:8000/api/v1/thoughts?category=reflection&page=1&page_size=10"

# Quick logging with convenience endpoints
curl -X POST "http://localhost:8000/api/v1/thoughts/perception?content=I observe changes&tags=visual"
```

#### API Documentation

When the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

CoreLogger uses environment variables for configuration. Create a `.env` file:

```env
# Database
DATABASE_URL=sqlite:///./corelogger.db
DATABASE_ECHO=false

# API Server
API_HOST=localhost
API_PORT=8000
API_RELOAD=true

# Logging
LOG_LEVEL=INFO

# Features
ENABLE_EMOTIONS=true
ENABLE_IMPORTANCE_SCORING=true
MAX_CONTENT_LENGTH=10000
DEFAULT_IMPORTANCE=0.5
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./corelogger.db` | Database connection string |
| `DATABASE_ECHO` | `false` | Enable SQL query logging |
| `API_HOST` | `localhost` | API server host |
| `API_PORT` | `8000` | API server port |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `ENABLE_EMOTIONS` | `true` | Enable emotion tracking |
| `ENABLE_IMPORTANCE_SCORING` | `true` | Enable importance scores |
| `MAX_CONTENT_LENGTH` | `10000` | Maximum thought content length |
| `DEFAULT_IMPORTANCE` | `0.5` | Default importance when not specified |

## Thought Schema

Each thought has the following structure:

```python
{
    "id": "uuid4",                    # Unique identifier
    "timestamp": "2024-01-01T12:00:00Z", # Creation time
    "category": "reflection",         # One of: perception, reflection, decision, tick, error
    "content": "Thought content...",  # Main thought text
    "tags": ["tag1", "tag2"],        # List of tags
    "emotion": "curious",            # Optional emotional state
    "importance": 0.7                # Optional importance score (0.0-1.0)
}
```

### Categories

- **perception**: Observations and sensory input
- **reflection**: Analysis and contemplation
- **decision**: Choices and determinations
- **tick**: System events and checkpoints
- **error**: Problems and failures

## Development

### Project Structure

```
corelogger/
├── cli/                  # CLI commands and interface
├── api/                  # FastAPI routes and endpoints
├── db/                   # Database models and session management
├── services/             # Business logic and formatting
├── models/               # Pydantic schemas
├── tests/                # Test suite
├── config.py             # Configuration management
├── corelogger.py         # CLI entry point
├── main.py              # API entry point
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_logger.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

## Future Development

### Planned Enhancements
- **Web Export**: Direct export functionality from web interface
- **Advanced Analytics**: Conversation pattern analysis and visualization
- **Additional AI Providers**: OpenAI GPT and Anthropic Claude integration
- **Conversation Search**: Full-text search across AI interactions
- **Data Visualization**: Charts and graphs for interaction patterns
- **API Endpoints**: RESTful API for third-party integrations

### Extensibility
The modular design allows easy extension:
- **Custom AI Providers**: Add new AI service integrations
- **Enhanced Emotion Detection**: More sophisticated emotion classification
- **Custom Analytics**: Additional NLP analysis metrics
- **Export Formats**: New data export options
- **UI Themes**: Additional interface themes and customization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive docstrings  
- Include type annotations
- Test new functionality thoroughly
- Use descriptive commit messages

## Current Status

**Version**: 1.0.0 (Production Ready)
**Status**: Fully Functional

### Completed Features
- CLI AI chat with emotion detection
- Web dashboard with real-time updates
- Automatic conversation logging
- 9-category emotion classification
- NLP analysis and importance scoring
- Data export (CLI)
- Dark theme web interface
- Multiple AI provider support (Gemini + Mock)

### In Development
- Web export functionality
- Advanced conversation analytics
- Additional AI provider integrations

## Version History

### v1.0.0 (Current)
- Production-ready AI conversation monitoring
- Complete emotion detection system
- Web and CLI interfaces fully functional
- Automatic database logging
- NLP analysis and importance scoring

### Future Versions
- v1.1.0: Web export functionality
- v1.2.0: OpenAI and Claude provider integration
- v1.3.0: Advanced analytics and visualization

---

**CoreLogger** - AI Interaction Monitoring Made Simple
