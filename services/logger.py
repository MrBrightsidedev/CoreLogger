import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from config import settings
from db.models import ThoughtModel
from models.thought import (
    Thought,
    ThoughtCreate,
    ThoughtQuery,
    ThoughtResponse,
    ThoughtsListResponse,
    ThoughtUpdate,
)
from services.nlp_analyzer import EnhancedThoughtScorer


class ThoughtLogger:
    """Service for logging and managing thoughts."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nlp_scorer = EnhancedThoughtScorer()
        
    def create_thought(self, session: Session, thought_data: ThoughtCreate) -> Thought:
        """Create a new thought entry with enhanced NLP analysis."""
        self.logger.info(f"Creating thought with category: {thought_data.category}")
        
        # Get existing content for novelty analysis (last 10 thoughts)
        existing_thoughts = session.query(ThoughtModel.content)\
            .order_by(desc(ThoughtModel.timestamp))\
            .limit(10)\
            .all()
        existing_content = [t.content for t in existing_thoughts] if existing_thoughts else []
        
        # Enhanced importance calculation using NLP
        importance = thought_data.importance
        if importance is None and settings.enable_importance_scoring:
            enhanced_importance, metrics = self.nlp_scorer.calculate_enhanced_importance(
                thought_data.content,
                existing_content=existing_content
            )
            importance = enhanced_importance
            self.logger.info(f"Auto-calculated importance: {importance:.3f}")
        elif importance is None:
            importance = settings.default_importance
            
        # Create database model
        db_thought = ThoughtModel(
            category=thought_data.category,
            content=thought_data.content,
            tags=thought_data.tags,
            emotion=thought_data.emotion if settings.enable_emotions else None,
            importance=importance,
        )
        
        session.add(db_thought)
        session.commit()
        session.refresh(db_thought)
        
        # Convert to Pydantic model
        thought = self._db_to_pydantic(db_thought)
        self.logger.info(f"Created thought with ID: {thought.id}")
        
        return thought
    
    def get_thought(self, session: Session, thought_id: UUID) -> Optional[Thought]:
        """Retrieve a thought by ID."""
        db_thought = session.query(ThoughtModel).filter(ThoughtModel.id == thought_id).first()
        if db_thought:
            return self._db_to_pydantic(db_thought)
        return None
    
    def update_thought(
        self, session: Session, thought_id: UUID, update_data: ThoughtUpdate
    ) -> Optional[Thought]:
        """Update an existing thought."""
        db_thought = session.query(ThoughtModel).filter(ThoughtModel.id == thought_id).first()
        if not db_thought:
            return None
            
        # Update fields that were provided
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "emotion" and not settings.enable_emotions:
                continue
            setattr(db_thought, field, value)
        
        session.commit()
        session.refresh(db_thought)
        
        self.logger.info(f"Updated thought with ID: {thought_id}")
        return self._db_to_pydantic(db_thought)
    
    def delete_thought(self, session: Session, thought_id: UUID) -> bool:
        """Delete a thought by ID."""
        db_thought = session.query(ThoughtModel).filter(ThoughtModel.id == thought_id).first()
        if db_thought:
            session.delete(db_thought)
            session.commit()
            self.logger.info(f"Deleted thought with ID: {thought_id}")
            return True
        return False
    
    # Add aliases and additional methods for compatibility
    def get_thoughts(self, session: Session, query: Optional[ThoughtQuery] = None) -> ThoughtsListResponse:
        """Get thoughts with filtering - alias for list_thoughts."""
        return self.list_thoughts(session, query)
    
    def get_thought_by_id(self, session: Session, thought_id: str) -> Optional[Thought]:
        """Get a thought by ID string - converts to UUID."""
        try:
            uuid_id = UUID(thought_id)
            return self.get_thought(session, uuid_id)
        except ValueError:
            return None
    
    def log_thought(self, session: Session, thought_data: ThoughtCreate) -> Thought:
        """Log a thought - alias for create_thought."""
        return self.create_thought(session, thought_data)
    
    def count_thoughts(self, session: Session, query: Optional[ThoughtQuery] = None, created_after: Optional[datetime] = None) -> int:
        """Count thoughts with optional filtering."""
        db_query = session.query(ThoughtModel)
        
        if created_after:
            db_query = db_query.filter(ThoughtModel.timestamp >= created_after)
        
        if query:
            db_query = self._apply_filters(db_query, query)
        
        return db_query.count()
    
    def list_thoughts(
        self,
        session: Session,
        query: Optional[ThoughtQuery] = None,
    ) -> ThoughtsListResponse:
        """List thoughts with optional filtering and pagination."""
        
        # Extract pagination from query or use defaults
        page = query.page if query else 1
        page_size = query.size if query else 50
        
        # Build base query
        db_query = session.query(ThoughtModel)
        
        # Apply filters
        if query:
            db_query = self._apply_filters(db_query, query)
        
        # Get total count before pagination
        total = db_query.count()
        
        # Apply ordering
        order_by = getattr(query, 'order_by', 'timestamp') if query else 'timestamp'
        order_desc = getattr(query, 'order_desc', True) if query else True
        
        if order_desc:
            db_query = db_query.order_by(desc(getattr(ThoughtModel, order_by, ThoughtModel.timestamp)))
        else:
            db_query = db_query.order_by(getattr(ThoughtModel, order_by, ThoughtModel.timestamp))
        
        # Apply pagination
        offset = (page - 1) * page_size
        db_thoughts = db_query.offset(offset).limit(page_size).all()
        
        # Convert to Pydantic models
        thoughts = [self._db_to_pydantic(db_thought) for db_thought in db_thoughts]
        
        total_pages = (total + page_size - 1) // page_size
        
        return ThoughtsListResponse(
            thoughts=[ThoughtResponse(**thought.model_dump()) for thought in thoughts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def log_perception(self, session: Session, content: str, **kwargs) -> Thought:
        """Convenience method for logging perceptions."""
        thought_data = ThoughtCreate(
            category="perception", 
            content=content, 
            **kwargs
        )
        return self.create_thought(session, thought_data)
    
    def log_reflection(self, session: Session, content: str, **kwargs) -> Thought:
        """Convenience method for logging reflections."""
        thought_data = ThoughtCreate(
            category="reflection", 
            content=content, 
            **kwargs
        )
        return self.create_thought(session, thought_data)
    
    def log_decision(self, session: Session, content: str, **kwargs) -> Thought:
        """Convenience method for logging decisions."""
        thought_data = ThoughtCreate(
            category="decision", 
            content=content, 
            **kwargs
        )
        return self.create_thought(session, thought_data)
    
    def log_tick(self, session: Session, content: str, **kwargs) -> Thought:
        """Convenience method for logging system ticks."""
        thought_data = ThoughtCreate(
            category="tick", 
            content=content, 
            **kwargs
        )
        return self.create_thought(session, thought_data)
    
    def log_error(self, session: Session, content: str, **kwargs) -> Thought:
        """Convenience method for logging errors."""
        thought_data = ThoughtCreate(
            category="error", 
            content=content, 
            **kwargs
        )
        return self.create_thought(session, thought_data)
    
    def _apply_filters(self, query, filters: ThoughtQuery):
        """Apply query filters to the database query."""
        if filters.category:
            query = query.filter(ThoughtModel.category == filters.category)
        
        # Handle both tags (list) and tag (single) fields
        if filters.tags:
            # Filter thoughts that contain any of the specified tags
            tag_conditions = []
            for tag in filters.tags:
                tag_conditions.append(ThoughtModel.tags.contains([tag]))
            query = query.filter(or_(*tag_conditions))
        elif filters.tag:
            query = query.filter(ThoughtModel.tags.contains([filters.tag]))
        
        if filters.emotion:
            query = query.filter(ThoughtModel.emotion == filters.emotion)
        
        if filters.min_importance is not None:
            query = query.filter(ThoughtModel.importance >= filters.min_importance)
        
        if filters.max_importance is not None:
            query = query.filter(ThoughtModel.importance <= filters.max_importance)
        
        if filters.start_date:
            query = query.filter(ThoughtModel.timestamp >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(ThoughtModel.timestamp <= filters.end_date)
        
        if filters.created_after:
            query = query.filter(ThoughtModel.timestamp >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(ThoughtModel.timestamp <= filters.created_before)
        
        # Handle both search_term and search fields
        search_text = filters.search_term or filters.search
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.filter(ThoughtModel.content.ilike(search_pattern))
        
        return query
    
    def get_nlp_analysis(self, session: Session, thought_id: UUID) -> Optional[dict]:
        """Get comprehensive NLP analysis for a thought."""
        db_thought = session.query(ThoughtModel).filter(ThoughtModel.id == thought_id).first()
        if not db_thought:
            return None
        
        # Get recent thoughts for novelty comparison
        recent_thoughts = session.query(ThoughtModel.content)\
            .filter(ThoughtModel.id != thought_id)\
            .order_by(desc(ThoughtModel.timestamp))\
            .limit(20)\
            .all()
        existing_content = [str(t.content) for t in recent_thoughts] if recent_thoughts else []
        
        return self.nlp_scorer.get_enhanced_analysis(str(db_thought.content), existing_content)
    
    def recalculate_importance_bulk(self, session: Session, limit: Optional[int] = None) -> int:
        """Recalculate importance scores for existing thoughts using enhanced NLP."""
        query = session.query(ThoughtModel).order_by(desc(ThoughtModel.timestamp))
        if limit:
            query = query.limit(limit)
        
        thoughts = query.all()
        updated_count = 0
        
        for thought in thoughts:
            # Get context for novelty calculation
            context_thoughts = session.query(ThoughtModel.content)\
                .filter(and_(
                    ThoughtModel.id != thought.id,
                    ThoughtModel.timestamp < thought.timestamp
                ))\
                .order_by(desc(ThoughtModel.timestamp))\
                .limit(10)\
                .all()
            existing_content = [str(t.content) for t in context_thoughts] if context_thoughts else []
            
            # Calculate new importance
            new_importance, _ = self.nlp_scorer.calculate_enhanced_importance(
                str(thought.content),
                existing_content=existing_content
            )
            
            # Update if significantly different  
            # Get the current importance value from the database object
            current_importance = getattr(thought, 'importance', None)
            if current_importance is None:
                current_importance = 0.0
            else:
                try:
                    current_importance = float(current_importance)
                except (TypeError, ValueError):
                    current_importance = 0.0
                    
            if abs(new_importance - current_importance) > 0.1:
                # Update the database field properly
                session.query(ThoughtModel)\
                    .filter(ThoughtModel.id == thought.id)\
                    .update({'importance': new_importance})
                updated_count += 1
        
        session.commit()
        self.logger.info(f"Updated importance scores for {updated_count} thoughts")
        return updated_count
    
    def _db_to_pydantic(self, db_thought: ThoughtModel) -> Thought:
        """Convert database model to Pydantic model."""
        thought_dict = db_thought.to_dict()
        return Thought(**thought_dict)
    
    def log_thought_from_chat(
        self, 
        session: Session, 
        content: str, 
        category: str,
        tags: Optional[List[str]] = None,
        emotion: Optional[str] = None,
        importance: Optional[float] = None
    ) -> Thought:
        """Helper method for logging thoughts from chat interface.
        
        This is a convenience method specifically designed for the chat interface
        to easily log both user messages and AI responses as thoughts.
        """
        thought_data = ThoughtCreate(
            category=category,  # type: ignore
            content=content,
            tags=tags or [],
            emotion=emotion,
            importance=importance
        )
        
        return self.create_thought(session, thought_data)


# Global logger instance
thought_logger = ThoughtLogger()
