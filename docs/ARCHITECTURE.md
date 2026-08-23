# Homekeeping Lab Architecture

## Goal

Build a mostly automated English-language evergreen site for home cleaning, laundry, stain removal, fabric care, odors, shoes, bedding, kitchen, bathroom, and general home maintenance.

## Implemented pipeline

1. `content_plan.csv` is the source of truth.
2. `scripts/validate_plan.py` validates IDs, slugs, categories, hubs, risk levels and explicit related links.
3. `scripts/generate.py` selects one eligible `Pending` topic by priority.
4. Topics with `SourceRequired=yes` are skipped until a verified `sources/<ID>.json` packet exists.
5. The generator writes structured JSON, not free-form page HTML.
6. `scripts/quality_gate.py` checks length, structure, practical depth, repetition and prohibited low-quality language.
7. `scripts/safety_gate.py` blocks unsafe chemical instructions, missing required sources and escalation topics.
8. `scripts/build_site.py` publishes only articles that reached `SafetyPassed`, then builds the static site.
9. Explicit `RelatedIDs` are the primary internal-link system.
10. The builder generates homepage, category hubs, guide pages, About, Editorial Policy, Safety Policy, sitemap and robots.txt.
11. `.github/workflows/generate.yml` runs one complete article cycle manually.
12. `.github/workflows/checks.yml` compiles scripts, validates the content plan and tests the static build on pushes/PRs.

## Publishing states

`Pending → Draft → QualityPassed → SafetyPassed → Published`

Failed checks become `QualityBlocked` or `SafetyBlocked`; blocked content is not rendered into the public site.

## Repository layout

```text
homekeeping-lab/
├── .github/
│   └── workflows/
│       ├── checks.yml
│       └── generate.yml
├── config/
│   └── site.json
├── content/
│   └── articles/          # generated structured article JSON
├── docs/
│   ├── ARCHITECTURE.md
│   └── SAFETY.md
├── qa/                    # machine-readable quality/safety reports
├── scripts/
│   ├── common.py
│   ├── generate.py
│   ├── quality_gate.py
│   ├── safety_gate.py
│   ├── build_site.py
│   └── validate_plan.py
├── site/                  # generated deployable static site
├── sources/               # verified source packets for safety-sensitive topics
├── content_plan.csv
└── requirements.txt
```

## URL model

Articles use stable guide URLs independent of category changes:

`https://homekeepinglab.com/guides/<slug>/`

Category hubs use top-level URLs such as `/laundry/`, `/stain-removal/`, `/bathroom/`, `/kitchen/`, `/odors/` and `/shoes/`.

## Safety model

Safety rules are enforced twice: generation instructions reduce unsafe output, but publication does not trust the prompt alone. The deterministic safety gate separately checks the completed draft.

Risk 0 can proceed without a source packet when the topic is genuinely routine. Risk 1+ requires a valid authoritative source packet. Risk 2 additionally requires `approved_for_auto_publish=true`. Risk 3 is blocked from automatic publication.

## Internal linking

Football Training Lab primarily inferred related articles from shared title tokens. Homekeeping Lab instead uses explicit `RelatedIDs` as the primary relationship graph. Only related guides that are actually published are rendered as links.

## Launch strategy

The initial plan contains 25 launch articles. We will not publish them in one burst. After the first manual end-to-end test succeeds, the workflow can be scheduled for roughly 2–4 new guides per week.

## Remaining phases

- add `OPENAI_API_KEY` as a GitHub Actions repository secret
- run and inspect the first manual article cycle
- fix any real-world pipeline issues found by that run
- enable the publishing schedule
- connect the deployable `site/` directory to hosting
- connect `homekeepinglab.com` through DNS
- add Search Console after indexing/performance data exists
- add AdSense only after the site has enough useful content and traffic
