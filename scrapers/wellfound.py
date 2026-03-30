"""
scrapers/wellfound.py — Scrapes Wellfound (AngelList Talent) job search.
Wellfound uses server-side rendering for role pages; this hits
the public role URL which lists companies hiring for a given role.
"""
from __future__ import annotations

import logging
import re
import time
from typing import List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .base import Job
from config import SEARCH_QUERY

logger = logging.getLogger(__name__)

BASE_ROLE_URL = "https://wellfound.com/role/r/{slug}"
SEARCH_URL = "https://wellfound.com/jobs?q={query}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Pre-known role slugs that correspond to FDE-type roles on Wellfound
ROLE_SLUGS = [
    "forward-deployed-engineer",
    "solutions-engineer",
    "field-engineer",
    "implementation-engineer",
    "customer-success-engineer",
]


class WellfoundScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    def scrape(self) -> List[Job]:
        jobs: List[Job] = []

        for slug in ROLE_SLUGS:
            url = BASE_ROLE_URL.format(slug=slug)
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 404:
                    continue
                if resp.status_code in (403, 429):
                    logger.warning("Wellfound: blocked for slug %s", slug)
                    time.sleep(5)
                    continue
                resp.raise_for_status()

                page_jobs = self._parse_role_page(resp.text, slug)
                jobs.extend(page_jobs)
                time.sleep(2)
            except requests.RequestException as exc:
                logger.warning("Wellfound error (%s): %s", slug, exc)

        logger.info("Wellfound: found %d jobs", len(jobs))
        return jobs

    def _parse_role_page(self, html: str, slug: str) -> List[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Job] = []

        # Wellfound role pages list job cards
        for card in soup.select("[data-test='StartupResult'], div.styles_component__Ey28k, div[class*='JobListing']"):
            try:
                title_el = card.select_one("a[class*='jobTitle'], span[class*='title'], h2")
                company_el = card.select_one("a[class*='startupName'], span[class*='company'], h3")
                location_el = card.select_one("span[class*='location'], [data-test='location']")
                link_el = card.select_one("a[href*='/jobs/']") or card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                location = location_el.get_text(strip=True) if location_el else "Remote / Not specified"

                href = ""
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        href = f"https://wellfound.com{href}"

                if title:
                    jobs.append(
                        Job(
                            title=title or slug.replace("-", " ").title(),
                            company=company or "Unknown",
                            location=location,
                            url=href,
                            source="Wellfound",
                        )
                    )
            except (AttributeError, KeyError):
                continue

        return jobs
