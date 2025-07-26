"""Advanced NLP analysis for thought scoring and processing."""

import re
import math
from typing import Dict, List, Set, Tuple, Union, Optional
from collections import Counter
import logging
from datetime import datetime

# Optional NLP dependencies - graceful fallback if not installed
try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    nltk = None
    NLTK_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TextBlob = None
    TEXTBLOB_AVAILABLE = False

from sqlalchemy.orm import Session


class NLPAnalyzer:
    """Advanced NLP analysis for thought content."""
    
    def __init__(self):
        # Common English stop words for filtering
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'i', 'you', 'we', 'they', 'this',
            'but', 'or', 'not', 'have', 'had', 'what', 'when', 'where', 'who',
            'which', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'can', 'could', 'should', 'would'
        }
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text."""
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
        
        # Filter out stop words
        keywords = [word for word in words if word not in self.stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def calculate_keyword_density(self, text: str) -> Dict[str, float]:
        """Calculate keyword density for the text."""
        keywords = self.extract_keywords(text)
        total_words = len(text.split())
        
        if total_words == 0:
            return {}
        
        keyword_counts = Counter(keywords)
        densities = {}
        
        for keyword, count in keyword_counts.items():
            densities[keyword] = count / total_words
        
        return densities
    
    def calculate_repetition_score(self, text: str) -> float:
        """Calculate repetition score (0.0 = no repetition, 1.0 = high repetition)."""
        words = text.lower().split()
        if len(words) <= 1:
            return 0.0
        
        word_counts = Counter(words)
        unique_words = len(word_counts)
        total_words = len(words)
        
        # Calculate repetition as 1 - (unique_words / total_words)
        repetition = 1.0 - (unique_words / total_words)
        return min(repetition, 1.0)
    
    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of the text (measure of information content)."""
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(text.lower())
        total_chars = len(text)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Extract n-grams from text."""
        words = text.lower().split()
        if len(words) < n:
            return []
        
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    def calculate_novelty_score(
        self, 
        current_text: str, 
        existing_texts: List[str],
        ngram_size: int = 3
    ) -> float:
        """Calculate novelty score based on n-gram overlap with existing content."""
        if not existing_texts:
            return 1.0  # Maximum novelty if no existing content
        
        current_ngrams = set(self.extract_ngrams(current_text, ngram_size))
        if not current_ngrams:
            return 0.5  # Neutral novelty for very short text
        
        # Calculate overlap with existing texts
        total_overlap = 0
        for existing_text in existing_texts:
            existing_ngrams = set(self.extract_ngrams(existing_text, ngram_size))
            if existing_ngrams:
                overlap = len(current_ngrams.intersection(existing_ngrams))
                max_possible = max(len(current_ngrams), len(existing_ngrams))
                if max_possible > 0:
                    total_overlap += overlap / max_possible
        
        # Average overlap across all existing texts
        avg_overlap = total_overlap / len(existing_texts) if existing_texts else 0
        
        # Novelty is inverse of overlap
        novelty = 1.0 - min(avg_overlap, 1.0)
        return max(0.0, novelty)
    
    def analyze_sentiment_basic(self, text: str) -> Tuple[str, float]:
        """Basic sentiment analysis using keyword matching."""
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'excited', 'pleased', 'satisfied',
            'awesome', 'brilliant', 'perfect', 'success', 'achievement', 'win'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad',
            'angry', 'frustrated', 'disappointed', 'failed', 'failure', 'wrong',
            'error', 'problem', 'issue', 'difficult', 'hard', 'struggle'
        }
        
        words = set(text.lower().split())
        positive_count = len(words.intersection(positive_words))
        negative_count = len(words.intersection(negative_words))
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return "neutral", 0.5
        
        sentiment_score = positive_count / total_sentiment_words
        
        if sentiment_score > 0.6:
            return "positive", sentiment_score
        elif sentiment_score < 0.4:
            return "negative", 1.0 - sentiment_score
        else:
            return "neutral", 0.5
    
    def calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity based on various factors."""
        if not text:
            return 0.0
        
        words = text.split()
        sentences = text.split('.')
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Vocabulary richness (unique words / total words)
        vocab_richness = len(set(words)) / len(words) if words else 0
        
        # Normalize and combine factors
        word_complexity = min(avg_word_length / 10, 1.0)  # Normalize to 0-1
        sentence_complexity = min(avg_sentence_length / 20, 1.0)  # Normalize to 0-1
        
        # Weighted combination
        complexity = (word_complexity * 0.3 + sentence_complexity * 0.4 + vocab_richness * 0.3)
        return min(complexity, 1.0)


