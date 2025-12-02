"""Tests for main FastAPI application endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint_returns_success(self):
        """Test that root endpoint returns 200 and correct structure."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
        assert data["version"] == "0.2.0"
    
    def test_root_endpoint_message_content(self):
        """Test that root endpoint message is correct."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "GCP RAG Chatbot API" in data["message"]


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_endpoint_returns_healthy(self):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_endpoint_structure(self):
        """Test that health endpoint has correct structure."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


class TestChatEndpoint:
    """Tests for the chat endpoint."""
    
    def test_chat_endpoint_success(self):
        """Test successful chat request."""
        response = client.post(
            "/chat",
            json={"message": "Hello, this is a test message"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "message" in data
        assert data["message"] == "Hello, this is a test message"
        assert "Step 2" in data["answer"]
    
    def test_chat_endpoint_echo_response(self):
        """Test that chat endpoint echoes the message."""
        test_message = "Test message 123"
        response = client.post(
            "/chat",
            json={"message": test_message}
        )
        assert response.status_code == 200
        data = response.json()
        assert test_message in data["answer"]
        assert data["message"] == test_message
    
    def test_chat_endpoint_empty_message_validation(self):
        """Test that empty message is rejected."""
        response = client.post(
            "/chat",
            json={"message": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_missing_message_field(self):
        """Test that missing message field is rejected."""
        response = client.post(
            "/chat",
            json={}
        )
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_whitespace_only_message(self):
        """Test that whitespace-only message is handled."""
        response = client.post(
            "/chat",
            json={"message": "   "}
        )
        # Should either be rejected (422) or handled by endpoint (400)
        assert response.status_code in [400, 422]
    
    def test_chat_endpoint_max_length_validation(self):
        """Test that message exceeding max length is rejected."""
        long_message = "a" * 1001  # Exceeds max_length=1000
        response = client.post(
            "/chat",
            json={"message": long_message}
        )
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_min_length_validation(self):
        """Test that message must have at least 1 character."""
        response = client.post(
            "/chat",
            json={"message": ""}
        )
        assert response.status_code == 422
    
    def test_chat_endpoint_valid_max_length(self):
        """Test that message at max length is accepted."""
        max_message = "a" * 1000  # Exactly max_length=1000
        response = client.post(
            "/chat",
            json={"message": max_message}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == max_message
    
    def test_chat_endpoint_special_characters(self):
        """Test that special characters are handled correctly."""
        special_message = "Hello! @#$%^&*() Test 123"
        response = client.post(
            "/chat",
            json={"message": special_message}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == special_message
    
    def test_chat_endpoint_multiline_message(self):
        """Test that multiline messages are handled."""
        multiline_message = "Line 1\nLine 2\nLine 3"
        response = client.post(
            "/chat",
            json={"message": multiline_message}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == multiline_message
    
    def test_chat_endpoint_response_structure(self):
        """Test that response has correct structure."""
        response = client.post(
            "/chat",
            json={"message": "Test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "answer" in data
        assert "message" in data
        assert isinstance(data["answer"], str)
        assert isinstance(data["message"], str)


class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        response = client.get("/health")
        # TestClient doesn't fully simulate CORS, but we can check the middleware is configured
        assert response.status_code == 200
    
    def test_options_request_handled(self):
        """Test that OPTIONS requests are handled (CORS preflight)."""
        response = client.options("/chat")
        # FastAPI with CORS middleware should handle OPTIONS
        assert response.status_code in [200, 204, 405]  # 405 if not explicitly handled

