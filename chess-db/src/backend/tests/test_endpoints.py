import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, Any
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"  # Update this if your server runs on a different port

class EndpointTester:
    def __init__(self):
        self.session = None
        self.results: Dict[str, Dict[str, Any]] = {}
        
    async def setup(self):
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        if self.session:
            await self.session.close()
            
    async def test_endpoint(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Test a single endpoint and return the results"""
        url = f"{BASE_URL}{endpoint}"
        start_time = datetime.now()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
            else:  # POST
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                        
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000  # in milliseconds
            
            result = {
                "status": status,
                "latency_ms": round(latency, 2),
                "success": 200 <= status < 300,
                "response": response_data if status != 200 else "Success"
            }
            
            logger.info(f"{method} {endpoint} - Status: {status} - Latency: {latency:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error testing {method} {endpoint}: {str(e)}")
            return {
                "status": 0,
                "latency_ms": 0,
                "success": False,
                "response": str(e)
            }

    async def run_all_tests(self):
        """Run all endpoint tests"""
        
        # Test Players endpoints
        self.results["/players/search"] = await self.test_endpoint("GET", "/players/search", {"q": "Nakamura", "limit": 10})
        self.results["/players/1394"] = await self.test_endpoint("GET", "/players/1394")
        self.results["/players/1394/performance"] = await self.test_endpoint("GET", "/players/1394/performance")
        self.results["/players/1394/detailed-stats"] = await self.test_endpoint("GET", "/players/1394/detailed-stats")
        
        # Test Games endpoints
        self.results["/games/count"] = await self.test_endpoint("GET", "/games/count")
        self.results["/games"] = await self.test_endpoint("GET", "/games", {"limit": 10})
        self.results["/games/suggest-players"] = await self.test_endpoint("GET", "/games/suggest-players", {"name": "Magnus", "limit": 10})
        self.results["/games/stats"] = await self.test_endpoint("GET", "/games/stats")
        self.results["/games/player"] = await self.test_endpoint("GET", "/games/player/Nakamura,Hi", {"limit": 10})
        self.results["/games/1394"] = await self.test_endpoint("GET", "/games/1394")
        
        # Test Analysis endpoints
        self.results["/analysis/move-counts"] = await self.test_endpoint("GET", "/analysis/move-counts")
        self.results["/analysis/database-metrics"] = await self.test_endpoint("GET", "/analysis/database-metrics")
        self.results["/analysis/players/1394/openings"] = await self.test_endpoint("GET", "/analysis/players/1394/openings")
        self.results["/analysis/openings/popular"] = await self.test_endpoint("GET", "/analysis/openings/popular")
        
    def generate_report(self):
        """Generate a summary report of all tests"""
        successful_tests = sum(1 for result in self.results.values() if result["success"])
        total_tests = len(self.results)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": f"{(successful_tests/total_tests)*100:.1f}%"
            },
            "results": self.results
        }
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"logs/endpoint_test_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"\nTest Report Summary:")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful Tests: {successful_tests}")
        logger.info(f"Failed Tests: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        logger.info(f"\nDetailed report saved to: {report_file}")

async def main():
    tester = EndpointTester()
    try:
        await tester.setup()
        await tester.run_all_tests()
        tester.generate_report()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
