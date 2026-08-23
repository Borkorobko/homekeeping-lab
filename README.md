# Homekeeping Lab

Automated English-language evergreen content site for practical home cleaning, laundry, stain removal, fabric care, odors, shoes, bedding, kitchen, bathroom, and general home maintenance.

**Domain:** https://homekeepinglab.com

## Current project state

The first end-to-end publishing pipeline is now in place:

- 25-article launch content plan
- explicit category/cluster metadata and related article IDs
- stable `/guides/<slug>/` URL model
- structured OpenAI article generator
- deterministic quality gate
- hard chemical/household safety gate
- verified source-packet requirement for safety-sensitive topics
- static site builder with homepage, category hubs, guide pages, trust pages, sitemap and robots.txt
- GitHub Actions checks
- manual one-article generation workflow

Automatic scheduling is intentionally disabled until the first manual pipeline run succeeds. Cloudflare Pages, custom-domain DNS, Search Console feedback and AdSense come later.

## Publishing states

`Pending → Draft → QualityPassed → SafetyPassed → Published`

A failed check becomes `QualityBlocked` or `SafetyBlocked` and is not published.

## Key files

- `content_plan.csv` — launch article queue and metadata
- `config/site.json` — site/category/publishing configuration
- `scripts/generate.py` — structured article generation
- `scripts/quality_gate.py` — usefulness/structure checks
- `scripts/safety_gate.py` — hard publication safety checks
- `scripts/build_site.py` — static HTML/category/sitemap builder
- `scripts/validate_plan.py` — content-plan integrity checks
- `sources/README.md` — verified safety-source packet format
- `docs/SAFETY.md` — non-negotiable safety rules
- `docs/ARCHITECTURE.md` — architecture and roadmap

## Safety principle

SEO and automation never override household safety. Safety-sensitive advice is blocked unless it satisfies the configured source and safety requirements.
