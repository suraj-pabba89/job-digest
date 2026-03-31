"""
email_template/template.py — Renders the daily digest as a clean HTML email.
Uses Roboto font (Google Fonts), one card per job, apply button per job.
"""
from __future__ import annotations

import html
from datetime import date
from typing import List

from scrapers.base import Job
from config import TO_EMAIL


def render_email(jobs: List[Job]) -> str:
    """Returns a complete HTML email string."""
    today = date.today().strftime("%B %d, %Y")
    job_cards = "\n".join(_job_card(j) for j in jobs)
    count = len(jobs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>FDE Job Digest — {today}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Roboto', Arial, sans-serif;
      background: #f4f6f9;
      color: #1a1a2e;
      line-height: 1.6;
    }}
    .wrapper {{
      max-width: 680px;
      margin: 32px auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,0,0,0.10);
    }}

    /* ── Header ── */
    .header {{
      background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
      padding: 36px 40px 28px;
      text-align: center;
    }}
    .header h1 {{
      color: #e94560;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }}
    .header p {{
      color: #a8b2d8;
      font-size: 13px;
      margin-top: 6px;
    }}
    .header .badge {{
      display: inline-block;
      background: #e94560;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      border-radius: 20px;
      padding: 3px 12px;
      margin-top: 10px;
      letter-spacing: 0.3px;
    }}

    /* ── Job cards ── */
    .jobs {{
      padding: 24px 32px;
    }}
    .job-card {{
      background: #f8faff;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #e94560;
      border-radius: 8px;
      padding: 20px 22px;
      margin-bottom: 18px;
      transition: box-shadow 0.2s;
    }}
    .job-card:last-child {{ margin-bottom: 0; }}

    .job-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .company-name {{
      font-size: 18px;
      font-weight: 700;
      color: #0f3460;
    }}
    .funding-badge {{
      background: #e8f4fd;
      color: #2980b9;
      font-size: 11px;
      font-weight: 500;
      border-radius: 12px;
      padding: 3px 10px;
      white-space: nowrap;
    }}

    .job-title {{
      font-size: 15px;
      font-weight: 500;
      color: #2d3748;
      margin-top: 4px;
    }}
    .job-meta {{
      font-size: 12px;
      color: #718096;
      margin-top: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .job-meta span::before {{
      margin-right: 4px;
    }}
    .location::before {{ content: "📍"; }}
    .source::before  {{ content: "🔍"; }}

    .fit-reason {{
      font-style: italic;
      color: #4a5568;
      font-size: 13px;
      margin-top: 12px;
      padding: 10px 14px;
      background: #fffbf0;
      border-left: 3px solid #f6ad55;
      border-radius: 0 6px 6px 0;
    }}
    .fit-label {{
      font-style: normal;
      font-weight: 700;
      font-size: 11px;
      text-transform: uppercase;
      color: #d69e2e;
      letter-spacing: 0.5px;
      display: block;
      margin-bottom: 4px;
    }}

    .apply-btn {{
      display: inline-block;
      margin-top: 14px;
      background: #e94560;
      color: #ffffff !important;
      text-decoration: none;
      font-weight: 600;
      font-size: 13px;
      padding: 8px 22px;
      border-radius: 6px;
      letter-spacing: 0.3px;
    }}
    .apply-btn:hover {{ background: #c53030; }}

    /* ── Footer ── */
    .footer {{
      background: #f0f4f8;
      padding: 20px 32px;
      text-align: center;
      font-size: 11px;
      color: #a0aec0;
      border-top: 1px solid #e2e8f0;
    }}
    .footer a {{ color: #718096; text-decoration: underline; }}

    /* ── Empty state ── */
    .empty {{
      text-align: center;
      padding: 48px 32px;
      color: #718096;
    }}
    .empty .emoji {{ font-size: 48px; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <!-- Header -->
    <div class="header">
      <h1>Forward Deployed Engineer<br>Job Digest</h1>
      <p>{today}</p>
      <span class="badge">{count} new role{"s" if count != 1 else ""} found today</span>
    </div>

    <!-- Job cards -->
    <div class="jobs">
      {"".join([job_cards]) if jobs else _empty_state()}
    </div>

    <!-- Footer -->
    <div class="footer">
      <p>Sent daily to <strong>{TO_EMAIL}</strong> &middot;
         Sources: LinkedIn · Greenhouse · Lever · Ashby · Indeed · Wellfound · Adzuna</p>
      <p style="margin-top:6px;">
        To stop receiving these, disable the cron job:
        <code>crontab -e</code>
      </p>
    </div>
  </div>
</body>
</html>"""


def _job_card(job: Job) -> str:
    """Renders a single job card as an HTML string."""
    company = html.escape(job.company)
    title = html.escape(job.title)
    location = html.escape(job.location)
    source = html.escape(job.source)
    url = html.escape(job.url or "#")
    fit = html.escape(job.fit_reason) if job.fit_reason else ""

    funding_parts = []
    if job.funding_stage:
        funding_parts.append(html.escape(job.funding_stage))
    if job.funding_amount:
        funding_parts.append(html.escape(job.funding_amount))
    funding_text = " · ".join(funding_parts)

    funding_badge = (
        f'<span class="funding-badge">{funding_text}</span>' if funding_text else ""
    )

    fit_block = ""
    if fit:
        fit_block = f"""
      <div class="fit-reason">
        <span class="fit-label">Why I'd fit</span>
        {fit}
      </div>"""

    apply_button = (
        f'<a href="{url}" class="apply-btn" target="_blank">Apply Now →</a>'
        if url and url != "#"
        else ""
    )

    return f"""
    <div class="job-card">
      <div class="job-header">
        <span class="company-name">{company}</span>
        {funding_badge}
      </div>
      <div class="job-title">{title}</div>
      <div class="job-meta">
        <span class="location">{location}</span>
        <span class="source">{source}</span>
      </div>
      {fit_block}
      {apply_button}
    </div>"""


def _empty_state() -> str:
    return """
    <div class="empty">
      <div class="emoji">🔍</div>
      <p style="margin-top:16px;font-weight:500;">No new Forward Deployed Engineer roles found today.</p>
      <p style="margin-top:8px;font-size:13px;">Check back tomorrow — the digest runs every morning at 7 AM.</p>
    </div>"""
