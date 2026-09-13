#!/usr/bin/env python3
"""Check Unity's public Greenhouse job board for early-career SOFTWARE roles in Montreal.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BOARD = os.environ.get("GREENHOUSE_BOARD", "unity3d")
API_URL = f"https://boards-api.greenhouse.io/v1/boards/{BOARD}/jobs?content=true"
SEEN_FILE = os.environ.get("SEEN_FILE", "seen_jobs.json")


def _keywords(env_name, default):
    return [k.strip().lower() for k in os.environ.get(env_name, default).split(",") if k.strip()]


# A role must match a keyword from EACH of these three groups to count.
LOCATION_KEYWORDS = _keywords("LOCATION_KEYWORDS", "montreal,montréal")
EARLY_CAREER_KEYWORDS = _keywords(
    "EARLY_CAREER_KEYWORDS",
    "early career,student,intern,internship,stagiaire,new grad,"
    "new graduate,graduate,apprentice,co-op,coop,campus,junior",
)
SOFTWARE_KEYWORDS = _keywords(
    "SOFTWARE_KEYWORDS",
    "software,developer,développeur,developpeur,swe,programmer,"
    "programming,software engineer,logiciel",
)


def fetch_jobs(url):
    req = urllib.request.Request(url, headers={"User-Agent": "unity-early-careers-check/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get("jobs", [])


def job_location_text(job):
    parts = []
    loc = job.get("location") or {}
    if loc.get("name"):
        parts.append(loc["name"])
    for office in job.get("offices") or []:
        if office.get("name"):
            parts.append(office["name"])
        if office.get("location"):
            parts.append(office["location"])
    return " | ".join(parts)


def job_department_text(job):
    return " | ".join(d.get("name", "") for d in (job.get("departments") or []))


def is_match(job):
    location = job_location_text(job).lower()
    # Match the early-career and software signals on title + department only (not
    # the full description), which keeps false positives down.
    role_text = f"{(job.get('title') or '').lower()} {job_department_text(job).lower()}"
    in_location = any(k in location for k in LOCATION_KEYWORDS)
    early_career = any(k in role_text for k in EARLY_CAREER_KEYWORDS)
    software = any(k in role_text for k in SOFTWARE_KEYWORDS)
    return in_location and early_career and software


def load_seen(path):
    """Return the dict of already-seen job IDs, or empty if missing/corrupt."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("seen", {})
    except (FileNotFoundError, OSError, ValueError):
        return {}


def save_seen(path, seen):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"seen": seen}, fh, indent=2, sort_keys=True, ensure_ascii=False)


def write_summary(lines):
    """Write a Markdown summary to the GitHub Actions run page, if available."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def describe(job):
    return f"{job.get('title', '(no title)')} \u2014 {job_location_text(job)}"


def main():
    print(f"Querying {API_URL}")
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    try:
        jobs = fetch_jobs(API_URL)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        # Leave the seen file untouched so we don't lose state on a transient error.
        print(f"::error::Could not query the Greenhouse API: {exc}", file=sys.stderr)
        return 2

    print(f"Fetched {len(jobs)} total published jobs.")
    print(f"Location keywords:     {LOCATION_KEYWORDS}")
    print(f"Early-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if str(job.get("id")) in seen else new_jobs).append(job)

    # Record any newly-seen matches, then persist. The workflow's cache-save step
    # runs with `if: always()`, so this is stored even when we exit non-zero.
    now = datetime.now(timezone.utc).isoformat()
    for job in new_jobs:
        seen[str(job.get("id"))] = {
            "title": job.get("title", ""),
            "location": job_location_text(job),
            "first_seen": now,
        }
    save_seen(SEEN_FILE, seen)

    summary = ["### Unity early-careers software watch (Montreal)", ""]

    if not matches:
        print("No early-career software roles in Montreal found. \u2713")
        summary.append("No matching roles found. \u2705")
        write_summary(summary)
        return 0

    if not new_jobs:
        msg = f"{len(already_seen)} matching role(s), all previously seen \u2014 not failing."
        print(msg)
        for job in already_seen:
            print(f"  (seen) {describe(job)}")
        summary.append(msg)
        write_summary(summary)
        return 0

    header = f"Found {len(new_jobs)} NEW early-career software role(s) in Montreal:"
    print(f"::warning::{header}")
    summary += [f"**{header}**", ""]
    for job in new_jobs:
        url = job.get("absolute_url", "")
        print(f"  - {describe(job)}\n    {url}")
        summary.append(f"- [{describe(job)}]({url})")
    if already_seen:
        note = f"(Plus {len(already_seen)} previously-seen match(es), not counted.)"
        print(note)
        summary += ["", note]
    write_summary(summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())
