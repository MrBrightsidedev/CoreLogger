import pytest
from datetime import datetime
from uuid import uuid4

from models.thought import ThoughtCreate, ThoughtQuery, ThoughtUpdate
from services.logger import ThoughtLogger


class TestThoughtLogger:
    """Test cases for ThoughtLogger service."""
    
    def setup_method(self):
        """Set up test method."""
        self.logger = ThoughtLogger()
    
    def test_create_thought(self, db_session):
        """Test creating a thought."""
        # Arrange
        thought_data = ThoughtCreate(
            category="reflection",
            content="This is a test thought",
            tags=["test", "reflection"],
            emotion="curious",
            importance=0.7,
        )
        
        # Act
        thought = self.logger.create_thought(db_session, thought_data)
        
        # Assert
        assert thought.id is not None
        assert thought.timestamp is not None
        assert thought.category == "reflection"
        assert thought.content == "This is a test thought"
        assert "test" in thought.tags
        assert "reflection" in thought.tags
        assert thought.emotion == "curious"
        assert thought.importance == 0.7
    
    def test_create_thought_with_defaults(self, db_session):
        """Test creating a thought with default values."""
        # Arrange
        thought_data = ThoughtCreate(
            category="perception",
            content="Simple perception",
            tags=[],
            emotion=None,
            importance=None,
        )
        
        # Act
        thought = self.logger.create_thought(db_session, thought_data)
        
        # Assert
        assert thought.category == "perception"
        assert thought.content == "Simple perception"
        assert thought.tags == []
        assert thought.emotion is None
        assert thought.importance == 0.5  # Default from config
    
    def test_get_thought(self, db_session):
        """Test retrieving a thought by ID."""
        # Arrange
        thought_data = ThoughtCreate(
            category="decision",
            content="Test decision",
            tags=[],
            emotion=None,
            importance=None,
        )
        created_thought = self.logger.create_thought(db_session, thought_data)
        
        # Act
        retrieved_thought = self.logger.get_thought(db_session, created_thought.id)
        
        # Assert
        assert retrieved_thought is not None
        assert retrieved_thought.id == created_thought.id
        assert retrieved_thought.content == "Test decision"
    
    def test_get_nonexistent_thought(self, db_session):
        """Test retrieving a non-existent thought."""
        # Arrange
        fake_id = uuid4()
        
        # Act
        thought = self.logger.get_thought(db_session, fake_id)
        
        # Assert
        assert thought is None
    
    def test_update_thought(self, db_session):
        """Test updating a thought."""
        # Arrange
        thought_data = ThoughtCreate(
            category="reflection",
            content="Original content",
            tags=["original"],
            emotion=None,
            importance=None,
        )
        created_thought = self.logger.create_thought(db_session, thought_data)
        
        update_data = ThoughtUpdate(
            content="Updated content",
            tags=["updated", "modified"],
            importance=0.9,
        )
        
        # Act
        updated_thought = self.logger.update_thought(
            db_session, created_thought.id, update_data
        )
        
        # Assert
        assert updated_thought is not None
        assert updated_thought.id == created_thought.id
        assert updated_thought.content == "Updated content"
        assert "updated" in updated_thought.tags
        assert "modified" in updated_thought.tags
        assert updated_thought.importance == 0.9
        assert updated_thought.category == "reflection"  # Unchanged
    
    def test_delete_thought(self, db_session):
        """Test deleting a thought."""
        # Arrange
        thought_data = ThoughtCreate(
            category="tick",
            content="To be deleted",
            tags=[],
            emotion=None,
            importance=None,
        )
        created_thought = self.logger.create_thought(db_session, thought_data)
        
        # Act
        success = self.logger.delete_thought(db_session, created_thought.id)
        
        # Assert
        assert success is True
        
        # Verify deletion
        deleted_thought = self.logger.get_thought(db_session, created_thought.id)
        assert deleted_thought is None
    
    def test_delete_nonexistent_thought(self, db_session):
        """Test deleting a non-existent thought."""
        # Arrange
        fake_id = uuid4()
        
        # Act
        success = self.logger.delete_thought(db_session, fake_id)
        
        # Assert
        assert success is False
    
    def test_list_thoughts_no_filter(self, db_session):
        """Test listing thoughts without filters."""
        # Arrange
        thoughts_data = [
            ThoughtCreate(category="perception", content="Perception 1", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="Reflection 1", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="decision", content="Decision 1", tags=[], emotion=None, importance=None),
        ]
        
        for thought_data in thoughts_data:
            self.logger.create_thought(db_session, thought_data)
        
        # Act
        response = self.logger.list_thoughts(db_session)
        
        # Assert
        assert response.total >= 3
        assert len(response.thoughts) >= 3
        assert response.page == 1
        assert response.page_size == 50
    
    def test_list_thoughts_with_category_filter(self, db_session):
        """Test listing thoughts with category filter."""
        # Arrange
        thoughts_data = [
            ThoughtCreate(category="perception", content="Perception 1", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="perception", content="Perception 2", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="Reflection 1", tags=[], emotion=None, importance=None),
        ]
        
        for thought_data in thoughts_data:
            self.logger.create_thought(db_session, thought_data)
        
        query = ThoughtQuery(
            category="perception",
            tags=None,
            emotion=None,
            min_importance=None,
            max_importance=None,
            start_date=None,
            end_date=None,
            search_term=None,
        )
        
        # Act
        response = self.logger.list_thoughts(db_session, query)
        
        # Assert
        assert response.total >= 2
        for thought in response.thoughts:
            assert thought.category == "perception"
    
    def test_list_thoughts_with_tag_filter(self, db_session):
        """Test listing thoughts with tag filter."""
        # Arrange
        thoughts_data = [
            ThoughtCreate(category="reflection", content="Tagged 1", tags=["important"], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="Tagged 2", tags=["important", "urgent"], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="Not tagged", tags=[], emotion=None, importance=None),
        ]
        
        for thought_data in thoughts_data:
            self.logger.create_thought(db_session, thought_data)
        
        query = ThoughtQuery(
            category=None,
            tags=["important"],
            emotion=None,
            min_importance=None,
            max_importance=None,
            start_date=None,
            end_date=None,
            search_term=None,
        )
        
        # Act
        response = self.logger.list_thoughts(db_session, query)
        
        # Assert
        assert response.total >= 2
        for thought in response.thoughts:
            assert "important" in thought.tags
    
    def test_list_thoughts_with_search_filter(self, db_session):
        """Test listing thoughts with search filter."""
        # Arrange
        thoughts_data = [
            ThoughtCreate(category="reflection", content="This contains search term", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="This does not contain it", tags=[], emotion=None, importance=None),
            ThoughtCreate(category="reflection", content="Another search term example", tags=[], emotion=None, importance=None),
        ]
        
        for thought_data in thoughts_data:
            self.logger.create_thought(db_session, thought_data)
        
        query = ThoughtQuery(
            category=None,
            tags=None,
            emotion=None,
            min_importance=None,
            max_importance=None,
            start_date=None,
            end_date=None,
            search_term="search term",
        )
        
        # Act
        response = self.logger.list_thoughts(db_session, query)
        
        # Assert
        assert response.total >= 2
        for thought in response.thoughts:
            assert "search term" in thought.content.lower()
    
    def test_list_thoughts_pagination(self, db_session):
        """Test pagination in thought listing."""
        # Arrange
        for i in range(15):
            thought_data = ThoughtCreate(
                category="tick",
                content=f"Tick {i}",
                tags=[],
                emotion=None,
                importance=None,
            )
            self.logger.create_thought(db_session, thought_data)
        
        # Act - First page
        response_page1 = self.logger.list_thoughts(
            db_session, page=1, page_size=5
        )
        
        # Act - Second page
        response_page2 = self.logger.list_thoughts(
            db_session, page=2, page_size=5
        )
        
        # Assert
        assert response_page1.page == 1
        assert response_page1.page_size == 5
        assert len(response_page1.thoughts) == 5
        
        assert response_page2.page == 2
        assert response_page2.page_size == 5
        assert len(response_page2.thoughts) == 5
        
        # Ensure different thoughts on different pages
        page1_ids = {t.id for t in response_page1.thoughts}
        page2_ids = {t.id for t in response_page2.thoughts}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_convenience_methods(self, db_session):
        """Test convenience methods for different thought categories."""
        # Test log_perception
        perception = self.logger.log_perception(
            db_session, "I see something", tags=["visual"]
        )
        assert perception.category == "perception"
        assert perception.content == "I see something"
        assert "visual" in perception.tags
        
        # Test log_reflection
        reflection = self.logger.log_reflection(
            db_session, "I think about this", emotion="thoughtful"
        )
        assert reflection.category == "reflection"
        assert reflection.emotion == "thoughtful"
        
        # Test log_decision
        decision = self.logger.log_decision(
            db_session, "I decide to do this", importance=0.8
        )
        assert decision.category == "decision"
        assert decision.importance == 0.8
        
        # Test log_tick
        tick = self.logger.log_tick(db_session, "System tick")
        assert tick.category == "tick"
        
        # Test log_error
        error = self.logger.log_error(db_session, "An error occurred")
        assert error.category == "error"
