"""Utility functions for chat interface."""

import re
from datetime import datetime, timezone
from typing import Optional, List


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a timestamp for display."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def analyze_emotion(text: str) -> Optional[str]:
    """Simple emotion analysis based on text content."""
    text_lower = text.lower()
    
    # Positive emotions
    positive_keywords = [
        "happy", "joy", "excited", "great", "awesome", "amazing", 
        "wonderful", "fantastic", "love", "like", "good", "excellent"
    ]
    
    # Negative emotions
    negative_keywords = [
        "sad", "angry", "frustrated", "disappointed", "upset", 
        "annoyed", "hate", "dislike", "bad", "terrible", "awful"
    ]
    
    # Neutral/analytical emotions
    analytical_keywords = [
        "think", "analyze", "consider", "understand", "process", 
        "evaluate", "assess", "examine", "study"
    ]
    
    # Question/curious emotions
    question_keywords = [
        "wonder", "curious", "question", "what", "how", "why", 
        "when", "where", "confused", "uncertain"
    ]
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
    analytical_count = sum(1 for keyword in analytical_keywords if keyword in text_lower)
    curious_count = sum(1 for keyword in question_keywords if keyword in text_lower)
    
    # Determine dominant emotion
    if positive_count > max(negative_count, analytical_count, curious_count):
        return "positive"
    elif negative_count > max(positive_count, analytical_count, curious_count):
        return "negative" 
    elif curious_count > max(positive_count, negative_count, analytical_count):
        return "curious"
    elif analytical_count > 0:
        return "analytical"
    elif "?" in text:
        return "questioning"
    else:
        return "neutral"


def calculate_importance(text: str, is_ai_response: bool = False) -> float:
    """Calculate importance score for a message."""
    base_score = 0.3  # Default base importance
    
    # Length factor (longer messages tend to be more important)
    length_factor = min(len(text) / 500, 0.3)  # Max 0.3 boost for length
    
    # Keyword importance boosters
    important_keywords = [
        "important", "critical", "urgent", "significant", "key", 
        "essential", "crucial", "major", "primary", "main"
    ]
    
    question_keywords = ["?", "what", "how", "why", "when", "where", "which"]
    decision_keywords = [
        "decide", "choose", "select", "determine", "conclude", 
        "resolution", "solution", "answer"
    ]
    
    text_lower = text.lower()
    
    # Boost for important keywords
    importance_boost = sum(0.1 for keyword in important_keywords if keyword in text_lower)
    importance_boost = min(importance_boost, 0.4)  # Cap at 0.4
    
    # Boost for questions (user asking questions)
    if not is_ai_response:
        question_boost = sum(0.05 for keyword in question_keywords if keyword in text_lower)
        question_boost = min(question_boost, 0.2)  # Cap at 0.2
    else:
        question_boost = 0
    
    # Boost for decisions/solutions (AI providing answers)
    if is_ai_response:
        decision_boost = sum(0.05 for keyword in decision_keywords if keyword in text_lower)
        decision_boost = min(decision_boost, 0.2)  # Cap at 0.2
    else:
        decision_boost = 0
    
    # Calculate final score
    final_score = base_score + length_factor + importance_boost + question_boost + decision_boost
    
    # Ensure score is within bounds
    return min(max(final_score, 0.1), 1.0)


def extract_tags(text: str, is_ai_response: bool = False) -> List[str]:
    """Extract relevant tags from text content."""
    tags = []
    text_lower = text.lower()
    
    # Common topic tags
    topic_patterns = {
        "programming": ["code", "programming", "python", "software", "development", "bug", "function"],
        "science": ["science", "research", "study", "experiment", "data", "analysis"],
        "technology": ["technology", "tech", "computer", "AI", "artificial intelligence", "machine learning"],
        "education": ["learn", "teaching", "education", "knowledge", "understand", "explain"],
        "question": ["?", "what", "how", "why", "when", "where", "which"],
        "greeting": ["hello", "hi", "good morning", "good afternoon", "good evening"],
        "conversation": ["chat", "talk", "discuss", "conversation", "speaking"],
    }
    
    for tag, keywords in topic_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(tag)
    
    # Add role-based tags
    if is_ai_response:
        tags.append("ai-response")
    else:
        tags.append("user-input")
    
    # Add length-based tags
    if len(text) > 200:
        tags.append("long-form")
    elif len(text) < 50:
        tags.append("short-form")
    
    # Remove duplicates and return
    return list(set(tags))


def clean_ai_response(response: str) -> str:
    """Clean and format AI response text."""
    # Remove excessive whitespace
    response = re.sub(r'\s+', ' ', response.strip())
    
    # Remove markdown if present (simple cleanup)
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Bold
    response = re.sub(r'\*(.*?)\*', r'\1', response)      # Italic
    response = re.sub(r'`(.*?)`', r'\1', response)        # Code
    
    # Ensure proper sentence ending
    if response and not response.endswith(('.', '!', '?')):
        response += '.'
    
    return response


def format_chat_display(role: str, message: str, timestamp: Optional[datetime] = None) -> str:
    """Format a chat message for display."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    time_str = timestamp.strftime("%H:%M:%S")
    role_display = "You" if role == "user" else "AI"
    
    return f"[{time_str}] {role_display}: {message}"