class EnhancedThoughtScorer:
    """Enhanced thought scoring with NLP analysis."""
    
    def __init__(self):
        self.nlp = NLPAnalyzer()
    
    def calculate_enhanced_importance(
        self,
        content: str,
        length_weight: float = 0.2,
        complexity_weight: float = 0.25,
        novelty_weight: float = 0.3,
        sentiment_weight: float = 0.15,
        entropy_weight: float = 0.1,
        existing_content: Optional[List[str]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate enhanced importance score with detailed metrics."""
        
        if not content:
            return 0.0, {}
        
        # Length factor (normalized)
        length_factor = min(len(content) / 500, 1.0)  # Max at 500 chars
        
        # Complexity factor
        complexity_factor = self.nlp.calculate_complexity_score(content)
        
        # Novelty factor
        novelty_factor = 1.0  # Default to high novelty
        if existing_content:
            novelty_factor = self.nlp.calculate_novelty_score(content, existing_content)
        
        # Sentiment factor (more extreme sentiments get higher scores)
        sentiment, sentiment_strength = self.nlp.analyze_sentiment_basic(content)
        if sentiment == "neutral":
            sentiment_factor = 0.3  # Lower score for neutral
        else:
            sentiment_factor = sentiment_strength
        
        # Entropy factor (information content)
        entropy = self.nlp.calculate_entropy(content)
        entropy_factor = min(entropy / 5, 1.0)  # Normalize entropy (typical max ~5)
        
        # Calculate weighted importance
        importance = (
            length_factor * length_weight +
            complexity_factor * complexity_weight +
            novelty_factor * novelty_weight +
            sentiment_factor * sentiment_weight +
            entropy_factor * entropy_weight
        )
        
        # Ensure importance is between 0 and 1
        importance = max(0.0, min(importance, 1.0))
        
        # Return detailed metrics
        metrics = {
            'length_factor': length_factor,
            'complexity_factor': complexity_factor,
            'novelty_factor': novelty_factor,
            'sentiment_factor': sentiment_factor,
            'entropy_factor': entropy_factor,
            'final_importance': importance
        }
        
        return importance, metrics
    
    def get_enhanced_analysis(self, content: str, existing_content: Optional[List[str]] = None) -> Dict:
        """Get comprehensive NLP analysis of the content."""
        keywords = self.nlp.extract_keywords(content)
        keyword_density = self.nlp.calculate_keyword_density(content)
        repetition_score = self.nlp.calculate_repetition_score(content)
        entropy = self.nlp.calculate_entropy(content)
        sentiment, sentiment_score = self.nlp.analyze_sentiment_basic(content)
        complexity = self.nlp.calculate_complexity_score(content)
        novelty = self.nlp.calculate_novelty_score(content, existing_content or [])
        importance, metrics = self.calculate_enhanced_importance(content, existing_content=existing_content)
        
        return {
            'keywords': keywords[:10],  # Top 10 keywords
            'keyword_density': dict(list(keyword_density.items())[:5]),  # Top 5
            'repetition_score': repetition_score,
            'entropy': entropy,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'complexity_score': complexity,
            'novelty_score': novelty,
            'importance_score': importance,
            'importance_metrics': metrics,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
