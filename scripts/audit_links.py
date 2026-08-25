from __future__ import annotations

import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
PLAN_PATH = ROOT / "content_plan.csv"
CONFIG_PATH = ROOT / "config" / "site.json"


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value.strip())


def read_plan() -> list[dict[str, str]]:
    with PLAN_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def expected_file(href: str) -> Path | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None
    path = parts.path
    if not path or path.startswith("#"):
        return None
    if not path.startswith("/"):
        return None

    relative = path.lstrip("/")
    if not relative:
        return SITE_DIR / "index.html"
    if path.endswith("/"):
        return SITE_DIR / relative / "index.html"

    direct = SITE_DIR / relative
    if direct.exists():
        return direct
    return SITE_DIR / relative / "index.html"


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    rows = read_plan()
    by_id = {int(row["ID"]): row for row in rows}
    category_hubs = {item["name"]: f"/{item['slug']}/" for item in config["categories"]}
    published = {
        int(row["ID"]): row
        for row in rows
        if row["Status"] in {"SafetyPassed", "Published"}
    }

    problems: list[str] = []

    # Validate editorial link relationships in the content plan.
    for row in rows:
        rid = int(row["ID"])
        expected_hub = category_hubs.get(row["Category"])
        if expected_hub is None:
            problems.append(f"article {rid}: unknown category {row['Category']!r}")
        elif row["ParentHub"] != expected_hub:
            problems.append(
                f"article {rid}: ParentHub {row['ParentHub']!r} should be {expected_hub!r}"
            )

        related_raw = [item.strip() for item in row["RelatedIDs"].split("|") if item.strip()]
        related_ids: list[int] = []
        for item in related_raw:
            try:
                related_ids.append(int(item))
            except ValueError:
                problems.append(f"article {rid}: invalid RelatedID {item!r}")
        if rid in related_ids:
            problems.append(f"article {rid}: self-reference in RelatedIDs")
        if len(related_ids) != len(set(related_ids)):
            problems.append(f"article {rid}: duplicate RelatedIDs")
        for related_id in related_ids:
            if related_id not in by_id:
                problems.append(f"article {rid}: RelatedID {related_id} does not exist")

    # Crawl every generated HTML page for broken root-relative links.
    for html_path in SITE_DIR.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        parser = AnchorParser()
        parser.feed(text)
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
                continue
            target = expected_file(href)
            if target is not None and not target.exists():
                problems.append(
                    f"broken internal link in {html_path.relative_to(SITE_DIR)}: {href}"
                )

    # Every published article must link to its hub, use the right breadcrumbs,
    # and surface any related guide that is already published.
    for rid, row in published.items():
        article_path = SITE_DIR / "guides" / row["Slug"] / "index.html"
        if not article_path.exists():
            problems.append(f"published article {rid}: generated page is missing")
            continue

        text = article_path.read_text(encoding="utf-8")
        hub = row["ParentHub"]
        expected_breadcrumb = f'<a href="{hub}">{row["Category"]}</a>'
        if 'class="breadcrumbs"' not in text:
            problems.append(f"published article {rid}: breadcrumb navigation missing")
        if '<a href="/">Home</a>' not in text:
            problems.append(f"published article {rid}: Home breadcrumb missing")
        if expected_breadcrumb not in text:
            problems.append(f"published article {rid}: category breadcrumb is wrong or missing")

        hub_file = SITE_DIR / hub.strip("/") / "index.html"
        if not hub_file.exists():
            problems.append(f"published article {rid}: category hub page missing: {hub}")
        else:
            hub_text = hub_file.read_text(encoding="utf-8")
            article_href = f'/guides/{row["Slug"]}/'
            if article_href not in hub_text:
                problems.append(f"published article {rid}: category hub does not link back to article")

        related_ids = [int(x) for x in row["RelatedIDs"].split("|") if x.strip()]
        published_related = [by_id[x] for x in related_ids if x in published]
        max_related = int(config["seo"].get("max_related_articles", 4))
        for related in published_related[:max_related]:
            href = f'/guides/{related["Slug"]}/'
            if href not in text:
                problems.append(
                    f"published article {rid}: expected related link missing: {related['ID']}"
                )

    if problems:
        print("Internal-link/breadcrumb audit FAILED:")
        for problem in problems:
            print(f" - {problem}")
        raise SystemExit(1)

    print(
        f"Internal-link/breadcrumb audit PASS: {len(published)} published guides, "
        f"{len(list(SITE_DIR.rglob('*.html')))} HTML pages checked."
    )


if __name__ == "__main__":
    main()
