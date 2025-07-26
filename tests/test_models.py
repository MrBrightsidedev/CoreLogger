import pytest

from models.thought import (
    Thought,
    ThoughtCreate,
    ThoughtQuery,
    ThoughtUpdate,
    ThoughtsListResponse,
)


class TestPydanticModels:
    """Test cases for Pydantic models."""
    
    def test_thought_create_valid(self):
        """Test creating a valid ThoughtCreate."""
        thought = ThoughtCreate(
            category="reflection",
            content="This is a test thought",
            tags=["test", "reflection"],
            emotion="curious",
            importance=0.7,
        )
        
        assert thought.category == "reflection"
        assert thought.content == "This is a test thought"
        assert "test" in thought.tags
        assert "reflection" in thought.tags
        assert thought.emotion == "curious"
        assert thought.importance == 0.7
    
    def test_thought_create_minimal(self):
        """Test creating ThoughtCreate with minimal data."""
        thought = ThoughtCreate(
            category="perception",
            content="Simple perception",
            tags=[],
            emotion=None,
            importance=None,
        )
        
        assert thought.category == "perception"
        assert thought.content == "Simple perception"
        assert thought.tags == []
        assert thought.emotion is None
        assert thought.importance is None
    
    def test_thought_create_invalid_category(self):
        """Test ThoughtCreate with invalid category."""
        with pytest.raises(ValueError):
            # Use a dynamic value to bypass type checking
            invalid_category = "invalid"
            ThoughtCreate(
                category=invalid_category,  # type: ignore
                content="Test content",
                tags=[],
                emotion=None,
                importance=None,
            )
    
    def test_thought_create_empty_content(self):
        """Test ThoughtCreate with empty content."""
        with pytest.raises(ValueError):
            ThoughtCreate(
                category="reflection",
                content="",
                tags=[],
                emotion=None,
                importance=None,
            )
    
    def test_thought_create_invalid_importance(self):
        """Test ThoughtCreate with invalid importance."""
        with pytest.raises(ValueError):
            ThoughtCreate(
                category="reflection",
                content="Test content",
                tags=[],
                emotion=None,
                importance=1.5,  # > 1.0
            )
        
        with pytest.raises(ValueError):
            ThoughtCreate(
                category="reflection",
                content="Test content",
                tags=[],
                emotion=None,
                importance=-0.1,  # < 0.0
            )
    
    def test_thought_tags_validation(self):
        """Test tag validation and cleaning."""
        thought = ThoughtCreate(
            category="reflection",
            content="Test content",
            tags=["  Test  ", "test", "REFLECTION", "reflection", ""],
            emotion=None,
            importance=None,
        )
        
        # Should remove duplicates, clean whitespace, and convert to lowercase
        assert len(thought.tags) == 2
        assert "test" in thought.tags
        assert "reflection" in thought.tags
    
    def test_thought_emotion_validation(self):
        """Test emotion validation and cleaning."""
        # Valid emotion
        thought1 = ThoughtCreate(
            category="reflection",
            content="Test content",
            tags=[],
            emotion="  Happy  ",
            importance=None,
        )
        assert thought1.emotion == "happy"
        
        # Empty emotion should become None
        thought2 = ThoughtCreate(
            category="reflection",
            content="Test content",
            tags=[],
            emotion="   ",
            importance=None,
        )
        assert thought2.emotion is None
    
    def test_thought_update_validation(self):
        """Test ThoughtUpdate validation."""
        update = ThoughtUpdate(
            content="Updated content",
            tags=["new", "tags"],
            importance=0.9,
        )
        
        assert update.content == "Updated content"
        assert update.tags is not None
        assert "new" in update.tags
        assert "tags" in update.tags
        assert update.importance == 0.9
        assert update.category is None  # Not updated
        assert update.emotion is None  # Not updated
    
    def test_thought_query_validation(self):
        """Test ThoughtQuery validation."""
        query = ThoughtQuery(
            category="reflection",
            tags=["important", "urgent"],
            emotion=None,
            min_importance=0.5,
            max_importance=0.9,
            start_date=None,
            end_date=None,
            search_term="test",
        )
        
        assert query.category == "reflection"
        assert query.tags is not None
        assert "important" in query.tags
        assert "urgent" in query.tags
        assert query.min_importance == 0.5
        assert query.max_importance == 0.9
        assert query.search_term == "test"
    
    def test_thought_with_defaults(self):
        """Test Thought model with default values."""
        thought = Thought(
            category="perception",
            content="Test perception",
            tags=[],
            emotion=None,
            importance=None,
        )
        
        assert thought.id is not None
        assert thought.timestamp is not None
        assert thought.category == "perception"
        assert thought.content == "Test perception"
        assert thought.tags == []
        assert thought.emotion is None
        assert thought.importance is None
    
    def test_thoughts_list_response(self):
        """Test ThoughtsListResponse model."""
        thoughts = [
            Thought(category="reflection", content="Thought 1", tags=[], emotion=None, importance=None),
            Thought(category="perception", content="Thought 2", tags=[], emotion=None, importance=None),
        ]
        
        response = ThoughtsListResponse(
            thoughts=thoughts,
            total=2,
            page=1,
            page_size=10,
            total_pages=1,
        )
        
        assert len(response.thoughts) == 2
        assert response.total == 2
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 1
