"""
scrapers/base.py — Shared Job dataclass and base scraper interface.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str                          # which scraper found it
    description: str = ""
    funding_stage: str = ""              # filled by enrichment layer
    funding_amount: str = ""
    fit_reason: str = ""                 # filled by AI layer
    posted_date: str = ""

    @property
    def uid(self) -> str:
        """Stable dedup key based on company + title + url."""
        raw = f"{self.company.lower()}::{self.title.lower()}::{self.url}"
        return hashlib.md5(raw.encode()).hexdigest()

    def is_relevant(self, query: str) -> bool:
        """Case-insensitive check that the job title contains relevant keywords."""
        title_lower = self.title.lower()
        keywords = [w.lower() for w in query.split()]
        return any(k in title_lower for k in keywords)
