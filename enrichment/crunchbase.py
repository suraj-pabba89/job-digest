"""
enrichment/crunchbase.py — Enriches jobs with company funding data.

Two methods:
1. Crunchbase Basic API (requires CRUNCHBASE_API_KEY in .env)
   Free tier: 200 req/day — https://data.crunchbase.com/docs
2. Fallback: scrapes the company's Crunchbase page (best-effort, no key)
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Dict, List, Optional

import requests

from scrapers.base import Job

logger = logging.getLogger(__name__)

CRUNCHBASE_API = "https://api.crunchbase.com/api/v4/entities/organizations/{slug}"
CRUNCHBASE_SEARCH = "https://api.crunchbase.com/api/v4/searches/organizations"
AUTOCOMPLETE_URL = "https://api.crunchbase.com/api/v4/autocompletes"

# Simple in-process cache: company_name -> (funding_stage, funding_amount)
_CACHE: Dict[str, tuple[str, str]] = {}


class CrunchbaseEnricher:
    def __init__(self):
        self.api_key = os.getenv("CRUNCHBASE_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JobDigestBot/1.0",
            "Accept": "application/json",
        })

    def _api_enabled(self) -> bool:
        return bool(self.api_key)

    def enrich(self, jobs: List[Job]) -> List[Job]:
        """Enriches jobs in-place with funding stage/amount."""
        companies_seen: Dict[str, tuple[str, str]] = {}

        for job in jobs:
            key = job.company.strip().lower()
            if key in _CACHE:
                job.funding_stage, job.funding_amount = _CACHE[key]
                continue
            if key in companies_seen:
                job.funding_stage, job.funding_amount = companies_seen[key]
                _CACHE[key] = companies_seen[key]
                continue

            stage, amount = "", ""
            if self._api_enabled():
                stage, amount = self._fetch_via_api(job.company)
            else:
                stage, amount = self._fetch_via_scrape(job.company)

            job.funding_stage = stage
            job.funding_amount = amount
            companies_seen[key] = (stage, amount)
            _CACHE[key] = (stage, amount)
            time.sleep(0.2)

        return jobs

    # ── API path ──────────────────────────────────────────────────────────

    def _fetch_via_api(self, company_name: str) -> tuple[str, str]:
        try:
            # Step 1: autocomplete to get the slug
            resp = self.session.get(
                AUTOCOMPLETE_URL,
                params={
                    "query": company_name,
                    "collection_ids": "organizations",
                    "user_key": self.api_key,
                },
                timeout=10,
            )
            resp.raise_for_status()
            entities = resp.json().get("entities", [])
            if not entities:
                return "", ""

            slug = entities[0].get("identifier", {}).get("permalink", "")
            if not slug:
                return "", ""

            # Step 2: fetch org details
            org_resp = self.session.get(
                CRUNCHBASE_API.format(slug=slug),
                params={
                    "user_key": self.api_key,
                    "field_ids": "funding_stage,funding_total,last_funding_type",
                },
                timeout=10,
            )
            org_resp.raise_for_status()
            props = org_resp.json().get("properties", {})

            stage = props.get("last_funding_type", "") or props.get("funding_stage", "")
            total = props.get("funding_total", {})
            amount = ""
            if total:
                value = total.get("value_usd", 0)
                amount = self._format_usd(value)

            return stage, amount

        except Exception as exc:
            logger.debug("Crunchbase API error for %s: %s", company_name, exc)
            return "", ""

    # ── Scrape fallback ───────────────────────────────────────────────────

    def _fetch_via_scrape(self, company_name: str) -> tuple[str, str]:
        """Best-effort public Crunchbase page scrape (no API key needed)."""
        try:
            slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
            url = f"https://www.crunchbase.com/organization/{slug}"
            resp = self.session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                return "", ""

            text = resp.text
            # Look for structured funding info in the page source
            stage_match = re.search(
                r'"funding_stage"\s*:\s*"([^"]+)"', text
            ) or re.search(r'Series [A-Z]|Seed|Pre-Seed|IPO|Acquired|Series [A-Z]\d', text)
            amount_match = re.search(
                r'"funding_total"[^}]*"value_usd"\s*:\s*(\d+)', text
            )

            stage = stage_match.group(1) if stage_match else ""
            amount = self._format_usd(int(amount_match.group(1))) if amount_match else ""
            return stage, amount

        except Exception as exc:
            logger.debug("Crunchbase scrape error for %s: %s", company_name, exc)
            return "", ""

    @staticmethod
    def _format_usd(value: int) -> str:
        if not value:
            return ""
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.0f}M"
        if value >= 1_000:
            return f"${value / 1_000:.0f}K"
        return f"${value}"
