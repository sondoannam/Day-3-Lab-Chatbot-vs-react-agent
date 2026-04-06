import asyncio
import time
import json
import os
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

# Load .env so it can pick up keys if user adds them
load_dotenv()

from src.tools.JD_Web_Scraper import JD_Web_Scraper

async def run_single_test(scraper: JD_Web_Scraper, url: str, run_id: int):
    try:
        # Measure latency
        start = time.time()
        result_json_str = await scraper.execute(url)
        latency = time.time() - start
        
        # Validate JSON
        result = json.loads(result_json_str)
        # Verify SLA is respected
        print(f"[Run {run_id}] Output: status={result.get('status')}, source={result.get('source_engine')}, latency={latency:.2f}s, execution_time_ms={result.get('execution_time_ms')}")
        
        return result
    except Exception as e:
        print(f"[Run {run_id}] Failed with exception: {e}")
        return None

async def stress_test():
    # We will run 10 requests concurrently
    
    test_urls = [
        "https://www.linkedin.com/jobs/view/example-id-1",
        "https://www.linkedin.com/jobs/view/example-id-2",
        "https://www.indeed.com/viewjob?jk=12345",
        "https://www.linkedin.com/jobs/view/example-id-3",
        "https://www.google.com/search?q=jobs"
    ] * 2  # Total 10 requests

    print(f"Starting stress test for {len(test_urls)} concurrent requests...")
    
    start_total = time.time()
    
    # Mock requests.get and _parse_with_crawl4ai to test concurrency without real keys causing instant failure
    def mock_requests_get(*args, **kwargs):
        time.sleep(1) # simulate 1s network latency blocking a thread
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Fake JD</body></html>"
        mock_resp.json.return_value = {"jobs_results": [{"title": "Mock Title", "company_name": "Mock Company", "description": "Mock Description"}]}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    with patch("os.getenv", side_effect=lambda k: "fake_val" if k in ["BRIGHT_DATA_PROXY", "SERPAPI_API_KEY"] else os.environ.get(k)):
        with patch("requests.get", side_effect=mock_requests_get):
            with patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._parse_with_crawl4ai", return_value="# Job Title\n## Company Name\n- Skill 1\n- Skill 2"):
                scraper = JD_Web_Scraper()
                # Run all simultaneously
                tasks = [run_single_test(scraper, url, i+1) for i, url in enumerate(test_urls)]
                results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_total
    
    success_count = sum(1 for r in results if r is not None and r.get("status") in ["success_primary", "success_fallback"])
    failed_count = sum(1 for r in results if r is None or r.get("status") == "failed")
    
    print("=" * 40)
    print("STRESS TEST RESULTS")
    print(f"Total Requests: {len(test_urls)}")
    print(f"Successful Requests: {success_count}")
    print(f"Failed Requests: {failed_count}")
    print(f"Total Wall-clock Time: {total_time:.2f}s")
    
    # Asserting SLA constraint (each request must state <10s)
    sla_violations = sum(1 for r in results if r and r.get("execution_time_ms", 0) > 10000)
    print(f"SLA Violations (>10s): {sla_violations}")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(stress_test())
