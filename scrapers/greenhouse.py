"""
scrapers/greenhouse.py — Pulls jobs from Greenhouse public job-board API.
No API key required; boards are public.
Endpoint: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
"""
from __future__ import annotations

import logging
import time
from typing import List

import requests

from .base import Job
from config import GREENHOUSE_COMPANIES, SEARCH_QUERY_VARIANTS

logger = logging.getLogger(__name__)

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
REQUEST_DELAY = 0.3  # seconds between company requests


class GreenhouseScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "JobDigestBot/1.0 (personal job tracker)",
            "Accept": "application/json",
        })

    def scrape(self, companies: List[str] = GREENHOUSE_COMPANIES) -> List[Job]:
        jobs: List[Job] = []
        keywords = [v.lower() for v in SEARCH_QUERY_VARIANTS]

        for slug in companies:
            try:
                url = BASE_URL.format(slug=slug)
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 404:
                    logger.debug("Greenhouse: no board for %s", slug)
                    time.sleep(REQUEST_DELAY)
                    continue
                resp.raise_for_status()
                data = resp.json()

                for posting in data.get("jobs", []):
                    title = posting.get("title", "")
                    title_lower = title.lower()

                    if not any(kw in title_lower for kw in keywords):
                        continue

                    location_parts = posting.get("location", {})
                    location = (
                        location_parts.get("name", "")
                        if isinstance(location_parts, dict)
                        else str(location_parts)
                    )

                    job = Job(
                        title=title,
                        company=data.get("name", slug.title()),
                        location=location or "Remote / Not specified",
                        url=posting.get("absolute_url", ""),
                        source="Greenhouse",
                        description=self._strip_html(
                            posting.get("content", "")[:1500]
                        ),
                    )
                    jobs.append(job)

            except requests.RequestException as exc:
                logger.warning("Greenhouse error for %s: %s", slug, exc)
            finally:
                time.sleep(REQUEST_DELAY)

        logger.info("Greenhouse: found %d relevant jobs", len(jobs))
        return jobs

    @staticmethod
    def _strip_html(html: str) -> str:
        """Very light HTML tag stripper (no extra deps needed)."""
        import re
        return re.sub(r"<[^>]+>", " ", html).strip()
