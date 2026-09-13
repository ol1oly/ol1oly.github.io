#!/usr/bin/env python3
"""Check Unity's public Greenhouse job board for early-career SOFTWARE roles in Montreal.

Exit codes (GitHub treats any non-zero as a failed run):
    0  no NEW matching roles (nothing found, or all matches already seen) -> passes
    1  one or more NEW matching roles                                     -> fails (alert)
    2  no Greenhouse host returned a job list                             -> fails (broken check)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BOARD = os.environ.get("GREENHOUSE_BOARD", "unity3d")
SEEN_FILE = os.environ.get("SEEN_FILE", "seen_jobs.json")

# Greenhouse serves the public job-board API from several hosts. Tried in order;
# the first that returns a JSON body with a "jobs" key wins.
API_HOSTS = [
    h.strip().rstrip("/")
    for h in os.environ.get(
        "GREENHOUSE_API_HOSTS",
        "https://boards-api.greenhouse.io,"
        "https://api.greenhouse.io,"
        "https://job-boards.greenhouse.io,"
        "https://boards-api.eu.greenhouse.io",
    ).split(",")
    if h.strip()
]


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

# Metadata fields whose NAME contains one of these are treated as location info
# (covers boards that keep "Remote/Hybrid" in location.name and the city here).
LOCATION_META_HINTS = ("location", "office", "city", "region", "country", "site", "place")

USER_AGENT = "unity-early-careers-check/3.0"


def fetch_jobs(board):
    """Return the list of jobs from the first Greenhouse host that serves them."""
    errors = []
    for host in API_HOSTS:
        url = f"{host}/v1/boards/{board}/jobs?content=true"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            errors.append(f"{url} -> HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            errors.append(f"{url} -> {exc}")
            continue
        jobs = data.get("jobs")
        if jobs is not None:
            print(f"Using {url}  ({len(jobs)} jobs)")
            return jobs
        errors.append(f"{url} -> 200 but no 'jobs' key")
    raise RuntimeError("No Greenhouse host returned a job list. Tried:\n  " + "\n  ".join(errors))


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
    for meta in job.get("metadata") or []:
        if any(hint in (meta.get("name") or "").lower() for hint in LOCATION_META_HINTS):
            value = meta.get("value")
            if isinstance(value, list):
                parts.append(", ".join(str(v) for v in value))
            elif value:
                parts.append(str(value))
    return " | ".join(parts)


def job_department_text(job):
    return " | ".join(d.get("name", "") for d in (job.get("departments") or []))


def is_match(job):
    location = job_location_text(job).lower()
    # Match early-career and software signals on title + department only (not the
    # full description), which keeps false positives down.
    role_text = f"{(job.get('title') or '').lower()} {job_department_text(job).lower()}"
    in_location = any(k in location for k in LOCATION_KEYWORDS)
    early_career = any(k in role_text for k in EARLY_CAREER_KEYWORDS)
    software = any(k in role_text for k in SOFTWARE_KEYWORDS)
    return in_location and early_career and software


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


def describe(job):
    return f"{job.get('title', '(no title)')} \u2014 {job_location_text(job)}"


def main():
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    try:
        jobs = fetch_jobs(BOARD)
    except RuntimeError as exc:
        # Leave the seen file untouched so we don't lose state on a transient error.
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    print(f"Location keywords:     {LOCATION_KEYWORDS}")
    print(f"Early-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if str(job.get("id")) in seen else new_jobs).append(job)

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
