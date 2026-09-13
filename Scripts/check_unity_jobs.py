#!/usr/bin/env python3
"""Fail if Unity has a NEW early-career software role in Montreal.

Reads Unity's Workday job board (the source behind unity.com/careers) through
its public JSON API, falling back to the job list embedded in the unity.com
careers page. Standard library only, so it runs on a bare GitHub runner.

Early-career = Workday job type is intern/student, or the title has an
early-career keyword. Software = the title has a software keyword. Keywords
match whole words only (so "intern" does not match "internal").

Exit codes:
    0  no new matching roles (nothing found, or all matches already seen)
    1  one or more new matching roles found
    2  could not read job data from any source
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SEEN_FILE = os.environ.get("SEEN_FILE", "seen_jobs.json")
WORKDAY_BOARD = "https://unitytech.wd1.myworkdayjobs.com/Unity"
WORKDAY_API = "https://unitytech.wd1.myworkdayjobs.com/wday/cxs/unitytech/Unity/jobs"
CAREERS_PAGE = "https://unity.com/careers/positions"
LOCATION = re.compile(r"montr[eé]al", re.I)
EARLY_CAREER_JOB_TYPE = re.compile(r"intern|student|co-?op|apprenti|stagiaire|[ée]tudiant", re.I)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 30
PAGE_SIZE = 20


def _keywords(env_name, default):
    words = [k.strip() for k in os.environ.get(env_name, default).split(",") if k.strip()]
    alternation = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return words, re.compile(rf"(?<!\w)(?:{alternation})s?(?!\w)", re.I)


EARLY_CAREER_KEYWORDS, EARLY_CAREER_RE = _keywords(
    "EARLY_CAREER_KEYWORDS",
    "early career,student,intern,internship,co-op,coop,new grad,new graduate,"
    "graduate,apprentice,campus,junior,stagiaire,stage,étudiant,étudiante,etudiant,"
    "alternance,apprenti,apprentie,débutant,débutante,jeune diplômé,diplômé,diplômée",
)
SOFTWARE_KEYWORDS, SOFTWARE_RE = _keywords(
    "SOFTWARE_KEYWORDS",
    "software,developer,software engineer,swe,programmer,programming,logiciel,"
    "informatique,développeur,développeuse,developpeur,développement,programmeur,"
    "génie logiciel,génie informatique,engineer,engineering,ingénieur,ingénieure,ingenieur",
)


def http(url, payload=None):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8")


def _job_id(*candidates):
    for text in candidates:
        match = re.search(r"JOBREQ-\d+", text or "")
        if match:
            return match.group(0)
    return next((c for c in candidates if c), "")


def _facet_ids(facets, parameter, pattern):
    ids, present = [], False
    for facet in facets:
        values = facet.get("values") or []
        if values and "facetParameter" in values[0]:
            sub_ids, sub_present = _facet_ids(values, parameter, pattern)
            ids += sub_ids
            present = present or sub_present
        elif facet.get("facetParameter") == parameter:
            present = True
            ids += [v["id"] for v in values if pattern.search(v.get("descriptor", ""))]
    return ids, present


def _workday_search(applied_facets):
    postings, total = [], None
    while total is None or len(postings) < total:
        page = json.loads(http(WORKDAY_API, {
            "appliedFacets": applied_facets,
            "limit": PAGE_SIZE,
            "offset": len(postings),
            "searchText": "",
        }))
        if total is None:
            total = page.get("total") or 0
        batch = page.get("jobPostings") or []
        if not batch:
            break
        postings += batch
    return postings


def _workday_posting_id(posting):
    return _job_id(*(posting.get("bulletFields") or []), posting.get("externalPath"), posting.get("title"))


def fetch_workday():
    facets = json.loads(http(WORKDAY_API, {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})).get("facets") or []
    location_ids, has_locations = _facet_ids(facets, "locations", LOCATION)
    if not has_locations:
        raise ValueError("response has no 'locations' facet")
    if not location_ids:
        return []

    early_ids = set()
    type_ids, _ = _facet_ids(facets, "workerSubType", EARLY_CAREER_JOB_TYPE)
    if type_ids:
        early_postings = _workday_search({"locations": location_ids, "workerSubType": type_ids})
        early_ids = {_workday_posting_id(p) for p in early_postings}

    return [
        {
            "id": _workday_posting_id(p),
            "title": p.get("title", "").strip(),
            "location": p.get("locationsText", ""),
            "url": WORKDAY_BOARD + p.get("externalPath", ""),
            "early_career_type": _workday_posting_id(p) in early_ids,
        }
        for p in _workday_search({"locations": location_ids})
    ]


def fetch_careers_page():
    html = http(CAREERS_PAGE)
    chunks = re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html)
    stream = "".join(json.loads(c) for c in chunks)
    decoder = json.JSONDecoder()
    listed, jobs = 0, {}
    for match in re.finditer(r'\{"title":', stream):
        try:
            job, _ = decoder.raw_decode(stream, match.start())
        except ValueError:
            continue
        if "externalUrl" not in job:
            continue
        listed += 1
        places = (job.get("locations") or []) + (job.get("locationKeys") or [])
        if job.get("disabled") or not any(LOCATION.search(p) for p in places):
            continue
        job_id = _job_id(job.get("id"), job.get("externalUrl"), job.get("title"))
        jobs[job_id] = {
            "id": job_id,
            "title": job.get("title", "").strip(),
            "location": ", ".join(job.get("locations") or []),
            "url": job.get("externalUrl", ""),
            "early_career_type": False,
        }
    if not listed:
        raise ValueError("no job list embedded in the page")
    return list(jobs.values())


def fetch_jobs():
    for name, fetch in (("Workday API", fetch_workday), ("unity.com careers page", fetch_careers_page)):
        try:
            jobs = fetch()
        except Exception as exc:
            print(f"::warning::{name} failed: {exc}")
            continue
        print(f"Source: {name} -- {len(jobs)} role(s) in Montreal.")
        return jobs
    return None


def is_match(job):
    early = job["early_career_type"] or EARLY_CAREER_RE.search(job["title"])
    return bool(early and SOFTWARE_RE.search(job["title"]))


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
    loc = job["location"] or "(location not listed)"
    return f"{job['title']} — {loc}"


def main():
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    jobs = fetch_jobs()
    if jobs is None:
        print("::error::Could not read Unity job data from any source.")
        return 2

    for job in jobs:
        print(f"  {job['id']:<16} {describe(job)}")
    print(f"\nEarly-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if job["id"] in seen else new_jobs).append(job)

    now = datetime.now(timezone.utc).isoformat()
    for job in new_jobs:
        seen[job["id"]] = {"title": job["title"], "location": job["location"], "first_seen": now}
    save_seen(SEEN_FILE, seen)

    summary = ["### Unity early-careers software watch (Montreal)", ""]

    if not matches:
        print("No early-career software roles in Montreal found.")
        summary.append(f"No matching roles among {len(jobs)} Montreal role(s).")
        write_summary(summary)
        return 0

    if not new_jobs:
        msg = f"{len(already_seen)} matching role(s), all previously seen -- not failing."
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
        print(f"  - {describe(job)}\n    {job['url']}")
        summary.append(f"- [{describe(job)}]({job['url']})")
    if already_seen:
        note = f"(Plus {len(already_seen)} previously-seen match(es), not counted.)"
        print(note)
        summary += ["", note]
    write_summary(summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())
