#!/usr/bin/env python3
"""Fail if Unity's careers site has a NEW early-career software role in Montreal.

Unity disabled the public Greenhouse API and embed, so this loads Unity's own
Montreal-filtered careers page in a headless browser, captures the JSON the page
fetches to render its jobs, and flags new roles whose title is early-career and
software. Captured JSON endpoints are logged for diagnosis.

Exit codes:
    0  no new matching roles (nothing found, or all matches already seen)
    1  one or more new matching roles found
    2  could not locate/read job data on the careers site
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
NAV_TIMEOUT = int(os.environ.get("NAV_TIMEOUT_MS", "45000"))
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TITLE_KEYS = {"title", "name", "jobtitle", "job_title", "text", "label", "posting_title"}
LOC_KEYS = {"location", "office", "city", "region", "workplace", "locations", "offices", "location_name"}
ID_KEYS = {"id", "jobid", "job_id", "gh_id", "greenhouse_id", "requisition_id", "requisitionid", "slug", "ref", "internal_job_id"}
URL_KEYS = {"absolute_url", "absoluteurl", "url", "apply_url", "applyurl", "href", "link", "permalink", "canonical_url"}
JOBISH = re.compile(r"job|position|opening|posting|listing|role|vacanc|result|hit|node|edge|item|entry|card|opportunit", re.I)


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


def _first_str(d, keys):
    for k, v in d.items():
        if k.lower() in keys and isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _loc_str(d):
    for k, v in d.items():
        if k.lower() in LOC_KEYS:
            if isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, dict):
                n = _first_str(v, {"name", "title", "label", "text"})
                if n:
                    return n
            if isinstance(v, list):
                parts = []
                for it in v:
                    if isinstance(it, str):
                        parts.append(it)
                    elif isinstance(it, dict):
                        parts.append(_first_str(it, {"name", "title", "label", "text"}))
                joined = ", ".join(p for p in parts if p)
                if joined:
                    return joined
    return ""


def _mk_job(d):
    title = _first_str(d, TITLE_KEYS)
    if not title:
        return None
    loc = _loc_str(d)
    url = _first_str(d, URL_KEYS)
    jid = _first_str(d, ID_KEYS)
    if not (loc or url or jid):
        return None
    if url and not url.startswith("http"):
        url = "https://unity.com" + url if url.startswith("/") else ""
    if not url:
        for k, v in d.items():
            kl = k.lower()
            if isinstance(v, str) and (v.startswith("/") or v.startswith("http")) and any(
                h in kl for h in ("slug", "url", "href", "link", "path", "permalink")
            ):
                url = v if v.startswith("http") else "https://unity.com" + v
                break
    return {"id": jid or url or title, "title": title, "location": loc, "absolute_url": url}


def _harvest(node):
    found, jobs = False, []
    if isinstance(node, dict):
        for k, v in node.items():
            f, j = _harvest(v)
            if j and isinstance(v, list) and JOBISH.search(k):
                found = True
            found = found or f
            jobs.extend(j)
        m = _mk_job(node)
        if m:
            jobs.append(m)
    elif isinstance(node, list):
        for it in node:
            f, j = _harvest(it)
            found = found or f
            jobs.extend(j)
    return found, jobs


def _dedupe(jobs):
    uniq = {}
    for j in jobs:
        uniq.setdefault((j["title"], j["absolute_url"]), j)
    return list(uniq.values())


def render_jobs(url):
    from playwright.sync_api import sync_playwright

    payloads = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(user_agent=USER_AGENT, locale="en-US")

        def on_response(resp):
            try:
                if "json" in (resp.headers or {}).get("content-type", "").lower():
                    payloads.append((resp.url, resp.json()))
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT)
        page.wait_for_timeout(2500)
        browser.close()

    print(f"Captured {len(payloads)} JSON response(s):")
    for u, _ in payloads[:25]:
        print(f"  - {u}")

    found, jobs = False, []
    for _, data in payloads:
        f, j = _harvest(data)
        found = found or f
        jobs.extend(j)
    return _dedupe(jobs), found


def is_match(job):
    t = job["title"].lower()
    return any(k in t for k in EARLY_CAREER_KEYWORDS) and any(k in t for k in SOFTWARE_KEYWORDS)


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
    return f"{job['title']} \u2014 {loc}"


def main():
    seen = load_seen(SEEN_FILE)
    print(f"Loaded {len(seen)} previously-seen job ID(s) from {SEEN_FILE}.")

    try:
        jobs, found_container = render_jobs(MATCH_URL)
    except Exception as exc:
        print(f"::error::Could not render {MATCH_URL}: {exc}", file=sys.stderr)
        return 2

    print(f"Extracted {len(jobs)} roles from {MATCH_URL} (jobs container found: {found_container})\n")
    if not found_container:
        print("::error::No jobs container found in any captured JSON. Inspect the endpoints logged above.", file=sys.stderr)
        return 2

    print(f"Early-career keywords: {EARLY_CAREER_KEYWORDS}")
    print(f"Software keywords:     {SOFTWARE_KEYWORDS}\n")

    matches = [j for j in jobs if is_match(j)]
    new_jobs, already_seen = [], []
    for job in matches:
        (already_seen if str(job["id"]) in seen else new_jobs).append(job)

    now = datetime.now(timezone.utc).isoformat()
    for job in new_jobs:
        seen[str(job["id"])] = {"title": job["title"], "location": job["location"], "first_seen": now}
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