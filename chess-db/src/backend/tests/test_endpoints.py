"""Test endpoints for the API."""

import pytest
import aiohttp
import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from sqlalchemy import text

# Add the backend directory to Python path for imports
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from config import API_BASE_URL as BASE_URL
from database import get_session

logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "DB_HOST": "localhost",
    "TESTING": "true",
    "SAMPLE_PLAYER_ID": "1394",
    "MIN_GAMES": "5",
    "LIMIT": "10"
}

# Apply test configuration
for key, value in TEST_CONFIG.items():
    os.environ[key] = value

@pytest.fixture
async def client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Fixture to create and manage aiohttp client session."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
async def db_session():
    """Fixture to create and manage database session."""
    async for session in get_session():
        yield session

class TestEndpoints:
    """Test class for API endpoints."""
    
    async def _make_request(
        self, 
        session: aiohttp.ClientSession, 
        method: str, 
        endpoint: str,
        params: Dict[str, Any] = None
    ) -> dict:
        """Make an HTTP request to the API endpoint.
        
        Args:
            session: The aiohttp client session
            method: HTTP method
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            dict: Response data including success status and response content
        """
        url = f"{BASE_URL}{endpoint}"
        start_time = datetime.now()
        
        try:
            async with session.request(method, url, params=params) as response:
                status = response.status
                response_data = await response.read()  # Read raw bytes first
                response_size = len(response_data)  # Get exact size in bytes
                
                # Parse JSON if successful
                if status == 200:
                    try:
                        response_content = json.loads(response_data)
                    except json.JSONDecodeError:
                        response_content = response_data.decode('utf-8')
                else:
                    response_content = response_data.decode('utf-8')
                
                duration = (datetime.now() - start_time).total_seconds()
                
                result = {
                    "success": status == 200,
                    "status": status,
                    "response": response_content,
                    "duration": duration,
                    "size": response_size
                }
                
                log_level = logging.INFO if status == 200 else logging.ERROR
                logger.log(
                    log_level,
                    f"{method} {endpoint} - Status: {status} - Size: {response_size} bytes - Duration: {duration:.2f}s"
                )
                return result
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error testing {method} {endpoint}: {str(e)}")
            return {
                "success": False,
                "status": 500,
                "response": str(e),
                "duration": duration,
                "size": 0
            }

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client_session):
        """Test health check endpoint."""
        logger.info("Testing health endpoint...")
        result = await self._make_request(client_session, "GET", "/health")
        assert result["success"], "Health check endpoint failed"
        assert result["status"] == 200
        assert "response" in result

    @pytest.mark.asyncio
    async def test_database_status(self, client_session):
        """Test database status endpoint."""
        result = await self._make_request(client_session, "GET", "/api/database/status")
        assert result["success"], "Database status check failed"
        assert result["status"] == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", [
        "/api/games/recent",
        "/api/games/count",
        "/api/games"
    ])
    async def test_game_endpoints(self, client_session, endpoint):
        """Test game-related endpoints."""
        result = await self._make_request(client_session, "GET", endpoint)
        assert result["success"], f"Game endpoint {endpoint} failed"
        assert result["status"] == 200
        assert "response" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint,params", [
        ("/api/analysis/move-counts", None),
        ("/api/analysis/database-metrics", None),
        ("/api/analysis/openings/popular", {"min_games": TEST_CONFIG["MIN_GAMES"], "limit": TEST_CONFIG["LIMIT"]})
    ])
    async def test_analysis_endpoints(self, client_session, endpoint, params):
        """Test analysis endpoints."""
        result = await self._make_request(client_session, "GET", endpoint, params)
        assert result["success"], f"Analysis endpoint {endpoint} failed"
        assert result["status"] == 200
        assert "response" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint,params", [
        ("/api/players/search", {"q": "Naka", "limit": TEST_CONFIG["LIMIT"]}),
        (f"/api/players/{TEST_CONFIG['SAMPLE_PLAYER_ID']}", None),
        (f"/api/players/{TEST_CONFIG['SAMPLE_PLAYER_ID']}/openings", {"min_games": TEST_CONFIG["MIN_GAMES"]}),
        (f"/api/players/{TEST_CONFIG['SAMPLE_PLAYER_ID']}/performance", None),
        (f"/api/players/{TEST_CONFIG['SAMPLE_PLAYER_ID']}/games", None)
    ])
    async def test_player_endpoints(self, client_session, endpoint, params):
        """Test player-related endpoints."""
        result = await self._make_request(client_session, "GET", endpoint, params)
        assert result["success"], f"Player endpoint {endpoint} failed"
        assert result["status"] == 200
        assert "response" in result

    @pytest.mark.asyncio
    async def test_player_routes(self, client_session):
        """Test player-related endpoints."""
        logger.info("Testing player routes...")

        # Test player search with different parameters
        logger.info("- Testing player search...")
        search_params = [
            {"q": "a"},  # Basic search
            {"q": "a", "limit": 5},  # With limit
            {"q": "magnus"},  # Specific player search
        ]
        for params in search_params:
            result = await self._make_request(client_session, "GET", "/api/players/search", params)
            assert result["success"], f"Player search failed with params {params}"
            assert result["status"] == 200
            assert isinstance(result["response"], list), "Player search should return a list"

        # Get a player ID for further tests
        result = await self._make_request(client_session, "GET", "/api/players/search", {"q": "a"})
        player_id = result["response"][0]["id"] if result["response"] else 1

        # Test get player details
        logger.info("- Testing get player details...")
        result = await self._make_request(client_session, "GET", f"/api/players/{player_id}")
        assert result["success"], "Get player details endpoint failed"
        assert result["status"] == 200
        assert "id" in result["response"], "Player details should include id"
        assert "username" in result["response"], "Player details should include username"

        # Test player performance with different time periods
        logger.info("- Testing player performance...")
        time_periods = [None, "1y", "6m", "3m", "1m"]
        for period in time_periods:
            params = {"time_period": period} if period else {}
            result = await self._make_request(
                client_session, 
                "GET", 
                f"/api/players/{player_id}/performance",
                params
            )
            assert result["success"], f"Player performance failed for period {period}"
            assert result["status"] == 200
            assert isinstance(result["response"], list), "Performance data should be a list"

        # Test player detailed stats
        logger.info("- Testing player detailed stats...")
        result = await self._make_request(client_session, "GET", f"/api/players/{player_id}/detailed-stats")
        assert result["success"], "Player detailed stats endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], dict), "Detailed stats should be a dictionary"

        # Test player openings with various parameters
        logger.info("- Testing player openings...")
        opening_params = [
            {},  # Default parameters
            {"min_games": 3},  # Custom min games
            {"limit": 5},  # Custom limit
            {"start_date": "2023-01-01"},  # With start date
            {"end_date": "2023-12-31"},  # With end date
            {  # Combined parameters
                "min_games": 3,
                "limit": 5,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        ]
        for params in opening_params:
            result = await self._make_request(
                client_session, 
                "GET", 
                f"/api/players/{player_id}/openings",
                params
            )
            assert result["success"], f"Player openings failed with params {params}"
            assert result["status"] == 200
            assert isinstance(result["response"], dict), "Opening analysis should be a dictionary"

        # Test error cases
        logger.info("- Testing error cases...")
        
        # Invalid player ID
        result = await self._make_request(client_session, "GET", "/api/players/999999")
        assert result["status"] == 404, "Should return 404 for invalid player ID"

        # Invalid date format
        result = await self._make_request(
            client_session,
            "GET",
            f"/api/players/{player_id}/openings",
            {"start_date": "invalid-date"}
        )
        assert result["status"] == 400, "Should return 400 for invalid date format"

        # Invalid time period
        result = await self._make_request(
            client_session,
            "GET",
            f"/api/players/{player_id}/performance",
            {"time_period": "invalid"}
        )
        assert result["status"] == 400, "Should return 400 for invalid time period"

    @pytest.mark.asyncio
    async def test_game_routes(self, client_session):
        """Test game-related endpoints."""
        logger.info("Testing game routes...")
        
        # Test game count
        logger.info("- Testing game count...")
        result = await self._make_request(client_session, "GET", "/api/games/count")
        assert result["success"], "Game count endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], int), "Game count should return an integer"

        # Test recent games
        logger.info("- Testing recent games...")
        result = await self._make_request(client_session, "GET", "/api/games/recent")
        assert result["success"], "Recent games endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], list), "Recent games should return a list"

        # Test game stats
        logger.info("- Testing game stats...")
        result = await self._make_request(client_session, "GET", "/api/games/stats")
        assert result["success"], "Game stats endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], dict), "Game stats should return a dictionary"

        # Test player suggestions
        logger.info("- Testing player suggestions...")
        result = await self._make_request(client_session, "GET", "/api/games/players/suggest", {"name": "a"})
        assert result["success"], "Player suggestions endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], list), "Player suggestions should return a list"

        # Test game list with filters
        logger.info("- Testing game list with filters...")
        result = await self._make_request(
            client_session, 
            "GET", 
            "/api/games",
            {"limit": 5, "move_notation": "uci"}
        )
        assert result["success"], "Game list endpoint failed"
        assert result["status"] == 200
        assert isinstance(result["response"], list), "Game list should return a list"

    @pytest.mark.asyncio
    async def test_analysis_routes(self, client_session):
        """Test analysis-related endpoints."""
        logger.info("Testing analysis routes...")

        # Test move count distribution
        logger.info("- Testing move count distribution...")
        result = await self._make_request(client_session, "GET", "/api/analysis/move-counts")
        assert result["success"], "Move count distribution endpoint failed"
        assert result["status"] == 200

        # Test popular openings
        # logger.info("- Testing popular openings...")
        # result = await self._make_request(client_session, "GET", "/api/analysis/popular-openings")
        # assert result["success"], "Popular openings endpoint failed"
        # assert result["status"] == 200

        # Test database metrics
        logger.info("- Testing database metrics...")
        result = await self._make_request(client_session, "GET", "/api/analysis/database-metrics")
        assert result["success"], "Database metrics endpoint failed"
        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_database_routes(self, client_session):
        """Test database-related endpoints."""
        logger.info("Testing database routes...")

        # Test database status
        logger.info("- Testing database status...")
        result = await self._make_request(client_session, "GET", "/api/database/status")
        assert result["success"], "Database status endpoint failed"
        assert result["status"] == 200

        # Test database metrics
        logger.info("- Testing database metrics...")
        result = await self._make_request(client_session, "GET", "/api/database/metrics")
        assert result["success"], "Database metrics endpoint failed"
        assert result["status"] == 200

        # Test endpoint metrics
        logger.info("- Testing endpoint metrics...")
        result = await self._make_request(client_session, "GET", "/api/database/metrics/endpoints")
        assert result["success"], "Endpoint metrics endpoint failed"
        assert result["status"] == 200

        # Test health metrics
        logger.info("- Testing health metrics...")
        result = await self._make_request(client_session, "GET", "/api/database/metrics/health")
        assert result["success"], "Health metrics endpoint failed"
        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_metrics_recording(self, db_session):
        """Test that endpoint metrics are being recorded."""
        if os.getenv("TESTING") == "true":
            pytest.skip("Skipping metrics recording test in test mode")
            
        try:
            result = await db_session.execute(
                text("""
                SELECT endpoint, method, success_count, error_count, avg_response_time
                FROM endpoint_metrics
                WHERE endpoint = '/health'
                """)
            )
            row = result.fetchone()
            assert row is not None, "No metrics found for health endpoint"
            
        except Exception as e:
            pytest.fail(f"Error checking endpoint metrics: {str(e)}")

    @pytest.mark.asyncio
    async def run_all_tests(self, _):
        """Run all endpoint tests"""
        async with aiohttp.ClientSession() as client_session:
            logger.info("Starting endpoint tests")
            
            # Test health endpoint
            await self.test_health_endpoint(client_session)
            
            # Test analysis routes
            await self.test_analysis_routes(client_session)
            
            # Test player routes
            await self.test_player_routes(client_session)
            
            # Test game routes
            await self.test_game_routes(client_session)
            
            # Test database routes
            await self.test_database_routes(client_session)
            
            logger.info("All endpoint tests completed successfully")
            
@pytest.mark.asyncio
async def main():
    """Main test runner"""
    logger.info("Starting endpoint tests")
    
    try:
        tester = TestEndpoints()
        await tester.run_all_tests(None)  # Pass None as client_session since we'll create it inside run_all_tests
        logger.info("All tests completed")
            
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Initializing test suite")
    asyncio.run(main())
    logger.info("Test suite completed")
