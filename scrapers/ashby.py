"""
scrapers/ashby.py — Pulls jobs from Ashby public job-board API.
No API key required.
Endpoint: https://api.ashbyhq.com/posting-api/job-board/{slug}
"""
from __future__ import annotations

import logging
import time
from typing import List

import requests

from .base import Job
from config import ASHBY_COMPANIES, SEARCH_QUERY_VARIANTS

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"
REQUEST_DELAY = 0.3


class AshbyScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "JobDigestBot/1.0",
            "Accept": "application/json",
        })

    def scrape(self, companies: List[str] = ASHBY_COMPANIES) -> List[Job]:
        jobs: List[Job] = []
        keywords = [v.lower() for v in SEARCH_QUERY_VARIANTS]

        for slug in companies:
            try:
                url = BASE_URL.format(slug=slug)
                resp = self.session.get(url, timeout=10)
                if resp.status_code in (404, 422):
                    logger.debug("Ashby: no board for %s", slug)
                    time.sleep(REQUEST_DELAY)
                    continue
                resp.raise_for_status()
                data = resp.json()

                company_name = data.get("organization", {}).get(
                    "name", slug.replace("-", " ").title()
                )

                for posting in data.get("jobPostings", []):
                    title = posting.get("title", "")
                    title_lower = title.lower()

                    if not any(kw in title_lower for kw in keywords):
                        continue

                    location_list = posting.get("locationName", "") or ""
                    if isinstance(location_list, list):
                        location_list = ", ".join(location_list)

                    job = Job(
                        title=title,
                        company=company_name,
                        location=location_list or "Remote / Not specified",
                        url=posting.get("jobPostingUrl", ""),
                        source="Ashby",
                        description=self._extract_description(posting),
                    )
                    jobs.append(job)

            except requests.RequestException as exc:
                logger.warning("Ashby error for %s: %s", slug, exc)
            finally:
                time.sleep(REQUEST_DELAY)

        logger.info("Ashby: found %d relevant jobs", len(jobs))
        return jobs

    @staticmethod
    def _extract_description(posting: dict) -> str:
        import re
        raw = posting.get("descriptionHtml", "") or posting.get("description", "")
        return re.sub(r"<[^>]+>", " ", raw).strip()[:1500]
