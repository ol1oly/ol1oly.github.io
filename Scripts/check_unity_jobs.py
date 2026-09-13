#!/usr/bin/env python3
"""Check Unity's Greenhouse job board for early-career SOFTWARE roles in Montreal.

Exit codes (GitHub treats any non-zero as a failed run):
    0  no NEW matching roles (nothing found, or all matches already seen) -> passes
    1  one or more NEW matching roles                                     -> fails (alert)
    2  could not fetch/parse the board                                    -> fails (broken check)

Everything is configurable via environment variables.
"""

import html
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

BOARD = os.environ.get("GREENHOUSE_BOARD", "unity3d")
# Greenhouse's edge serves a 404 to requests that don't look like a browser, and
# the embed is mirrored on two hosts. Try each in turn with browser-like headers.
EMBED_URLS = [
    u.strip()
    for u in os.environ.get(
        "GREENHOUSE_EMBED_URLS",
        f"https://job-boards.greenhouse.io/embed/job_board?for={BOARD},"
        f"https://boards.greenhouse.io/embed/job_board?for={BOARD}",
    ).split(",")
    if u.strip()
]
EMBED_HOST = "https://job-boards.greenhouse.io"
SEEN_FILE = os.environ.get("SEEN_FILE", "seen_jobs.json")

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://unity.com/careers",
}


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


class _BoardParser(HTMLParser):
    """Pull (id, title, location, department) out of the Greenhouse embed HTML.

    Markup-agnostic: a job is any <a href=".../jobs/{id}">. Its location is taken
    to be the text that follows the link up to the next link or section heading,
    so it doesn't depend on Greenhouse's CSS class names. Section <h1>-<h6>
    headings set the current department.
    """

    _HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")

    def __init__(self):
        super().__init__()
        self.jobs = []
        self._dept = ""
        self._mode = None          # None | "heading" | "title"
        self._buf = []
        self._href = None
        self._cap_loc = False      # capturing the text that follows a job link
        self._loc_buf = []

    def _finalize_location(self):
        if self._cap_loc:
            loc = html.unescape(" ".join("".join(self._loc_buf).split())).strip()
            if loc and self.jobs and not self.jobs[-1]["location"]:
                self.jobs[-1]["location"] = loc
            self._cap_loc, self._loc_buf = False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        is_heading = tag in self._HEADINGS
        is_job = tag == "a" and a.get("href") and re.search(r"/jobs/\d+", a["href"])
        if is_heading or is_job:
            self._finalize_location()   # a link/heading ends the previous job's location
        if is_heading:
            self._mode, self._buf = "heading", []
        elif is_job:
            self._mode, self._buf, self._href = "title", [], a["href"]

    def handle_data(self, data):
        if self._mode in ("heading", "title"):
            self._buf.append(data)
        elif self._cap_loc:
            self._loc_buf.append(data)

    def handle_endtag(self, tag):
        if self._mode == "heading" and tag in self._HEADINGS:
            text = html.unescape(" ".join("".join(self._buf).split())).strip()
            if text and text.lower() not in ("job", "jobs", "openings"):
                self._dept = text
            self._mode = None
        elif self._mode == "title" and tag == "a":
            title = html.unescape(" ".join("".join(self._buf).split())).strip()
            title = re.sub(r"\s*New$", "", title)  # strip the "New" badge
            job_id = re.search(r"/jobs/(\d+)", self._href)
            href = self._href if self._href.startswith("http") else EMBED_HOST + self._href
            if title:
                self.jobs.append(
                    {
                        "id": job_id.group(1) if job_id else href,
                        "title": title,
                        "absolute_url": href,
                        "location": "",
                        "department": self._dept,
                    }
                )
            self._mode = None
            self._cap_loc, self._loc_buf = True, []   # start capturing location text

    def close(self):
        super().close()
        self._finalize_location()


def _fetch_one(url):
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    parser = _BoardParser()
    parser.feed(body)
    parser.close()
    return parser.jobs


def fetch_jobs(urls):
    """Return jobs from the first embed URL that yields any; else raise."""
    errors = []
    for url in urls:
        try:
            jobs = _fetch_one(url)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            errors.append(f"{url} -> {exc}")
            continue
        if jobs:
            print(f"Parsed {len(jobs)} jobs from {url}")
            return jobs
        # A 200 with zero parsed jobs almost certainly means the markup changed.
        errors.append(f"{url} -> 200 but parsed 0 jobs (markup may have changed)")
    raise RuntimeError("Could not fetch a usable board. Tried:\n  " + "\n  ".join(errors))


def is_match(job):
    location = job["location"].lower()
    role_text = f"{job['title'].lower()} {job['department'].lower()}"
    in_location = any(k in location for k in LOCATION_KEYWORDS)
    early_career = any(k in role_text for k in EARLY_CAREER_KEYWORDS)
    software = any(k in role_text for k in SOFTWARE_KEYWORDS)
    return in_location and early_career and software


def load_seen(path):
    import json
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("seen", {})
    except (FileNotFoundError, OSError, ValueError):
        return {}


def save_seen(path, seen):
    import json
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"seen": seen}, fh, indent=2, sort_keys=True, ensure_ascii=False)


def write_summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def describe(job):
    loc = job["location"] or "(no location listed)"
    return f"{job['title']} \u2014 {loc}"


def main():
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    try:
        jobs = fetch_jobs(EMBED_URLS)
    except RuntimeError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    print(f"Location keywords:     {LOCATION_KEYWORDS}")
    print(f"Early-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if str(job["id"]) in seen else new_jobs).append(job)

    now = datetime.now(timezone.utc).isoformat()
    for job in new_jobs:
        seen[str(job["id"])] = {
            "title": job["title"],
            "location": job["location"],
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
        print(f"  - {describe(job)}\n    {job['absolute_url']}")
        summary.append(f"- [{describe(job)}]({job['absolute_url']})")
    if already_seen:
        note = f"(Plus {len(already_seen)} previously-seen match(es), not counted.)"
        print(note)
        summary += ["", note]
    write_summary(summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())
