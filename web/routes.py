"""Web dashboard routes for CoreLogger."""

import os
import json
from typing import Optional, List, Dict, Any

from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.session import get_db
from models.thought import ThoughtCreate, ThoughtQuery
from services.logger import ThoughtLogger

# Try to import Gemini AI library with proper error handling
GEMINI_AVAILABLE = False
genai = None
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except ImportError:
    pass

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

# Mount static files
# This will be done in the main app


# Pydantic models for API requests
class ChatRequest(BaseModel):
    message: str
    provider: str = "gemini"
    streaming: bool = True
    save_chat: bool = False
    show_thinking: bool = False


class ChatResponse(BaseModel):
    success: bool
    response: str = ""
    error: str = ""
    thinking: str = ""


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "CoreLogger AI Monitoring System",
        "gemini_available": GEMINI_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard view with recent AI interactions and system stats."""
    thought_logger = ThoughtLogger()
    
    # Get recent AI interactions (last 10)
    query = ThoughtQuery(
        page=1,
        size=10,
        min_importance=None,
        max_importance=None,
        order_by="timestamp",
        order_desc=True
    )
    recent_ai_logs = thought_logger.get_thoughts(db, query)
    
    # Get AI system stats
    total_interactions = thought_logger.count_thoughts(db)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_interactions = thought_logger.count_thoughts(db, created_after=today_start)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_thoughts": recent_ai_logs.thoughts,  # AI conversation logs
        "total_thoughts": total_interactions,  # Total AI interactions
        "today_thoughts": today_interactions,  # Today's AI interactions
        "page_title": "CoreLogger - AI System Monitor"
    })


@router.get("/thoughts", response_class=HTMLResponse)
async def thoughts_list(
    request: Request,
    page: int = 1,
    size: int = 20,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Paginated AI interaction logs with filtering and analysis."""
    thought_logger = ThoughtLogger()
    
    query = ThoughtQuery(
        page=page,
        size=size,
        min_importance=None,
        max_importance=None,
        order_by="timestamp",
        order_desc=True,
        category=category,
        tag=tag,
        search=search
    )
    
    ai_interactions = thought_logger.get_thoughts(db, query)
    total_interactions = thought_logger.count_thoughts(db, query)
    total_pages = (total_interactions + size - 1) // size
    
    return templates.TemplateResponse("thoughts_list.html", {
        "request": request,
        "thoughts": ai_interactions.thoughts,  # AI conversation logs
        "current_page": page,
        "total_pages": total_pages,
        "total_thoughts": total_interactions,
        "filters": {
            "category": category,
            "tag": tag,
            "search": search
        },
        "page_title": "AI Interaction Logs"
    })


