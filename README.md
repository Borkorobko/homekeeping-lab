# Homekeeping Lab

Automated English-language evergreen content site for practical home cleaning, laundry, stain removal, fabric care, odors, shoes, bedding, kitchen, bathroom, and general home maintenance.

**Domain:** https://homekeepinglab.com

## Current project state

The project foundation is now in place:

- 25-article launch content plan
- explicit category/cluster metadata
- risk levels and source requirements
- hard cleaning/chemical safety guardrails
- stable `/guides/<slug>/` URL model
- explicit related-article IDs for stronger internal linking
- site configuration and publishing rules

The article generator, quality gate, safety gate, site builder, GitHub Actions workflow, Cloudflare Pages deployment, and Search Console feedback loop will be added in the next phases.

## Key files

- `content_plan.csv` — launch article queue and metadata
- `config/site.json` — site/category/publishing configuration
- `docs/SAFETY.md` — non-negotiable safety rules for generated cleaning advice
- `docs/ARCHITECTURE.md` — planned automation and repository architecture

## Safety principle

SEO and automation never override household safety. Risky chemical advice is blocked unless it passes the required source and safety checks.
