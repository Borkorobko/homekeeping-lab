from __future__ import annotations

import re
from urllib.parse import urlparse

from common import load_config, load_plan

rows = load_plan()
config = load_config()
errors: list[str] = []

ids = [int(row["ID"]) for row in rows]
if len(ids) != len(set(ids)):
    errors.append("duplicate article IDs")

slugs = [row["Slug"].strip() for row in rows]
if len(slugs) != len(set(slugs)):
    errors.append("duplicate slugs")

known_ids = set(ids)
known_categories = {item["name"]: item["slug"] for item in config["categories"]}

for row in rows:
    rid = row["ID"]
    slug = row["Slug"].strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append(f"ID {rid}: invalid slug {slug!r}")
    if row["Category"] not in known_categories:
        errors.append(f"ID {rid}: unknown category {row['Category']!r}")
    expected_hub = f"/{known_categories.get(row['Category'], '')}/"
    if row["ParentHub"] != expected_hub:
        errors.append(f"ID {rid}: ParentHub {row['ParentHub']!r} should be {expected_hub!r}")
    try:
        priority = int(row["Priority"])
        risk = int(row["RiskLevel"])
        if priority < 1:
            errors.append(f"ID {rid}: Priority must be >= 1")
        if risk not in {0, 1, 2, 3}:
            errors.append(f"ID {rid}: RiskLevel must be 0-3")
    except ValueError:
        errors.append(f"ID {rid}: Priority/RiskLevel must be integers")
    related = [int(x) for x in row["RelatedIDs"].split("|") if x.strip()]
    if int(rid) in related:
        errors.append(f"ID {rid}: article links to itself")
    for related_id in related:
        if related_id not in known_ids:
            errors.append(f"ID {rid}: unknown RelatedID {related_id}")
    if len(related) > config["seo"]["max_related_articles"]:
        errors.append(f"ID {rid}: too many RelatedIDs")

parsed = urlparse(config["domain"])
if parsed.scheme != "https" or not parsed.netloc:
    errors.append("config domain must be an absolute https URL")

if errors:
    print("Content plan validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(f"Content plan OK: {len(rows)} articles, {len(known_categories)} categories.")
