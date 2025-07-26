from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import get_db
from models.thought import (
    ThoughtCreate,
    ThoughtQuery,
    ThoughtResponse,
    ThoughtsListResponse,
    ThoughtUpdate,
)
from services import thought_logger

router = APIRouter(prefix="/api/v1", tags=["thoughts"])


@router.post("/thoughts", response_model=ThoughtResponse, status_code=201)
async def create_thought(
    thought: ThoughtCreate,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Create a new thought."""
    try:
        created_thought = thought_logger.create_thought(db, thought)
        return ThoughtResponse(**created_thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/thoughts", response_model=ThoughtsListResponse)
async def list_thoughts(
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    emotion: Optional[str] = Query(None),
    min_importance: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_importance: Optional[float] = Query(None, ge=0.0, le=1.0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search_term: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    order_by: str = Query("timestamp"),
    order_desc: bool = Query(True),
    db: Session = Depends(get_db)
) -> ThoughtsListResponse:
    """List thoughts with optional filtering and pagination."""
    
    # Validate category if provided
    if category is not None:
        valid_categories = ["perception", "reflection", "decision", "tick", "error"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
    
    try:
        query = ThoughtQuery(
            category=category,  # type: ignore
            tags=tags,
            emotion=emotion,
            min_importance=min_importance,
            max_importance=max_importance,
            start_date=start_date,
            end_date=end_date,
            search_term=search_term,
            page=page,
            size=page_size,
            order_by=order_by,
            order_desc=order_desc,
        )
        
        response = thought_logger.list_thoughts(db, query)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/thoughts/{thought_id}", response_model=ThoughtResponse)
async def get_thought(
    thought_id: UUID,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Get a specific thought by ID."""
    thought = thought_logger.get_thought(db, thought_id)
    if not thought:
        raise HTTPException(status_code=404, detail="Thought not found")
    return ThoughtResponse(**thought.model_dump())


@router.put("/thoughts/{thought_id}", response_model=ThoughtResponse)
async def update_thought(
    thought_id: UUID,
    update_data: ThoughtUpdate,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Update an existing thought."""
    thought = thought_logger.update_thought(db, thought_id, update_data)
    if not thought:
        raise HTTPException(status_code=404, detail="Thought not found")
    return ThoughtResponse(**thought.model_dump())


@router.delete("/thoughts/{thought_id}", status_code=204)
async def delete_thought(
    thought_id: UUID,
    db: Session = Depends(get_db)
) -> None:
    """Delete a thought by ID."""
    success = thought_logger.delete_thought(db, thought_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thought not found")


# Convenience endpoints for specific thought categories

@router.post("/thoughts/perception", response_model=ThoughtResponse, status_code=201)
async def log_perception(
    content: str,
    tags: Optional[List[str]] = None,
    emotion: Optional[str] = None,
    importance: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Log a perception thought."""
    try:
        thought = thought_logger.log_perception(
            db, content, tags=tags or [], emotion=emotion, importance=importance
        )
        return ThoughtResponse(**thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/thoughts/reflection", response_model=ThoughtResponse, status_code=201)
async def log_reflection(
    content: str,
    tags: Optional[List[str]] = None,
    emotion: Optional[str] = None,
    importance: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Log a reflection thought."""
    try:
        thought = thought_logger.log_reflection(
            db, content, tags=tags or [], emotion=emotion, importance=importance
        )
        return ThoughtResponse(**thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/thoughts/decision", response_model=ThoughtResponse, status_code=201)
async def log_decision(
    content: str,
    tags: Optional[List[str]] = None,
    emotion: Optional[str] = None,
    importance: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Log a decision thought."""
    try:
        thought = thought_logger.log_decision(
            db, content, tags=tags or [], emotion=emotion, importance=importance
        )
        return ThoughtResponse(**thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/thoughts/tick", response_model=ThoughtResponse, status_code=201)
async def log_tick(
    content: str,
    tags: Optional[List[str]] = None,
    importance: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Log a system tick thought."""
    try:
        thought = thought_logger.log_tick(
            db, content, tags=tags or [], importance=importance
        )
        return ThoughtResponse(**thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/thoughts/error", response_model=ThoughtResponse, status_code=201)
async def log_error(
    content: str,
    tags: Optional[List[str]] = None,
    importance: Optional[float] = None,
    db: Session = Depends(get_db)
) -> ThoughtResponse:
    """Log an error thought."""
    try:
        thought = thought_logger.log_error(
            db, content, tags=tags or [], importance=importance
        )
        return ThoughtResponse(**thought.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