@router.get("/thoughts/{thought_id}", response_class=HTMLResponse)
async def thought_detail(request: Request, thought_id: str, db: Session = Depends(get_db)):
    """Individual AI interaction detail view with metadata analysis."""
    thought_logger = ThoughtLogger()
    
    try:
        ai_interaction = thought_logger.get_thought_by_id(db, thought_id)
        if not ai_interaction:
            raise HTTPException(status_code=404, detail="AI interaction not found")
        
        return templates.TemplateResponse("thought_detail.html", {
            "request": request,
            "thought": ai_interaction,  # AI conversation data
            "page_title": f"AI Interaction - {ai_interaction.category}"
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="AI interaction not found")


@router.get("/search", response_class=HTMLResponse)
async def search_form(request: Request):
    """Advanced search form for AI interaction logs."""
    return templates.TemplateResponse("search_form.html", {
        "request": request,
        "page_title": "Search AI Interactions"
    })


@router.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Live AI chat interface with automatic logging to CoreLogger."""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "page_title": "AI Chat Monitor"
    })


@router.post("/api/chat")
async def chat_api(chat_request: ChatRequest, db: Session = Depends(get_db)):
    """API endpoint for chat functionality with automatic AI interaction logging."""
    try:
        if chat_request.provider == "gemini":
            response_text = await call_gemini_api(
                chat_request.message, 
                chat_request.show_thinking
            )
        else:
            # Mock response for other providers
            response_text = f"Mock response from {chat_request.provider}: This is a simulated response to '{chat_request.message}'"
        
        # Always log AI interactions to CoreLogger (this is the main purpose)
        await log_ai_interaction(db, chat_request.message, response_text, chat_request.provider)
        
        return ChatResponse(
            success=True,
            response=response_text,
            thinking="Processing your request and generating a thoughtful response..." if chat_request.show_thinking else ""
        )
    
    except Exception as e:
        return ChatResponse(
            success=False,
            error=str(e)
        )


async def call_gemini_api(message: str, show_thinking: bool = False) -> str:
    """Call Google Gemini API with improved error handling."""
    if not GEMINI_AVAILABLE or genai is None:
        return f"🤖 Mock Gemini Response: Thank you for asking '{message}'. This is a simulated response since the Gemini library is not available. In a real deployment, this would connect to Google's Gemini AI service."
    
    try:
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return f"🔑 API Key Missing: Thank you for your question about '{message}'. This is a demonstration response since no Gemini API key is configured. To use real AI responses, please set the GEMINI_API_KEY environment variable."
        
        # Configure and use Gemini with proper error handling
        try:
            # Configure the API using the global genai module
            genai.configure(api_key=api_key)  # type: ignore
            
            # Create model instance
            model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
            
            # Enhanced prompt for CoreLogger context
            system_prompt = """You are an AI assistant being monitored by CoreLogger, an AI interaction tracking system. 
            CoreLogger automatically captures and analyzes all our conversations for:
            - AI behavior pattern analysis
            - Response quality monitoring
            - Interaction metadata extraction
            - AI system performance tracking
            
            Be natural and helpful in your responses. Your interactions are being logged for AI research and monitoring purposes.
            """
            
            enhanced_prompt = f"{system_prompt}\n\nUser question: {message}\n\nResponse:"
            
            # Generate response with basic settings
            try:
                response = model.generate_content(enhanced_prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    return response.text.strip()
                else:
                    return f"🤔 I received your question about '{message}' but couldn't generate a proper response. Could you try rephrasing or asking something else?"
            except Exception as generation_error:
                return f"🚨 Generation Error: Failed to generate response for '{message}'. Error: {str(generation_error)}"
                
        except Exception as api_error:
            error_msg = str(api_error)
            if "API_KEY" in error_msg.upper() or "authentication" in error_msg.lower():
                return f"🔐 API Authentication Error: There's an issue with your Gemini API key. Please check that GEMINI_API_KEY is set correctly. Error: {error_msg}"
            elif "QUOTA" in error_msg.upper() or "LIMIT" in error_msg.upper():
                return f"📊 API Quota Exceeded: You've reached your Gemini API usage limit. Please try again later or check your Google Cloud console."
            else:
                return f"🚨 API Error: I encountered an issue while processing your question: '{message}'. Error: {error_msg}. Please try again or contact support if this persists."
            
    except Exception as e:
        # Fallback for any other unexpected errors
        return f"⚠️ Unexpected Error: I encountered an unexpected issue while processing '{message}'. Here's a helpful response instead: Thank you for your question. While I can't provide AI-generated insights right now, I encourage you to reflect on this topic and log your own thoughts for future reference. Error details: {str(e)}"


async def log_ai_interaction(db: Session, user_message: str, ai_response: str, provider: str = "gemini"):
    """Log AI interaction to CoreLogger database with automatic metadata analysis."""
    try:
        thought_logger = ThoughtLogger()
        
        # Simple emotion detection based on keywords and sentiment
        user_emotion = detect_emotion(user_message)
        ai_emotion = detect_emotion(ai_response)
        
        # Log user message
        user_log = ThoughtCreate(
            content=f"👤 User: {user_message}",
            category="user-input",
            tags=["chat", "user-query", provider.lower()],
            emotion=user_emotion,
            importance=0.3  # User questions generally lower importance
        )
        thought_logger.log_thought(db, user_log)
        
        # Log AI response with higher importance and analysis
        ai_log = ThoughtCreate(
            content=f"🤖 {provider.title()}: {ai_response}",
            category="ai-response",
            tags=["chat", "ai-generated", provider.lower(), "response"],
            emotion=ai_emotion,
            importance=0.7  # AI responses generally higher importance for analysis
        )
        thought_logger.log_thought(db, ai_log)
        
        # Log conversation pair for context
        conversation_log = ThoughtCreate(
            content=f"💬 Conversation\n\n👤 User: {user_message}\n\n🤖 {provider.title()}: {ai_response}",
            category="conversation",
            tags=["chat", "conversation", provider.lower(), "complete-exchange"],
            emotion="neutral",  # Conversations are generally neutral
            importance=0.5
        )
        thought_logger.log_thought(db, conversation_log)
        
    except Exception as e:
        # Don't fail the chat if logging fails, but log the error
        print(f"Error logging AI interaction to CoreLogger: {e}")


def detect_emotion(text: str) -> Optional[str]:
    """Simple emotion detection based on keywords and patterns."""
    if not text:
        return "neutral"
    
    text_lower = text.lower()
    
    # Positive emotions
    if any(word in text_lower for word in ["thank", "great", "awesome", "amazing", "love", "happy", "excited", "wonderful", "fantastic", "excellent"]):
        return "happy"
    
    # Excited/enthusiastic
    if any(word in text_lower for word in ["wow", "incredible", "brilliant", "outstanding", "perfect", "!", "?!"]):
        return "excited"
    
    # Confident/motivated
    if any(word in text_lower for word in ["confident", "sure", "definitely", "absolutely", "certain", "motivated", "determined"]):
        return "confident"
    
    # Frustrated/negative
    if any(word in text_lower for word in ["frustrated", "annoying", "terrible", "awful", "hate", "angry", "mad", "stupid", "bad"]):
        return "frustrated"
    
    # Confused/uncertain
    if any(word in text_lower for word in ["confused", "unclear", "don't understand", "not sure", "uncertain", "help", "how", "what", "why"]):
        return "confused"
    
    # Anxious/worried
    if any(word in text_lower for word in ["worried", "anxious", "nervous", "scared", "afraid", "concerned"]):
        return "anxious"
    
    # Calm/neutral positive
    if any(word in text_lower for word in ["calm", "peaceful", "relaxed", "okay", "fine", "good"]):
        return "calm"
    
    # Sad
    if any(word in text_lower for word in ["sad", "depressed", "down", "disappointed", "upset"]):
        return "sad"
    
    # Default to neutral
    return "neutral"