# Homekeeping Lab Architecture

## Goal

Build a mostly automated English-language evergreen site for home cleaning, laundry, stain removal, fabric care, odors, shoes, bedding, kitchen, bathroom, and general home maintenance.

## Core pipeline

1. `content_plan.csv` is the source of truth for planned articles.
2. The generator selects only eligible `Pending` topics, ordered by priority.
3. A duplicate/cannibalization gate checks title, intent, cluster, and existing published content.
4. A safety classifier reads `RiskLevel` and the draft itself.
5. Source retrieval is mandatory when `SourceRequired=yes` or when the draft is escalated by the safety classifier.
6. The article is generated into a structured HTML template.
7. Quality gates check usefulness, structure, metadata, links, unsupported claims, and obvious repetition.
8. The safety gate blocks unsafe chemical advice.
9. Explicit `RelatedIDs` are used for primary internal links; semantic similarity is only a fallback.
10. Category pages, homepage, sitemap, robots.txt, and article indexes are rebuilt.
11. GitHub Actions commits/publishes only when all required gates pass.
12. Google Search Console feedback will be added later once useful performance data exists.

## Planned repository layout

```text
homekeeping-lab/
├── .github/
│   └── workflows/
├── config/
│   └── site.json
├── docs/
│   ├── ARCHITECTURE.md
│   └── SAFETY.md
├── guides/                 # generated article output
├── images/                 # generated/approved article imagery
├── scripts/
│   ├── generate.py
│   ├── quality_gate.py
│   ├── safety_gate.py
│   ├── build_site.py
│   └── validate_plan.py
├── templates/
├── content_plan.csv
├── index.html
├── robots.txt
└── sitemap.xml
```

Directories that contain generated content will be created when the generator is added.

## URL model

Articles use stable guide URLs independent of category changes:

`https://homekeepinglab.com/guides/<slug>/`

Category hubs use short top-level URLs, for example:

- `/laundry/`
- `/stain-removal/`
- `/fabric-care/`
- `/bathroom/`
- `/kitchen/`
- `/odors/`
- `/bedding-towels/`
- `/shoes/`
- `/home-cleaning/`

## Internal linking

Football Training Lab primarily inferred related articles from shared title tokens. Homekeeping Lab will instead use explicit relationships from `content_plan.csv` as the primary system.

Each article can specify up to four `RelatedIDs`. The generator should validate that every referenced ID exists and should prefer links within the same problem journey or content cluster. Semantic similarity may fill missing slots but must not override explicit links.

## Content plan fields

- `ID` — stable article identifier.
- `Title` — intended page title/topic.
- `Category` — primary user-facing section.
- `Cluster` — narrower topical cluster.
- `Intent` — user search intent.
- `Priority` — lower number means earlier publication.
- `RiskLevel` — safety classification from 0 to 3.
- `SourceRequired` — whether authoritative sourcing is mandatory before publication.
- `ParentHub` — category hub that should link to the guide.
- `RelatedIDs` — pipe-delimited explicit related article IDs.
- `Status` — workflow state.
- `PublishedDate` — populated only after publication.
- `Slug` — stable URL slug.

## Launch strategy

The initial plan contains 25 launch articles. We will not publish them blindly in one burst. The build should support staged publication, with the initial high-priority cluster coverage followed by roughly 2–4 new guides per week after launch.

## Later phases

- GitHub Actions automation
- OpenAI API article generation
- source verification layer
- article templates and design system
- automatic sitemap/category rebuild
- deployment through Cloudflare Pages
- custom-domain DNS setup
- Google Search Console + feedback loop
- AdSense after the site has sufficient quality and traffic
