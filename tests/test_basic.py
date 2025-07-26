import pytest
from uuid import uuid4

from models.thought import ThoughtCreate, ThoughtQuery, ThoughtUpdate


def test_thought_create_basic():
    """Test basic ThoughtCreate functionality."""
    thought = ThoughtCreate(
        category="reflection",
        content="This is a test thought",
        tags=[],
        emotion=None,
        importance=None,
    )
    
    assert thought.category == "reflection"
    assert thought.content == "This is a test thought"
    assert thought.tags == []
    assert thought.emotion is None
    assert thought.importance is None


def test_thought_create_with_all_fields():
    """Test ThoughtCreate with all fields."""
    thought = ThoughtCreate(
        category="perception",
        content="I see something interesting",
        tags=["visual", "important"],
        emotion="curious",
        importance=0.8
    )
    
    assert thought.category == "perception"
    assert thought.content == "I see something interesting"
    assert "visual" in thought.tags
    assert "important" in thought.tags
    assert thought.emotion == "curious"
    assert thought.importance == 0.8


def test_thought_update_basic():
    """Test basic ThoughtUpdate functionality."""
    update = ThoughtUpdate(
        content="Updated content",
        importance=None,
    )
    
    assert update.content == "Updated content"
    assert update.category is None
    assert update.tags is None
    assert update.emotion is None
    assert update.importance is None


def test_thought_query_basic():
    """Test basic ThoughtQuery functionality."""
    query = ThoughtQuery(
        min_importance=None,
        max_importance=None,
    )
    
    assert query.category is None
    assert query.tags is None
    assert query.emotion is None
    assert query.min_importance is None
    assert query.max_importance is None
    assert query.search_term is None


def test_thought_query_with_filters():
    """Test ThoughtQuery with filters."""
    query = ThoughtQuery(
        category="reflection",
        tags=["important"],
        search_term="test",
        min_importance=None,
        max_importance=None,
    )
    
    assert query.category == "reflection"
    assert query.tags == ["important"]
    assert query.search_term == "test"
