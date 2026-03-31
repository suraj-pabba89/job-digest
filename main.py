#!/usr/bin/env python3
"""
main.py — Daily Forward Deployed Engineer job digest orchestrator.

Run manually:    python main.py
Run with dry run (no email): python main.py --dry-run
Save HTML to file: python main.py --save-html digest.html
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv(Path(__file__).parent / ".env")

from config import TO_EMAIL, EMAIL_SUBJECT, SEARCH_QUERY
from scrapers import (
    Job,
    GreenhouseScraper,
    LeverScraper,
    AshbyScraper,
    LinkedInScraper,
    IndeedScraper,
    WellfoundScraper,
    AdzunaScraper,
)
from enrichment import CrunchbaseEnricher
from ai_fitter import generate_fit_reasons
from email_template import render_email
from sender import send_digest

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def run_scrapers() -> List[Job]:
    """Runs all scrapers concurrently and returns deduplicated jobs."""

    scrapers = {
        "Greenhouse": lambda: GreenhouseScraper().scrape(),
        "Lever":      lambda: LeverScraper().scrape(),
        "Ashby":      lambda: AshbyScraper().scrape(),
        "LinkedIn":   lambda: LinkedInScraper().scrape(SEARCH_QUERY),
        "Indeed":     lambda: IndeedScraper().scrape(SEARCH_QUERY),
        "Wellfound":  lambda: WellfoundScraper().scrape(),
        "Adzuna":     lambda: AdzunaScraper().scrape(SEARCH_QUERY),
    }

    all_jobs: List[Job] = []
    seen_uids: Dict[str, bool] = {}

    # Run scrapers in parallel (I/O bound)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn): name for name, fn in scrapers.items()}

        for future in as_completed(futures):
            name = futures[future]
            try:
                jobs = future.result()
                new = 0
                for job in jobs:
                    if job.uid not in seen_uids:
                        seen_uids[job.uid] = True
                        all_jobs.append(job)
                        new += 1
                logger.info("%-12s → %3d jobs (%d new after dedup)", name, len(jobs), new)
            except Exception as exc:
                logger.error("Scraper %s failed: %s", name, exc)

    logger.info("Total unique jobs: %d", len(all_jobs))
    return all_jobs


_USA_TERMS = {
    "united states", "usa", "u.s.", "u.s.a", "us only",
    "remote", "remote us", "remote (us)", "remote - us",
    # states
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming", "washington dc", "washington, dc", "d.c.",
    # common US cities
    "san francisco", "new york", "los angeles", "chicago", "seattle",
    "austin", "boston", "denver", "atlanta", "miami", "dallas",
    "houston", "phoenix", "portland", "san jose", "san diego",
    "new york city", "nyc", "sf", "bay area", "silicon valley",
}


def _filter_usa(jobs: List[Job]) -> List[Job]:
    """Keep only jobs with a US location (or no location specified)."""
    result = []
    for job in jobs:
        loc = job.location.lower().strip()
        if not loc or any(term in loc for term in _USA_TERMS):
            result.append(job)
    return result


def main(dry_run: bool = False, save_html: str = "") -> None:
    logger.info("=" * 60)
    logger.info("FDE Job Digest — %s", date.today())
    logger.info("=" * 60)

    # ── 1. Scrape ─────────────────────────────────────────────────────────
    logger.info("Step 1/4 — Scraping job boards…")
    jobs = run_scrapers()

    if not jobs:
        logger.warning("No jobs found today — sending empty digest.")

    # ── 2. Enrich with funding data ───────────────────────────────────────
    logger.info("Step 2/4 — Enriching with Crunchbase funding data…")
    try:
        enricher = CrunchbaseEnricher()
        jobs = enricher.enrich(jobs)
    except Exception as exc:
        logger.warning("Crunchbase enrichment failed: %s", exc)

    # ── 3. Generate "why I'd fit" one-liners ─────────────────────────────
    logger.info("Step 3/4 — Generating 'why I'd fit' reasons…")
    try:
        jobs = generate_fit_reasons(jobs)
    except Exception as exc:
        logger.warning("Fit-reason generation failed: %s", exc)

    # ── 4. Filter to USA only and keep top 10 ────────────────────────────
    jobs = _filter_usa(jobs)
    logger.info("After USA filter: %d jobs", len(jobs))
    seen_companies: Dict[str, int] = {}
    top10 = []
    for job in sorted(jobs, key=lambda j: j.fit_score, reverse=True):
        company_key = job.company.lower().strip()
        if seen_companies.get(company_key, 0) < 1:
            top10.append(job)
            seen_companies[company_key] = seen_companies.get(company_key, 0) + 1
        if len(top10) == 10:
            break
    jobs = top10
    logger.info("Top 10 jobs selected (1 per company).")

    # ── 5. Render HTML and send ───────────────────────────────────────────
    logger.info("Step 4/4 — Rendering email and sending…")
    html = render_email(jobs)

    if save_html:
        Path(save_html).write_text(html, encoding="utf-8")
        logger.info("HTML saved to: %s", save_html)

    if dry_run:
        logger.info("--dry-run flag set: skipping email send.")
        logger.info("Found %d jobs. HTML written to stdout below.\n", len(jobs))
        print(html[:2000], "... [truncated]")
        return

    success = send_digest(html, TO_EMAIL, EMAIL_SUBJECT)
    if success:
        logger.info("✓ Digest sent to %s with %d jobs.", TO_EMAIL, len(jobs))
    else:
        logger.error("✗ Email send failed — check GMAIL_ADDRESS / GMAIL_APP_PASSWORD in .env")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily FDE Job Digest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and generate digest but do not send email",
    )
    parser.add_argument(
        "--save-html",
        metavar="FILE",
        default="",
        help="Save the rendered HTML email to a file (e.g. digest.html)",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run, save_html=args.save_html)
