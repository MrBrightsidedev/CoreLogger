from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ThoughtBase(BaseModel):
    """Base thought model with common fields."""
    
    category: str = Field(
        "reflection", description="Category of the thought"
    )
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Content of the thought"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the thought"
    )
    emotion: Optional[str] = Field(
        None, description="Emotional state or label"
    )
    importance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Importance score between 0 and 1"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        if not v:
            return []
        # Remove duplicates and clean whitespace
        cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned_tags

    @field_validator("emotion")
    @classmethod
    def validate_emotion(cls, v: Optional[str]) -> Optional[str]:
        """Validate emotion field."""
        if v is None:
            return None
        emotion = v.strip().lower()
        return emotion if emotion else None


class ThoughtCreate(BaseModel):
    """Schema for creating a new thought."""
    
    category: str = Field(
        "reflection", description="Category of the thought"
    )
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Content of the thought"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the thought"
    )
    emotion: Optional[str] = Field(
        None, description="Emotional state or label"
    )
    importance: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Importance score between 0 and 1"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        if not v:
            return []
        # Remove duplicates and clean whitespace
        cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned_tags

    @field_validator("emotion")
    @classmethod
    def validate_emotion(cls, v: Optional[str]) -> Optional[str]:
        """Validate emotion field."""
        if v is None:
            return None
        emotion = v.strip().lower()
        return emotion if emotion else None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "reflection",
                "content": "This is a sample thought",
                "tags": ["sample", "test"],
                "emotion": "neutral",
                "importance": 0.5
            }
        }
    )


class ThoughtUpdate(BaseModel):
    """Schema for updating an existing thought."""
    
    category: Optional[Literal["perception", "reflection", "decision", "tick", "error"]] = None
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    tags: Optional[List[str]] = None
    emotion: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if v is None:
            return None
        cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned_tags

    @field_validator("emotion")
    @classmethod
    def validate_emotion(cls, v: Optional[str]) -> Optional[str]:
        """Validate emotion field."""
        if v is None:
            return None
        emotion = v.strip().lower()
        return emotion if emotion else None


class Thought(ThoughtBase):
    """Complete thought model with all fields."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when thought was created"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class ThoughtResponse(Thought):
    """Response model for thought API endpoints."""
    pass


class ThoughtsListResponse(BaseModel):
    """Response model for listing thoughts."""
    
    thoughts: List[Thought]  # Changed from ThoughtResponse to Thought for compatibility
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class ThoughtQuery(BaseModel):
    """Query parameters for filtering thoughts."""
    
    # Basic filters
    category: Optional[str] = None  # Made more flexible for web interface
    tags: Optional[List[str]] = None
    tag: Optional[str] = None  # Single tag for web interface
    emotion: Optional[str] = None
    min_importance: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_importance: Optional[float] = Field(None, ge=0.0, le=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_term: Optional[str] = None
    search: Optional[str] = None  # Alternative search field
    
    # Pagination
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)
    
    # Ordering
    order_by: Optional[str] = Field("timestamp", description="Field to order by")
    order_desc: bool = Field(True, description="Whether to order in descending order")
    
    # Additional filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if v is None:
            return None
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category - allow any string for flexibility."""
        if v is None:
            return None
        return v.strip().lower() if v.strip() else None
