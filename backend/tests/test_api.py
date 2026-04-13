import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add the parent directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify the health check endpoint responds with 200 OK and expected JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "logsentinel-api"

@pytest.mark.asyncio
async def test_auth_validate_email_missing_token():
    """Verify that unauthenticated requests to the backend return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Simulating hitting the logs history without a Bearer token
        response = await ac.get("/api/v1/logs/history")
    
    # 401 Unauthorized expected because depends(verify_auth_token) failed
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
