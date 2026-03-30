"""
scrapers/indeed.py — Scrapes Indeed job search results.
Indeed has aggressive bot detection; this uses realistic headers
and a short delay. For production, consider a proxy/residential IP.
"""
from __future__ import annotations

import logging
import re
import time
from typing import List
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .base import Job
from config import SEARCH_QUERY, MAX_AGE_DAYS

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.indeed.com/jobs"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
# fromage=1 means "posted in last 1 day"
FROMAGE = str(MAX_AGE_DAYS)


class IndeedScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    def scrape(self, query: str = SEARCH_QUERY, pages: int = 3) -> List[Job]:
        jobs: List[Job] = []

        for page in range(pages):
            params = {
                "q": query,
                "l": "",          # blank = worldwide
                "sort": "date",
                "fromage": FROMAGE,
                "start": page * 10,
            }
            url = f"{SEARCH_URL}?{urlencode(params)}"
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code in (403, 429):
                    logger.warning("Indeed: blocked (status %d)", resp.status_code)
                    break
                resp.raise_for_status()

                page_jobs = self._parse_html(resp.text)
                if not page_jobs:
                    break
                jobs.extend(page_jobs)
                time.sleep(3)
            except requests.RequestException as exc:
                logger.warning("Indeed error (page %d): %s", page, exc)
                break

        logger.info("Indeed: found %d jobs", len(jobs))
        return jobs

    def _parse_html(self, html: str) -> List[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Job] = []

        # Indeed uses multiple card layouts; try both selectors
        cards = soup.select("div.job_seen_beacon") or soup.select("div.tapItem")

        for card in cards:
            try:
                title_el = card.select_one("h2.jobTitle span[title]") or card.select_one("h2.jobTitle")
                company_el = card.select_one("[data-testid='company-name']") or card.select_one(".companyName")
                location_el = card.select_one("[data-testid='text-location']") or card.select_one(".companyLocation")
                link_el = card.select_one("a[id^='job_']") or card.select_one("a.jcs-JobTitle")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else ""

                href = ""
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        href = f"https://www.indeed.com{href}"

                if not title:
                    continue

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location or "Not specified",
                        url=href,
                        source="Indeed",
                    )
                )
            except (AttributeError, KeyError, TypeError):
                continue

        return jobs
