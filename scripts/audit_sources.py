from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlparse

from common import SOURCES_DIR, load_plan, normalize_source_required

rows = load_plan()
errors: list[str] = []
required_ids: set[int] = set()
known_ids = {int(row["ID"]) for row in rows}

for row in rows:
    article_id = int(row["ID"])
    risk = int(row["RiskLevel"])
    required = normalize_source_required(row["SourceRequired"]) or risk >= 1
    if not required:
        continue

    required_ids.add(article_id)
    path = SOURCES_DIR / f"{article_id}.json"
    if not path.exists():
        errors.append(f"ID {article_id}: required source packet is missing")
        continue

    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"ID {article_id}: source packet is not valid JSON ({exc})")
        continue

    if packet.get("article_id") != article_id:
        errors.append(f"ID {article_id}: packet article_id does not match content plan")

    topic = str(packet.get("topic", "")).strip()
    if topic and topic != row["Title"].strip():
        errors.append(f"ID {article_id}: packet topic does not match article title")

    verified_at = str(packet.get("verified_at", "")).strip()
    if not verified_at:
        errors.append(f"ID {article_id}: verified_at is missing")
    else:
        try:
            date.fromisoformat(verified_at)
        except ValueError:
            errors.append(f"ID {article_id}: verified_at must be YYYY-MM-DD")

    if not str(packet.get("notes", "")).strip():
        errors.append(f"ID {article_id}: packet notes are missing")

    sources = packet.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"ID {article_id}: packet has no sources")
        continue

    seen_urls: set[str] = set()
    for index, source in enumerate(sources, start=1):
        prefix = f"ID {article_id} source {index}"
        if not isinstance(source, dict):
            errors.append(f"{prefix}: source entry must be an object")
            continue

        title = str(source.get("title", "")).strip()
        authority = str(source.get("authority", "")).strip()
        url = str(source.get("url", "")).strip()
        if not title:
            errors.append(f"{prefix}: title is missing")
        if not authority:
            errors.append(f"{prefix}: authority is missing")
        if not url:
            errors.append(f"{prefix}: URL is missing")
            continue

        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{prefix}: URL must be an absolute HTTPS URL")
        if url in seen_urls:
            errors.append(f"{prefix}: duplicate URL in packet")
        seen_urls.add(url)

    if risk == 2 and packet.get("approved_for_auto_publish") is not True:
        errors.append(
            f"ID {article_id}: RiskLevel 2 requires approved_for_auto_publish=true"
        )

# Numeric JSON packets should correspond to a real article. README and other
# documentation files are intentionally ignored.
for path in SOURCES_DIR.glob("*.json"):
    try:
        packet_id = int(path.stem)
    except ValueError:
        continue
    if packet_id not in known_ids:
        errors.append(f"{path.name}: source packet has no matching article ID")

if errors:
    print("Source coverage audit failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    f"Source coverage PASS: {len(required_ids)} source-required/risk-sensitive "
    f"articles have structurally valid packets."
)
