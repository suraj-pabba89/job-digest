"""
scrapers/adzuna.py — Searches jobs via Adzuna API.
Free tier: 250 req/month. Register at https://developer.adzuna.com/
Requires: ADZUNA_APP_ID and ADZUNA_API_KEY in .env
"""
from __future__ import annotations

import logging
import os
from typing import List
from urllib.parse import urlencode

import requests

from .base import Job
from config import SEARCH_QUERY, MAX_AGE_DAYS

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
COUNTRIES = ["us", "gb", "ca", "au", "de", "fr", "in", "sg"]


class AdzunaScraper:
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "")
        self.api_key = os.getenv("ADZUNA_API_KEY", "")
        self.session = requests.Session()

    def _enabled(self) -> bool:
        return bool(self.app_id and self.api_key)

    def scrape(self, query: str = SEARCH_QUERY) -> List[Job]:
        if not self._enabled():
            logger.info("Adzuna: skipped (ADZUNA_APP_ID / ADZUNA_API_KEY not set)")
            return []

        jobs: List[Job] = []
        max_days = MAX_AGE_DAYS

        for country in COUNTRIES:
            try:
                params = {
                    "app_id": self.app_id,
                    "app_key": self.api_key,
                    "results_per_page": 50,
                    "what": query,
                    "max_days_old": max_days,
                    "content-type": "application/json",
                    "sort_by": "date",
                }
                url = BASE_URL.format(country=country, page=1)
                resp = self.session.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                for result in data.get("results", []):
                    location_data = result.get("location", {})
                    location_parts = location_data.get("area", [])
                    location = ", ".join(location_parts[-2:]) if location_parts else country.upper()

                    jobs.append(
                        Job(
                            title=result.get("title", ""),
                            company=result.get("company", {}).get("display_name", "Unknown"),
                            location=location,
                            url=result.get("redirect_url", ""),
                            source="Adzuna",
                            description=result.get("description", "")[:1500],
                        )
                    )
            except requests.RequestException as exc:
                logger.warning("Adzuna error (%s): %s", country, exc)

        logger.info("Adzuna: found %d jobs", len(jobs))
        return jobs
