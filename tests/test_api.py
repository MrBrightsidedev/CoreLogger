import pytest
from uuid import uuid4

from models.thought import ThoughtCreate


class TestAPI:
    """Test cases for CoreLogger REST API."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs_url" in data
    
    def test_create_thought(self, client):
        """Test creating a thought via API."""
        thought_data = {
            "category": "reflection",
            "content": "This is a test thought via API",
            "tags": ["test", "api"],
            "emotion": "curious",
            "importance": 0.7,
        }
        
        response = client.post("/api/v1/thoughts", json=thought_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["category"] == "reflection"
        assert data["content"] == "This is a test thought via API"
        assert "test" in data["tags"]
        assert "api" in data["tags"]
        assert data["emotion"] == "curious"
        assert data["importance"] == 0.7
        assert "id" in data
        assert "timestamp" in data
    
    def test_create_thought_minimal(self, client):
        """Test creating a thought with minimal data."""
        thought_data = {
            "category": "perception",
            "content": "Simple perception",
        }
        
        response = client.post("/api/v1/thoughts", json=thought_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["category"] == "perception"
        assert data["content"] == "Simple perception"
        assert data["tags"] == []
        assert data["emotion"] is None
    
    def test_create_thought_invalid_category(self, client):
        """Test creating a thought with invalid category."""
        thought_data = {
            "category": "invalid",
            "content": "Test content",
        }
        
        response = client.post("/api/v1/thoughts", json=thought_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_thought_missing_content(self, client):
        """Test creating a thought without content."""
        thought_data = {
            "category": "reflection",
        }
        
        response = client.post("/api/v1/thoughts", json=thought_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_thought(self, client):
        """Test retrieving a thought by ID."""
        # Create a thought first
        thought_data = {
            "category": "decision",
            "content": "Test decision",
        }
        
        create_response = client.post("/api/v1/thoughts", json=thought_data)
        assert create_response.status_code == 201
        thought_id = create_response.json()["id"]
        
        # Get the thought
        response = client.get(f"/api/v1/thoughts/{thought_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == thought_id
        assert data["content"] == "Test decision"
    
    def test_get_nonexistent_thought(self, client):
        """Test retrieving a non-existent thought."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/thoughts/{fake_id}")
        assert response.status_code == 404
    
    def test_update_thought(self, client):
        """Test updating a thought."""
        # Create a thought first
        thought_data = {
            "category": "reflection",
            "content": "Original content",
        }
        
        create_response = client.post("/api/v1/thoughts", json=thought_data)
        thought_id = create_response.json()["id"]
        
        # Update the thought
        update_data = {
            "content": "Updated content",
            "importance": 0.9,
        }
        
        response = client.put(f"/api/v1/thoughts/{thought_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["importance"] == 0.9
        assert data["category"] == "reflection"  # Unchanged
    
    def test_delete_thought(self, client):
        """Test deleting a thought."""
        # Create a thought first
        thought_data = {
            "category": "tick",
            "content": "To be deleted",
        }
        
        create_response = client.post("/api/v1/thoughts", json=thought_data)
        thought_id = create_response.json()["id"]
        
        # Delete the thought
        response = client.delete(f"/api/v1/thoughts/{thought_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/v1/thoughts/{thought_id}")
        assert get_response.status_code == 404
    
    def test_list_thoughts(self, client):
        """Test listing thoughts."""
        # Create some thoughts
        thoughts_data = [
            {"category": "perception", "content": "Perception 1"},
            {"category": "reflection", "content": "Reflection 1"},
            {"category": "decision", "content": "Decision 1"},
        ]
        
        for thought_data in thoughts_data:
            client.post("/api/v1/thoughts", json=thought_data)
        
        # List thoughts
        response = client.get("/api/v1/thoughts")
        assert response.status_code == 200
        
        data = response.json()
        assert "thoughts" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 3
    
    def test_list_thoughts_with_filters(self, client):
        """Test listing thoughts with filters."""
        # Create some thoughts
        thoughts_data = [
            {"category": "perception", "content": "Perception with tag", "tags": ["important"]},
            {"category": "reflection", "content": "Reflection without tag"},
        ]
        
        for thought_data in thoughts_data:
            client.post("/api/v1/thoughts", json=thought_data)
        
        # Filter by category
        response = client.get("/api/v1/thoughts?category=perception")
        assert response.status_code == 200
        data = response.json()
        for thought in data["thoughts"]:
            assert thought["category"] == "perception"
        
        # Filter by tags
        response = client.get("/api/v1/thoughts?tags=important")
        assert response.status_code == 200
        data = response.json()
        for thought in data["thoughts"]:
            assert "important" in thought["tags"]
    
    def test_list_thoughts_pagination(self, client):
        """Test pagination in thought listing."""
        # Create multiple thoughts
        for i in range(15):
            thought_data = {"category": "tick", "content": f"Tick {i}"}
            client.post("/api/v1/thoughts", json=thought_data)
        
        # Test pagination
        response = client.get("/api/v1/thoughts?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["thoughts"]) == 5
    
    def test_convenience_endpoints(self, client):
        """Test convenience endpoints for different thought categories."""
        
        # Test perception endpoint
        response = client.post(
            "/api/v1/thoughts/perception",
            params={"content": "I see something", "tags": ["visual"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "perception"
        assert data["content"] == "I see something"
        
        # Test reflection endpoint
        response = client.post(
            "/api/v1/thoughts/reflection",
            params={"content": "I think about this", "emotion": "thoughtful"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "reflection"
        assert data["emotion"] == "thoughtful"
        
        # Test decision endpoint
        response = client.post(
            "/api/v1/thoughts/decision",
            params={"content": "I decide to do this", "importance": 0.8},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "decision"
        assert data["importance"] == 0.8
        
        # Test tick endpoint
        response = client.post(
            "/api/v1/thoughts/tick",
            params={"content": "System tick"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "tick"
        
        # Test error endpoint
        response = client.post(
            "/api/v1/thoughts/error",
            params={"content": "An error occurred"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "error"
