"""
ai_fitter.py — Generates personalised "why I'd fit" one-liners using Claude.

Uses Anthropic's claude-haiku model (fast + cheap for daily digest use).
Falls back to a rule-based generator if ANTHROPIC_API_KEY is not set.
"""
from __future__ import annotations

import logging
import os
import re
from typing import List

from scrapers.base import Job
from config import RESUME

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Suraj's resume summary — injected into every prompt so Claude has context
# ─────────────────────────────────────────────────────────────────────────────
_RESUME_SUMMARY = RESUME  # config.py now holds the real resume (see below)

# Rule-based keywords → snippet map (fallback when no API key)
_RULE_BUCKETS = [
    (
        ["llm", "ai", "ml", "language model", "generative", "gpt", "anthropic", "openai",
         "agent", "rag", "embedding", "vector"],
        "Having built and scaled LLM field applications at Treehouse (from $300K to $1M/month MRR) "
        "and co-founded InField AI with 20+ Fortune 500 pilots, I can bridge cutting-edge AI "
        "capabilities to enterprise customer value from day one.",
    ),
    (
        ["salesforce", "crm", "saas", "enterprise", "demo", "poc", "presales", "pre-sales"],
        "My 4 years as a Solutions Engineer at Salesforce/MuleSoft—owning enterprise demos, "
        "POCs, and Fortune 500 integrations—maps directly to the pre-sales motion here.",
    ),
    (
        ["data", "analytics", "snowflake", "dbt", "warehouse", "pipeline", "bi", "tableau",
         "databricks", "sql", "spark"],
        "As the current Data Consulting Leader at CNA architecting AI agents and predictive "
        "pricing models on Snowflake/GCP, I can accelerate customer adoption of your data stack.",
    ),
    (
        ["field", "hardware", "iot", "operations", "dispatch", "technician", "mobile workforce",
         "fsm", "field service"],
        "I built Treehouse's FSM product and API integrations that scaled field operations "
        "to $1M/month—I understand the operational complexity your customers face.",
    ),
    (
        ["startup", "seed", "series a", "early stage", "founding", "growth", "scale"],
        "As an Antler NYC EIR and serial builder, I thrive in the ambiguity of early-stage "
        "companies and know how to wear the SE/PM/Founder hat simultaneously.",
    ),
    (
        ["security", "compliance", "document", "legal", "contract", "imanage"],
        "My SE of the Year recognition at iManage—deploying document-intelligence solutions "
        "at top law firms—gives me a strong foundation for enterprise compliance use cases.",
    ),
    (
        ["integration", "api", "platform", "mulesoft", "zapier", "hubspot", "automation",
         "middleware", "webhook"],
        "With years of MuleSoft/iPaaS pre-sales and hands-on HubSpot/Zapier automation work, "
        "I speak both the business and technical sides of integration projects fluently.",
    ),
]


def generate_fit_reasons(jobs: List[Job]) -> List[Job]:
    """Populates job.fit_reason for each job. Tries Claude API first, falls back to rules."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        return _generate_with_claude(jobs, api_key)
    else:
        logger.info("ai_fitter: ANTHROPIC_API_KEY not set — using rule-based fallback")
        return _generate_rule_based(jobs)


# ── Claude path ───────────────────────────────────────────────────────────────

def _generate_with_claude(jobs: List[Job], api_key: str) -> List[Job]:
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed — pip install anthropic")
        return _generate_rule_based(jobs)

    client = anthropic.Anthropic(api_key=api_key)

    for job in jobs:
        try:
            prompt = _build_prompt(job)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=120,
                messages=[{"role": "user", "content": prompt}],
            )
            job.fit_reason = message.content[0].text.strip().strip('"')
        except Exception as exc:
            logger.warning("Claude error for %s @ %s: %s", job.title, job.company, exc)
            job.fit_reason = _rule_based_reason(job)

    return jobs


def _build_prompt(job: Job) -> str:
    desc_snippet = job.description[:600] if job.description else "(no description available)"
    funding_line = ""
    if job.funding_stage or job.funding_amount:
        funding_line = f"Company funding: {job.funding_stage} {job.funding_amount}".strip()

    return f"""You are writing a job application one-liner for Suraj Pabba.

SURAJ'S BACKGROUND:
{_RESUME_SUMMARY}

JOB:
Title: {job.title}
Company: {job.company}
Location: {job.location}
{funding_line}
Description snippet: {desc_snippet}

TASK:
Write exactly ONE sentence (first-person, ≤ 25 words) explaining why Suraj is a strong fit.
Match his most relevant experience to what this specific company does.
Be concrete — name a specific past role or achievement. Do not be generic.
Return only the sentence, no quotes, no labels."""


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _generate_rule_based(jobs: List[Job]) -> List[Job]:
    for job in jobs:
        job.fit_reason = _rule_based_reason(job)
    return jobs


def _rule_based_reason(job: Job) -> str:
    haystack = (
        f"{job.title} {job.company} {job.description}".lower()
    )
    for keywords, snippet in _RULE_BUCKETS:
        if any(kw in haystack for kw in keywords):
            return snippet
    # Default catch-all
    return (
        "With 12+ years spanning pre-sales SE, LLM product builds, and enterprise data "
        "strategy, I can deliver customer value across both technical and business dimensions."
    )
