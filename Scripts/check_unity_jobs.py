#!/usr/bin/env python3
"""Fail if Unity's careers site has a NEW early-career software role in Montreal.

Unity disabled the public Greenhouse API and embed, so this renders Unity's own
Montreal-filtered careers page with a headless browser and flags new roles whose
title is both early-career and software.

Exit codes:
    0  no new matching roles (nothing found, or all matches already seen)
    1  one or more new matching roles found
    2  could not render or read the careers site
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

SEEN_FILE = os.environ.get("SEEN_FILE", "seen_jobs.json")
MATCH_URL = os.environ.get(
    "MATCH_URL", "https://unity.com/careers/positions?location=can-montreal"
)
JOB_SELECTOR = os.environ.get("JOB_SELECTOR", 'a[href*="/position"], a[href*="/jobs/"]')
NAV_TIMEOUT = int(os.environ.get("NAV_TIMEOUT_MS", "45000"))
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _keywords(env_name, default):
    return [k.strip().lower() for k in os.environ.get(env_name, default).split(",") if k.strip()]


EARLY_CAREER_KEYWORDS = _keywords(
    "EARLY_CAREER_KEYWORDS",
    "early career,student,intern,internship,stagiaire,stage,new grad,new graduate,"
    "graduate,apprentice,apprenti,co-op,coop,campus,junior,étudiant,etudiant,"
    "alternance,débutant,jeune diplômé,diplômé",
)
SOFTWARE_KEYWORDS = _keywords(
    "SOFTWARE_KEYWORDS",
    "software,developer,software engineer,swe,programmer,programming,logiciel,"
    "informatique,développeur,développeuse,developpeur,développement,programmeur,"
    "génie logiciel,génie informatique",
)


def render_jobs(url):
    from playwright.sync_api import sync_playwright

    jobs, seen_keys = [], set()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(user_agent=USER_AGENT, locale="en-US")
        page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT)
        try:
            page.wait_for_selector(JOB_SELECTOR, timeout=10000)
        except Exception:
            pass
        for el in page.query_selector_all(JOB_SELECTOR):
            title = (el.inner_text() or "").strip()
            href = el.get_attribute("href") or ""
            if not title:
                continue
            key = href or title
            if key in seen_keys:
                continue
            seen_keys.add(key)
            job_id = re.search(r"(\d{5,})", href)
            jobs.append(
                {
                    "id": job_id.group(1) if job_id else (href or title),
                    "title": title,
                    "absolute_url": href if href.startswith("http") else "https://unity.com" + href,
                }
            )
        browser.close()
    return jobs


def is_match(job):
    t = job["title"].lower()
    early = any(k in t for k in EARLY_CAREER_KEYWORDS)
    software = any(k in t for k in SOFTWARE_KEYWORDS)
    return early and software


def load_seen(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("seen", {})
    except (FileNotFoundError, OSError, ValueError):
        return {}


def save_seen(path, seen):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"seen": seen}, fh, indent=2, sort_keys=True, ensure_ascii=False)


def write_summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    try:
        jobs = render_jobs(MATCH_URL)
    except Exception as exc:
        print(f"::error::Could not render {MATCH_URL}: {exc}", file=sys.stderr)
        return 2

    print(f"Rendered {len(jobs)} Montreal roles from {MATCH_URL}")
    if not jobs:
        print(f"::error::Rendered 0 roles -- selector '{JOB_SELECTOR}' may be wrong.", file=sys.stderr)
        return 2

    print(f"Early-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if str(job["id"]) in seen else new_jobs).append(job)

    now = datetime.now(timezone.utc).isoformat()
    for job in new_jobs:
        seen[str(job["id"])] = {"title": job["title"], "first_seen": now}
    save_seen(SEEN_FILE, seen)

    summary = ["### Unity early-careers software watch (Montreal)", ""]

    if not matches:
        print("No early-career software roles in Montreal found.")
        summary.append("No matching roles found.")
        write_summary(summary)
        return 0

    if not new_jobs:
        msg = f"{len(already_seen)} matching role(s), all previously seen -- not failing."
        print(msg)
        for job in already_seen:
            print(f"  (seen) {job['title']}")
        summary.append(msg)
        write_summary(summary)
        return 0

    header = f"Found {len(new_jobs)} NEW early-career software role(s) in Montreal:"
    print(f"::warning::{header}")
    summary += [f"**{header}**", ""]
    for job in new_jobs:
        print(f"  - {job['title']}\n    {job['absolute_url']}")
        summary.append(f"- [{job['title']}]({job['absolute_url']})")
    if already_seen:
        note = f"(Plus {len(already_seen)} previously-seen match(es), not counted.)"
        print(note)
        summary += ["", note]
    write_summary(summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())