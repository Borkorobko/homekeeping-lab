# Verified source packets

Safety-sensitive articles are not eligible for automatic generation/publication until a verified source packet exists here.

Use the article ID as the file name, for example `3.json`.

Example:

```json
{
  "article_id": 3,
  "verified_at": "2026-08-23",
  "approved_for_auto_publish": false,
  "notes": "Use only the supplied manufacturer/government guidance for safety-sensitive claims.",
  "sources": [
    {
      "title": "Official guidance title",
      "url": "https://example.gov/guidance",
      "authority": "Government agency",
      "claims": ["Specific supported claim", "Another supported claim"]
    }
  ]
}
```

Rules:

- Prefer official manufacturer instructions and government/poison-control/consumer-safety sources.
- Do not use anonymous blogs, affiliate pages, forums, or AI-generated pages as primary safety evidence.
- `approved_for_auto_publish=true` is required for RiskLevel 2 and should only be set after a deliberate source review.
- Source packets are evidence inputs, not article copy. The generator must not invent additional safety-sensitive details.
