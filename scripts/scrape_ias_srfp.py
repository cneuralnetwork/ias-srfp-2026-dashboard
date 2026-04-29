#!/usr/bin/env python3
"""Refresh IAS SRFP 2026 selected-candidate CSVs.

The public result page stores the selected subject through sessionAjax.jsp and
then renders selectedList.jsp server-side. This script replays that flow for
each subject and writes deterministic CSV/Markdown outputs for the dashboard.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://webjapps.ias.ac.in/fellowship2026/lists"
SOURCE_URL = f"{BASE_URL}/result1.jsp"

SUBJECTS = [
    ("Che", "Chemistry"),
    ("Eps", "Earth and Planetary Sciences"),
    ("Eng", "Engineering including Computer Sciences"),
    ("Lif", "Life Sciences"),
    ("Mat", "Mathematics"),
    ("Phy", "Physics"),
]

PEOPLE_FIELDS = [
    "source_url",
    "route",
    "subject_code",
    "subject",
    "last_updated",
    "serial",
    "application",
    "name",
    "affiliation",
    "category",
    "guide",
    "guide_institution",
]

SUMMARY_FIELDS = [
    "subject_code",
    "section",
    "rendered_section",
    "result",
    "selected_count",
    "last_updated",
]


@dataclass(frozen=True)
class SubjectResult:
    subject_code: str
    section: str
    rendered_section: str
    selected_count: int
    last_updated: str


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def iso_date_from_page(text: str) -> str:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
    if not match:
        return ""
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def request_text(session: requests.Session, url: str, **kwargs: object) -> str:
    response = session.request(timeout=45, url=url, **kwargs)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "ISO-8859-1"
    return response.text


def fetch_subject(code: str, section: str) -> tuple[SubjectResult, list[dict[str, str]]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "IAS-SRFP-dashboard-refresh/1.0 (+https://webjapps.ias.ac.in/fellowship2026/lists/result1.jsp)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    ajax_url = f"{BASE_URL}/sessionAjax.jsp?subject={code}"
    ajax_text = request_text(session, ajax_url, method="POST")
    if clean(ajax_text) != code:
        raise RuntimeError(f"Unexpected sessionAjax response for {code}: {clean(ajax_text)!r}")

    html = request_text(session, f"{BASE_URL}/selectedList.jsp", method="GET")
    soup = BeautifulSoup(html, "html.parser")

    h2 = soup.find("h2")
    rendered_section = clean(h2.get_text(" ", strip=True)) if h2 else section
    last_text = next((clean(value) for value in soup.find_all(string=lambda value: value and "Last Updated" in value)), "")
    last_updated = iso_date_from_page(last_text)

    people: list[dict[str, str]] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) != 5:
            continue

        serial = clean(cells[0].get_text(" ", strip=True))
        if not serial.isdigit():
            continue

        name_tag = cells[2].find("b")
        name = clean(name_tag.get_text(" ", strip=True)) if name_tag else ""

        affiliation_text = cells[2].get_text("\n", strip=True).replace("\xa0", " ")
        affiliation_parts = [clean(part) for part in affiliation_text.split("\n") if clean(part)]
        affiliation = " ".join(part for part in affiliation_parts if part != name).strip()

        guide_parts = [
            clean(part)
            for part in cells[4].get_text("\n", strip=True).replace("\xa0", " ").split("\n")
            if clean(part)
        ]

        people.append(
            {
                "source_url": SOURCE_URL,
                "route": f"sessionAjax.jsp?subject={code} -> selectedList.jsp",
                "subject_code": code,
                "subject": rendered_section,
                "last_updated": last_updated,
                "serial": serial,
                "application": clean(cells[1].get_text(" ", strip=True)),
                "name": name,
                "affiliation": affiliation,
                "category": clean(cells[3].get_text(" ", strip=True)),
                "guide": guide_parts[0] if guide_parts else "",
                "guide_institution": guide_parts[1] if len(guide_parts) > 1 else "",
            }
        )

    return (
        SubjectResult(
            subject_code=code,
            section=section,
            rendered_section=rendered_section,
            selected_count=len(people),
            last_updated=last_updated,
        ),
        people,
    )


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_route_summary(path: Path, summaries: list[SubjectResult]) -> None:
    total = sum(item.selected_count for item in summaries)
    data_version = max((item.last_updated for item in summaries if item.last_updated), default="Unknown")

    lines = [
        "# IAS SRFP 2026 Selected List Route Summary",
        "",
        f"Source page: {SOURCE_URL}",
        "",
        f"Site data version: {data_version}",
        "",
        "## Frontend Route",
        "",
        "The result page does not embed selected candidate names in the frontend HTML.",
        "It embeds counts and JavaScript subject links such as `javascript:submit('Lif')`.",
        "",
        "The click handler sends:",
        "",
        "```text",
        "POST /fellowship2026/lists/sessionAjax.jsp?subject=<subject_code>",
        "```",
        "",
        "Then the browser is redirected to:",
        "",
        "```text",
        "GET /fellowship2026/lists/selectedList.jsp",
        "```",
        "",
        "## Backend Behavior",
        "",
        "`sessionAjax.jsp` stores the selected subject in the JSP session and echoes the subject code.",
        "`selectedList.jsp` renders the selected-candidate table server-side using that session value.",
        "",
        "Conclusion: the candidate records are backend/server-rendered, not present as frontend data or a JSON route in the initial page.",
        "",
        "## Subject Results",
        "",
        "| Subject Code | Section | Route Result | Last Updated |",
        "| --- | --- | --- | --- |",
    ]

    for item in summaries:
        result = f"{item.selected_count} selected candidates" if item.selected_count else "No Record Found"
        lines.append(f"| {item.subject_code} | {item.section} | {result} | {item.last_updated or 'Unknown'} |")

    lines.extend(
        [
            "",
            f"Total selected rows found: {total}.",
            "",
            "All selected people are saved in `ias_srfp2026_selected_people.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def scrape(output_dir: Path, delay_seconds: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[SubjectResult] = []
    people: list[dict[str, str]] = []

    for index, (code, section) in enumerate(SUBJECTS):
        if index:
            time.sleep(delay_seconds)
        summary, subject_people = fetch_subject(code, section)
        summaries.append(summary)
        people.extend(subject_people)
        print(f"{code}: {summary.selected_count} rows, last_updated={summary.last_updated or 'unknown'}")

    summary_rows = [
        {
            "subject_code": item.subject_code,
            "section": item.section,
            "rendered_section": item.rendered_section,
            "result": f"{item.selected_count} selected candidates" if item.selected_count else "No Record Found",
            "selected_count": item.selected_count,
            "last_updated": item.last_updated,
        }
        for item in summaries
    ]

    write_csv(output_dir / "ias_srfp2026_selected_people.csv", PEOPLE_FIELDS, people)
    write_csv(output_dir / "ias_srfp2026_subject_results.csv", SUMMARY_FIELDS, summary_rows)
    write_route_summary(output_dir / "ias_srfp2026_route_summary.md", summaries)
    print(f"total: {len(people)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape IAS SRFP 2026 selected candidate lists.")
    parser.add_argument("--output-dir", default=".", help="Directory for generated CSV and Markdown files.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between subject requests in seconds.")
    args = parser.parse_args()

    scrape(Path(args.output_dir), args.delay)


if __name__ == "__main__":
    main()
