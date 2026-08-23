from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "content_plan.csv"
CONFIG_PATH = ROOT / "config" / "site.json"
ARTICLES_DIR = ROOT / "content" / "articles"
QA_DIR = ROOT / "qa"
SOURCES_DIR = ROOT / "sources"
SITE_DIR = ROOT / "site"

ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_plan() -> list[dict[str, str]]:
    with PLAN_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def save_plan(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError("content_plan.csv cannot be empty")
    fieldnames = list(rows[0].keys())
    with PLAN_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plan_by_id(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    return {int(row["ID"]): row for row in rows}


def article_path(row: dict[str, str]) -> Path:
    return ARTICLES_DIR / f'{row["Slug"]}.json'


def qa_path(row: dict[str, str]) -> Path:
    return QA_DIR / f'{row["Slug"]}.json'


def source_path(row: dict[str, str]) -> Path:
    return SOURCES_DIR / f'{row["ID"]}.json'


def load_source_packet(row: dict[str, str]) -> dict[str, Any] | None:
    path = source_path(row)
    if not path.exists():
        return None
    packet = json.loads(path.read_text(encoding="utf-8"))
    sources = packet.get("sources", [])
    if not isinstance(sources, list) or not sources:
        return None
    return packet


def normalize_source_required(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "1"}


def article_text(article: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "summary", "quick_answer"):
        value = article.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("items_needed", "steps", "mistakes", "safety_notes"):
        value = article.get(key, [])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))
    for section in article.get("sections", []):
        if isinstance(section, dict):
            parts.extend(str(v) for v in section.values() if isinstance(v, str))
            bullets = section.get("bullets", [])
            if isinstance(bullets, list):
                parts.extend(str(v) for v in bullets)
    for item in article.get("faq", []):
        if isinstance(item, dict):
            parts.extend(str(v) for v in item.values() if isinstance(v, str))
    return "\n".join(parts)
