"""
scrapers/linkedin.py — Scrapes LinkedIn Jobs guest search endpoint.
Uses the public (non-authenticated) jobs listing HTML API.
No login required, but LinkedIn may throttle. Add delays as needed.
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

# 86400s = 1 day, 604800s = 1 week
TIME_FILTER = {1: "r86400", 7: "r604800", 30: "r2592000"}

GUEST_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.linkedin.com/jobs/search/",
}


class LinkedInScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    def scrape(self, query: str = SEARCH_QUERY, pages: int = 3) -> List[Job]:
        jobs: List[Job] = []
        time_filter = TIME_FILTER.get(MAX_AGE_DAYS, "r86400")

        for page in range(pages):
            start = page * 25
            params = {
                "keywords": query,
                "location": "",
                "f_TPR": time_filter,
                "start": start,
                "count": 25,
            }
            url = f"{GUEST_SEARCH_URL}?{urlencode(params)}"
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 429:
                    logger.warning("LinkedIn: rate limited, stopping")
                    break
                resp.raise_for_status()

                page_jobs = self._parse_html(resp.text)
                if not page_jobs:
                    break
                jobs.extend(page_jobs)
                time.sleep(2)  # be polite
            except requests.RequestException as exc:
                logger.warning("LinkedIn error (page %d): %s", page, exc)
                break

        logger.info("LinkedIn: found %d jobs", len(jobs))
        return jobs

    def _parse_html(self, html: str) -> List[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Job] = []

        for card in soup.select("li"):
            try:
                title_el = card.select_one(".base-search-card__title")
                company_el = card.select_one(".base-search-card__subtitle")
                location_el = card.select_one(".job-search-card__location")
                link_el = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else ""
                url = link_el["href"].split("?")[0] if link_el else ""

                if not title or not url:
                    continue

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location or "Not specified",
                        url=url,
                        source="LinkedIn",
                    )
                )
            except (AttributeError, KeyError, TypeError):
                continue

        return jobs
