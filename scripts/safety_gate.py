from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from common import (
    article_path,
    article_text,
    load_plan,
    load_source_packet,
    normalize_source_required,
    qa_path,
    save_plan,
)

NEGATIONS = ("do not", "don't", "never", "avoid", "must not", "should not", "cannot", "can't")
ESCALATION_TERMS = (
    "sewage",
    "widespread mold",
    "large area of mold",
    "chemical exposure symptoms",
    "difficulty breathing after",
    "unlabeled chemical",
    "unknown chemical",
)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def negated(sentence: str) -> bool:
    lower = sentence.lower()
    return any(term in lower for term in NEGATIONS)


def dangerous_instruction(sentence: str) -> str | None:
    lower = sentence.lower()
    if negated(sentence):
        return None

    action = bool(re.search(r"\b(mix|combine|add|pour|blend)\b", lower))
    has_bleach = bool(re.search(r"\b(bleach|chlorine bleach)\b", lower))
    incompatible = bool(re.search(r"\b(ammonia|vinegar|acid|toilet cleaner|drain cleaner|another cleaner)\b", lower))
    if action and has_bleach and incompatible:
        return "instruction appears to combine bleach with an incompatible cleaner"

    # Do not auto-publish invented bleach recipes/concentrations.
    if has_bleach and re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|milliliters?|l|liters?|oz|ounces?|cups?|tbsp|tablespoons?|tsp|teaspoons?|%)\b", lower):
        return "numeric bleach recipe/concentration detected"

    if action and "cleaner" in lower and "unknown" in lower:
        return "instruction appears to combine an unknown cleaner"
    return None


def source_packet_valid(packet: dict | None) -> tuple[bool, str | None]:
    if not packet:
        return False, "required authoritative source packet is missing"
    sources = packet.get("sources", [])
    if not isinstance(sources, list) or not sources:
        return False, "source packet contains no sources"
    for source in sources:
        if not isinstance(source, dict):
            return False, "source entry is not an object"
        if not source.get("title") or not source.get("url") or not source.get("authority"):
            return False, "source entry is missing title, url, or authority"
        if not str(source.get("url", "")).startswith("https://"):
            return False, "source URL must use https"
    return True, None


rows = load_plan()
changed = False
for row in rows:
    if row["Status"] != "QualityPassed":
        continue

    path = article_path(row)
    if not path.exists():
        continue
    article = json.loads(path.read_text(encoding="utf-8"))
    text = article_text(article)
    risk = int(row["RiskLevel"])
    source_required = normalize_source_required(row["SourceRequired"])
    packet = load_source_packet(row)
    reasons: list[str] = []

    if risk >= 3:
        reasons.append("RiskLevel 3 is blocked from automatic publication")

    if source_required or risk >= 1:
        valid, reason = source_packet_valid(packet)
        if not valid and reason:
            reasons.append(reason)

    if risk == 2 and not (packet and packet.get("approved_for_auto_publish") is True):
        reasons.append("RiskLevel 2 requires explicit approved_for_auto_publish=true in the verified source packet")

    lower = text.lower()
    for term in ESCALATION_TERMS:
        if term in lower:
            reasons.append(f"escalation topic detected: {term}")

    for sentence in sentences(text):
        reason = dangerous_instruction(sentence)
        if reason:
            reasons.append(reason)

    # A risk 1+ article must include at least one useful safety note.
    if risk >= 1 and len(article.get("safety_notes", [])) < 1:
        reasons.append("RiskLevel 1+ article has no safety notes")

    # Deduplicate reasons for a compact audit report.
    reasons = list(dict.fromkeys(reasons))
    passed = not reasons
    row["Status"] = "SafetyPassed" if passed else "SafetyBlocked"
    changed = True

    report_path = qa_path(row)
    report = {}
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    report["safety"] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "risk_level": risk,
        "source_required": source_required,
        "passed": passed,
        "reasons": reasons,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Safety {'PASS' if passed else 'BLOCK'}: {row['Slug']}")
    for reason in reasons:
        print(f" - {reason}")

if changed:
    save_plan(rows)
else:
    print("No QualityPassed articles waiting for safety review.")
