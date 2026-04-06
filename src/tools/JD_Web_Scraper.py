import os
import time
import asyncio
import requests
import json
from typing import Dict, Optional, Literal
from pydantic import BaseModel, HttpUrl

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_configs import CrawlerRunConfig
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter
except ImportError:
    # Handle gracefully for environments missing crawl4ai
    AsyncWebCrawler = None
    CrawlerRunConfig = None
    DefaultMarkdownGenerator = None
    PruningContentFilter = None

class JDMetaData(BaseModel):
    job_title: str
    company: str

class JDScraperOutput(BaseModel):
    status: Literal["success_primary", "success_fallback", "failed"]
    source_engine: Literal["bright_data", "serp_api", "none"]
    execution_time_ms: int
    raw_markdown: str
    meta_data: JDMetaData

class JD_Web_Scraper:
    def __init__(self):
        self.bright_data_proxy = os.getenv("BRIGHT_DATA_PROXY")
        self.serp_api_key = os.getenv("SERPAPI_API_KEY")

    async def execute(self, url: str) -> str:
        """
        Executes the scraping process according to the Master Prompt constraints.
        Must return a strict JSON string mapping to JDScraperOutput.
        """
        start_time = time.time()

        status: Literal["success_primary", "success_fallback", "failed"] = "failed"
        source_engine: Literal["bright_data", "serp_api", "none"] = "none"
        raw_markdown = ""
        meta_data = JDMetaData(job_title="Unknown", company="Unknown")

        # STEP 1: Primary Extraction (Bright Data Web Unlocker + Crawl4AI)
        raw_html = await self._fetch_with_bright_data(url)

        if raw_html:
            parsed_markdown = await self._parse_with_crawl4ai(raw_html, url)
            if parsed_markdown:
                status = "success_primary"
                source_engine = "bright_data"
                raw_markdown = parsed_markdown
                # Simple extraction, in production this could be an NER step
                meta_data = self._extract_metadata(parsed_markdown)

        # STEP 2: Error Handling & SerpApi Fallback
        if status == "failed":
            fallback_result = await self._fetch_with_serp_api(url)
            if fallback_result:
                status = "success_fallback"
                source_engine = "serp_api"
                raw_markdown = fallback_result.get("description", "")
                meta_data = JDMetaData(
                    job_title=fallback_result.get("title", "Unknown"),
                    company=fallback_result.get("company", "Unknown")
                )

        # Ensure execution time stays under SLA (10 seconds)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Construct payload
        output = JDScraperOutput(
            status=status,
            source_engine=source_engine,
            execution_time_ms=execution_time_ms,
            raw_markdown=raw_markdown,
            meta_data=meta_data
        )

        return json.dumps(output.model_dump(), ensure_ascii=False)

    async def _fetch_with_bright_data(self, url: str) -> Optional[str]:
        """
        Uses Bright Data Web Unlocker API via standard proxy requests.
        Includes User-Agent rotation implicitly handled by the unlocker.
        """
        if not self.bright_data_proxy:
            return None

        proxies = {
            "http": self.bright_data_proxy,
            "https": self.bright_data_proxy
            }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

        try:
            response = await asyncio.to_thread(
                requests.get,
                url, 
                proxies=proxies, 
                headers=headers, 
                verify=False, 
                timeout=6  # Keep within SLA
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    async def _parse_with_crawl4ai(self, raw_html: str, url: str) -> Optional[str]:
        """
        STEP 3: Parses the raw HTML using Crawl4AI with PruningContentFilter.
        """
        try:
            md_generator = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(),
                options={
                    "ignore_links": True,
                    "ignore_images": True
                }
            )

            run_config = CrawlerRunConfig(markdown_generator=md_generator)

            async with AsyncWebCrawler() as crawler:
                # Inject raw HTML directly using raw:// scheme
                result = await crawler.arun(url=f"raw://{raw_html}", config=run_config)
                
                if hasattr(result, "markdown_v2") and hasattr(result.markdown_v2, "fit_markdown"):
                    return result.markdown_v2.fit_markdown
                return result.markdown
        except Exception:
            # Fallback if parsing fails
            return None

    async def _fetch_with_serp_api(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fallback to SerpApi using Google Jobs engine if primary extraction fails.
        """
        if not self.serp_api_key:
            return None

        # Build precise query as instructed
        params = {
            "engine": "google_jobs",
            "q": f'site:linkedin.com/jobs/view "{url}"',
            "api_key": self.serp_api_key,
            "no_cache": "true",
            "async": "false"
        }

        try:
            response = await asyncio.to_thread(requests.get, "https://serpapi.com/search", params=params, timeout=3)
            response.raise_for_status()
            data = response.json()

            jobs_results = data.get("jobs_results", [])
            if jobs_results:
                job = jobs_results[0]
                return {
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "description": job.get("description", "")
                }
            return None
        except requests.RequestException:
            return None

    def _extract_metadata(self, markdown_text: str) -> JDMetaData:
        """
        Simple extraction of metadata from the parsed text.
        In a real scenario, this might use lightweight LLM NER or sophisticated regex.
        """
        lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
        
        title = lines[0].replace("#", "").strip() if len(lines) > 0 else "Unknown"
        company = lines[1].replace("#", "").strip() if len(lines) > 1 else "Unknown"
        
        return JDMetaData(job_title=title, company=company)
