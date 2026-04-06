import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.tools.JD_Web_Scraper import JD_Web_Scraper

@pytest.fixture
def scraper():
    with patch("os.getenv", side_effect=lambda k: "fake_val" if k in ["BRIGHT_DATA_PROXY", "SERPAPI_API_KEY"] else None):
        return JD_Web_Scraper()

@pytest.mark.asyncio
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._fetch_with_bright_data")
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._parse_with_crawl4ai", new_callable=AsyncMock)
async def test_execute_primary_success(mock_parse, mock_fetch, scraper):
    mock_fetch.return_value = "<html><body>Fake JD</body></html>"
    mock_parse.return_value = "# Job Title\n## Company Name\n- Skill 1\n- Skill 2"
    
    result_json_str = await scraper.execute("http://fake.url")
    result = json.loads(result_json_str)
    
    assert result["status"] == "success_primary"
    assert result["source_engine"] == "bright_data"
    assert result["execution_time_ms"] < 10000
    assert result["raw_markdown"] == "# Job Title\n## Company Name\n- Skill 1\n- Skill 2"
    assert result["meta_data"]["job_title"] == "Job Title"
    assert result["meta_data"]["company"] == "Company Name"


@pytest.mark.asyncio
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._fetch_with_bright_data", return_value=None)
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._fetch_with_serp_api")
async def test_execute_fallback_success(mock_serp, mock_bright, scraper):
    mock_serp.return_value = {
        "title": "Fallback Job",
        "company": "Fallback Company",
        "description": "Fallback Description"
    }
    
    result_json_str = await scraper.execute("http://fake.url")
    result = json.loads(result_json_str)
    
    assert result["status"] == "success_fallback"
    assert result["source_engine"] == "serp_api"
    assert result["meta_data"]["job_title"] == "Fallback Job"
    assert result["meta_data"]["company"] == "Fallback Company"
    assert result["raw_markdown"] == "Fallback Description"

@pytest.mark.asyncio
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._fetch_with_bright_data", return_value=None)
@patch("src.tools.JD_Web_Scraper.JD_Web_Scraper._fetch_with_serp_api", return_value=None)
async def test_execute_failed(mock_serp, mock_bright, scraper):
    result_json_str = await scraper.execute("http://fake.url")
    result = json.loads(result_json_str)
    
    assert result["status"] == "failed"
    assert result["source_engine"] == "none"
