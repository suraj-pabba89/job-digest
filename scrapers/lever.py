"""
scrapers/lever.py — Pulls jobs from Lever public posting API.
No API key required; postings are public.
Endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
"""
from __future__ import annotations

import logging
import time
from typing import List

import requests

from .base import Job
from config import LEVER_COMPANIES, SEARCH_QUERY_VARIANTS

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json&limit=250"
REQUEST_DELAY = 0.3


class LeverScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "JobDigestBot/1.0",
            "Accept": "application/json",
        })

    def scrape(self, companies: List[str] = LEVER_COMPANIES) -> List[Job]:
        jobs: List[Job] = []
        keywords = [v.lower() for v in SEARCH_QUERY_VARIANTS]

        for slug in companies:
            try:
                url = BASE_URL.format(slug=slug)
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 404:
                    logger.debug("Lever: no board for %s", slug)
                    time.sleep(REQUEST_DELAY)
                    continue
                resp.raise_for_status()
                postings = resp.json()

                for posting in postings:
                    title = posting.get("text", "")
                    title_lower = title.lower()

                    if not any(kw in title_lower for kw in keywords):
                        continue

                    categories = posting.get("categories", {})
                    location = categories.get("location", "") or categories.get(
                        "allLocations", [""]
                    )
                    if isinstance(location, list):
                        location = ", ".join(location)

                    description_html = posting.get("descriptionPlain", "") or ""

                    job = Job(
                        title=title,
                        company=slug.replace("-", " ").title(),
                        location=location or "Remote / Not specified",
                        url=posting.get("hostedUrl", ""),
                        source="Lever",
                        description=description_html[:1500],
                    )
                    jobs.append(job)

            except requests.RequestException as exc:
                logger.warning("Lever error for %s: %s", slug, exc)
            finally:
                time.sleep(REQUEST_DELAY)

        logger.info("Lever: found %d relevant jobs", len(jobs))
        return jobs
