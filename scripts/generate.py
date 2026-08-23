from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from openai import OpenAI

from common import (
    article_path,
    load_plan,
    load_source_packet,
    normalize_source_required,
    save_plan,
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def eligible(row: dict[str, str]) -> bool:
    if row["Status"].strip().lower() != "pending":
        return False
    risk = int(row["RiskLevel"])
    if risk >= 3:
        return False
    if article_path(row).exists():
        return False
    if normalize_source_required(row["SourceRequired"]) and load_source_packet(row) is None:
        return False
    return True


def choose_topic(rows: list[dict[str, str]]) -> dict[str, str] | None:
    candidates = [row for row in rows if eligible(row)]
    candidates.sort(key=lambda row: (int(row["Priority"]), int(row["ID"])))
    return candidates[0] if candidates else None


def source_context(row: dict[str, str]) -> str:
    packet = load_source_packet(row)
    if not packet:
        return "No external source packet is required for this low-risk topic. Do not invent studies, statistics, or product-specific claims."
    safe = {
        "notes": packet.get("notes", ""),
        "sources": packet.get("sources", []),
    }
    return json.dumps(safe, ensure_ascii=False, indent=2)


rows = load_plan()
row = choose_topic(rows)
if row is None:
    print("No eligible Pending article. Source-required topics remain blocked until a source packet exists.")
    raise SystemExit(0)

risk = int(row["RiskLevel"])
sources = source_context(row)

prompt = f'''
You are writing one practical English guide for Homekeeping Lab, an evergreen home cleaning, laundry and home-care website.

Exact title: {row['Title']}
Category: {row['Category']}
Cluster: {row['Cluster']}
Search intent: {row['Intent']}
Risk level: {risk}

SAFETY RULES OVERRIDE SEO AND STYLE:
- Never recommend mixing bleach with ammonia, vinegar, acids, or another cleaner unless a manufacturer explicitly permits the exact combination.
- Never recommend mixing unknown cleaning products.
- Never invent chemical ratios, concentrations, exposure limits, dwell times, material compatibility, or product-label directions.
- Do not tell readers that stronger chemical concentration is better.
- If a commercial cleaner is relevant, tell the reader to follow the product label.
- When material compatibility is uncertain, recommend manufacturer guidance or an inconspicuous patch test.
- Do not claim personal testing or first-hand experience.
- Do not invent studies, statistics, certifications, or endorsements.
- If a source packet is provided, use only claims supported by it for safety-sensitive details.

SOURCE PACKET:
{sources}

Return ONLY one valid JSON object. Do not use Markdown fences.
Required shape:
{{
  "title": "exact requested title",
  "summary": "1-2 sentence summary",
  "quick_answer": "direct answer in 80-160 words",
  "items_needed": ["item or condition"],
  "steps": [
    {{"title": "short step title", "body": "clear step explanation"}}
  ],
  "mistakes": ["specific mistake and why to avoid it"],
  "safety_notes": ["only relevant, useful safety notes"],
  "sections": [
    {{"heading": "useful supporting section", "body": "detailed explanation", "bullets": ["optional practical bullet"]}}
  ],
  "faq": [
    {{"question": "question", "answer": "concise answer"}},
    {{"question": "question", "answer": "concise answer"}},
    {{"question": "question", "answer": "concise answer"}}
  ]
}}

Quality requirements:
- Aim for roughly 900-1500 useful words, but do not pad.
- Answer the problem immediately, then explain why the method works and where it may not apply.
- Give concrete steps rather than generic cleaning advice.
- Include at least 4 steps when the topic is procedural.
- Include material-specific caveats when relevant.
- Mention what not to do when it prevents damage or unsafe use.
- Keep the tone calm and practical, not promotional.
'''

response = client.responses.create(model=MODEL, input=prompt)
raw = clean_json_text(response.output_text)
article = json.loads(raw)

required_keys = {"title", "summary", "quick_answer", "items_needed", "steps", "mistakes", "safety_notes", "sections", "faq"}
missing = required_keys - set(article)
if missing:
    raise RuntimeError(f"Generated JSON is missing fields: {sorted(missing)}")
if article["title"].strip() != row["Title"].strip():
    article["title"] = row["Title"].strip()

article["meta"] = {
    "id": int(row["ID"]),
    "slug": row["Slug"],
    "category": row["Category"],
    "cluster": row["Cluster"],
    "intent": row["Intent"],
    "risk_level": risk,
    "source_required": normalize_source_required(row["SourceRequired"]),
    "parent_hub": row["ParentHub"],
    "related_ids": [int(x) for x in row["RelatedIDs"].split("|") if x.strip()],
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "model": MODEL,
}

path = article_path(row)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(article, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for item in rows:
    if item["ID"] == row["ID"]:
        item["Status"] = "Draft"
        break
save_plan(rows)
print(f"Generated draft: {path.relative_to(path.parents[2]) if len(path.parents) > 2 else path}")
