"""Scrape the public contribution calendar into data/contributions.json.

The endpoint is undocumented, so the page is validated first. If GitHub changes
the markup, this exits with an error and the last good data stays in place.
"""
import json
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from svg_common import ROOT, USERNAME

URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = ROOT / "data" / "contributions.json"
MIN_DAYS = 300


def parse_count(text):
    if text.startswith("No contributions"):
        return 0
    match = re.match(r"([\d,]+) contributions? on", text)
    if not match:
        raise ValueError(f"unrecognised tooltip: {text!r}")
    return int(match.group(1).replace(",", ""))


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        tip = tips.get(cell.get("id"))
        if tip is None:
            raise ValueError(f"no tooltip for {cell.get('data-date')}")
        days.append(
            {
                "date": cell["data-date"],
                "count": parse_count(tip),
                "level": int(cell["data-level"]),
            }
        )
    if len(days) < MIN_DAYS:
        raise ValueError(f"expected at least {MIN_DAYS} days, found {len(days)}")
    days.sort(key=lambda d: d["date"])

    heading = re.search(r"([\d,]+)\s+contributions?\s+in the last year", soup.get_text(" "))
    if heading:
        stated = int(heading.group(1).replace(",", ""))
        counted = sum(d["count"] for d in days)
        if stated != counted:
            print(f"warning: page says {stated}, daily counts add up to {counted}", file=sys.stderr)
    return days


def compute_stats(days):
    counts = [d["count"] for d in days]

    longest = run = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)

    # Today may simply not have any activity yet, so it doesn't break a streak.
    recent = counts[:-1] if counts[-1] == 0 else counts
    current = 0
    for count in reversed(recent):
        if not count:
            break
        current += 1

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    best = max(days, key=lambda d: (d["count"], d["date"]))
    return {
        "total": sum(counts),
        "active_days": sum(1 for c in counts if c),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main():
    response = requests.get(URL, headers={"User-Agent": "profile-readme-build"}, timeout=30)
    response.raise_for_status()
    days = parse_days(response.text)

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": compute_stats(days),
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    stats = payload["stats"]
    print(f"{len(days)} days, {stats['total']} contributions, longest streak {stats['longest_streak']}")


if __name__ == "__main__":
    main()
