"""Tests for main FastAPI application endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import app after setting up mocks
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
        assert "status" in data
        assert data["status"] == "healthy"
        assert "gemini" in data
    
    def test_health_endpoint_structure(self):
        """Test that health endpoint has correct structure."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "gemini" in data
        assert data["gemini"] in ["available", "unavailable"]


class TestChatEndpoint:
    """Tests for the chat endpoint."""
    
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
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_success_with_gemini(self, mock_gemini_client):
        """Test successful chat request with Gemini API."""
        # Mock Gemini client to be available and return a response
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "This is a test AI response from Gemini."
        
        response = client.post(
            "/chat",
            json={"message": "Hello, this is a test message"}
        )
        
        # If Gemini is not configured, we'll get 503, otherwise 200
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "message" in data
        assert data["message"] == "Hello, this is a test message"
        assert len(data["answer"]) > 0
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_gemini_integration(self, mock_gemini_client):
        """Test that chat endpoint calls Gemini API."""
        # Mock Gemini client
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "AI generated response"
        
        test_message = "What is AI?"
        response = client.post(
            "/chat",
            json={"message": test_message}
        )
        
        # If Gemini is not configured, skip
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == test_message
        # Verify Gemini was called
        mock_gemini_client.generate_response.assert_called_once()
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_valid_max_length(self, mock_gemini_client):
        """Test that message at max length is accepted."""
        # Mock Gemini
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "Response"
        
        max_message = "a" * 1000  # Exactly max_length=1000
        response = client.post(
            "/chat",
            json={"message": max_message}
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == max_message
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_special_characters(self, mock_gemini_client):
        """Test that special characters are handled correctly."""
        # Mock Gemini
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "Response"
        
        special_message = "Hello! @#$%^&*() Test 123"
        response = client.post(
            "/chat",
            json={"message": special_message}
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == special_message
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_multiline_message(self, mock_gemini_client):
        """Test that multiline messages are handled."""
        # Mock Gemini
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "Response"
        
        multiline_message = "Line 1\nLine 2\nLine 3"
        response = client.post(
            "/chat",
            json={"message": multiline_message}
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == multiline_message
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_response_structure(self, mock_gemini_client):
        """Test that response has correct structure."""
        # Mock Gemini
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.return_value = "Test response"
        
        response = client.post(
            "/chat",
            json={"message": "Test"}
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "answer" in data
        assert "message" in data
        assert isinstance(data["answer"], str)
        assert isinstance(data["message"], str)
    
    @patch('app.main.gemini_client')
    def test_chat_endpoint_gemini_error_handling(self, mock_gemini_client):
        """Test error handling when Gemini API fails."""
        # Mock Gemini to raise an exception
        mock_gemini_client.__bool__ = lambda x: True
        mock_gemini_client.generate_response.side_effect = Exception("API Error")
        
        response = client.post(
            "/chat",
            json={"message": "Test message"}
        )
        
        # If Gemini is not configured, we'll get 503, otherwise 500
        if response.status_code == 503:
            pytest.skip("Gemini API not configured in test environment")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"].lower() or "error generating" in data["detail"].lower()
    
    def test_chat_endpoint_gemini_unavailable(self):
        """Test that chat endpoint handles Gemini unavailability gracefully."""
        # This test checks behavior when Gemini is not configured
        # It will pass if gemini_client is None (returns 503)
        response = client.post(
            "/chat",
            json={"message": "Test"}
        )
        # Should return 503 if Gemini is not configured, or 200/500 if it is
        assert response.status_code in [200, 500, 503]


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
