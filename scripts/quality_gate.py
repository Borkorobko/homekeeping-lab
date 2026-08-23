from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from common import article_path, article_text, load_plan, load_source_packet, qa_path, save_plan

MIN_WORDS = 650
MAX_WORDS = 2200
MAX_SUMMARY_CHARS = 150
BANNED_PHRASES = (
    "as an ai",
    "as a language model",
    "i personally tested",
    "i tested this",
    "guaranteed to",
    "100% safe",
)

UNSOURCED_DOSING_PATTERNS = (
    r"\b\d+(?:\.\d+)?\s*(?:to|[-–])\s*\d+(?:\.\d+)?\s*(?:tablespoons?|tbsp|teaspoons?|tsp|cups?|millilit(?:er|re)s?|ml|ounces?|oz)\b",
    r"\b\d+(?:\.\d+)?\s*(?:tablespoons?|tbsp|teaspoons?|tsp|cups?|millilit(?:er|re)s?|ml|ounces?|oz)\b",
    r"\b\d+(?:\.\d+)?\s*%\b",
    r"\b\d+\s*:\s*\d+\b",
)


def evaluate(row: dict[str, str], article: dict) -> tuple[bool, list[str], dict]:
    reasons: list[str] = []
    text = article_text(article)
    words = re.findall(r"\b[\w'-]+\b", text)
    count = len(words)
    summary = " ".join(str(article.get("summary", "")).split())

    if article.get("title", "").strip() != row["Title"].strip():
        reasons.append("title does not match content plan")
    if not summary:
        reasons.append("summary is missing")
    elif len(summary) > MAX_SUMMARY_CHARS:
        reasons.append(f"summary too long: {len(summary)} characters (maximum {MAX_SUMMARY_CHARS})")
    if count < MIN_WORDS:
        reasons.append(f"too short: {count} words (minimum {MIN_WORDS})")
    if count > MAX_WORDS:
        reasons.append(f"too long: {count} words (maximum {MAX_WORDS})")
    if len(article.get("quick_answer", "").split()) < 35:
        reasons.append("quick answer is too thin")
    if not isinstance(article.get("steps"), list) or len(article.get("steps", [])) < 3:
        reasons.append("fewer than 3 practical steps")
    if not isinstance(article.get("mistakes"), list) or len(article.get("mistakes", [])) < 2:
        reasons.append("fewer than 2 useful mistakes/warnings")
    if not isinstance(article.get("sections"), list) or len(article.get("sections", [])) < 2:
        reasons.append("fewer than 2 supporting sections")
    if not isinstance(article.get("faq"), list) or len(article.get("faq", [])) != 3:
        reasons.append("FAQ must contain exactly 3 items")

    lower = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower:
            reasons.append(f"banned phrase: {phrase}")
    if "```" in text:
        reasons.append("markdown code fence found in structured content")
    if re.search(r"https?://", text):
        reasons.append("raw URL found in article body; sources belong in metadata")

    # Exact detergent/cleaner dosing needs a verified source packet because formulas vary.
    if load_source_packet(row) is None:
        for pattern in UNSOURCED_DOSING_PATTERNS:
            if re.search(pattern, lower, flags=re.I):
                reasons.append("unsourced exact cleaner/detergent dose, concentration, or ratio detected")
                break

    # Catch near-empty or repetitive step bodies.
    bodies = []
    for step in article.get("steps", []):
        if not isinstance(step, dict):
            reasons.append("step is not an object")
            continue
        body = str(step.get("body", "")).strip()
        title = str(step.get("title", "")).strip()
        if len(body.split()) < 12 or len(title.split()) < 1:
            reasons.append("one or more steps are underdeveloped")
        normalized = re.sub(r"\W+", " ", body.lower()).strip()
        if normalized:
            bodies.append(normalized)
    if len(bodies) != len(set(bodies)):
        reasons.append("duplicate step text detected")

    report = {
        "article_id": int(row["ID"]),
        "slug": row["Slug"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "word_count": count,
        "summary_characters": len(summary),
        "passed": not reasons,
        "reasons": reasons,
    }
    return not reasons, reasons, report


rows = load_plan()
changed = False
for row in rows:
    if row["Status"] != "Draft":
        continue
    path = article_path(row)
    if not path.exists():
        continue
    article = json.loads(path.read_text(encoding="utf-8"))
    passed, reasons, report = evaluate(row, article)
    out = qa_path(row)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    row["Status"] = "QualityPassed" if passed else "QualityBlocked"
    changed = True
    print(f"Quality {'PASS' if passed else 'BLOCK'}: {row['Slug']}")
    if reasons:
        for reason in reasons:
            print(f" - {reason}")

if changed:
    save_plan(rows)
else:
    print("No Draft articles waiting for quality review.")
