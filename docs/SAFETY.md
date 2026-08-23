# Homekeeping Lab Safety Guardrails

These rules are hard gates for automated article generation. They override style, SEO, and publishing goals.

## Risk levels

- **Risk 0 — routine household care:** low-risk washing, fabric care, drying, dusting, basic maintenance.
- **Risk 1 — caution required:** bleach, disinfectants, acids, limescale removers, hydrogen peroxide, mold cleaning, biological stains, strong cleaners, appliance cleaning where chemicals are involved.
- **Risk 2 — high-risk chemical or exposure topic:** multiple chemical products, concentrated chemicals, severe mold, sewage, unknown substances, or procedures where ventilation/PPE/exposure limits materially matter.
- **Risk 3 — blocked by default:** requests or draft content that combines incompatible chemicals, bypasses product labels, invents concentrations, or recommends hazardous improvisation.

## Non-negotiable prohibitions

The generator must never recommend:

- mixing bleach with ammonia;
- mixing bleach with vinegar or other acids;
- mixing bleach with another cleaner unless the exact combination is explicitly permitted by the product manufacturer;
- mixing unknown cleaning products;
- increasing a chemical concentration beyond label directions;
- using a cleaner on a material when compatibility is unknown and no cautious test step is provided;
- heating, boiling, aerosolizing, or otherwise intensifying household chemicals unless an authoritative source explicitly instructs it;
- entering enclosed spaces with chemical fumes without appropriate ventilation guidance;
- claiming that a homemade chemical mixture is universally safe.

## Source requirements

For any item in `content_plan.csv` with `SourceRequired=yes`, publication must be blocked until the draft is grounded in trustworthy sources appropriate to the topic.

Preferred source order:

1. official manufacturer care/cleaning instructions;
2. government health, poison-control, consumer-safety, or environmental agencies;
3. recognized standards or professional organizations;
4. reputable institutional guidance.

Affiliate pages, anonymous blogs, forums, and AI-generated pages must not be treated as primary safety evidence.

## Mandatory article behavior for Risk 1+

A Risk 1+ article must:

- identify the relevant hazard in plain English;
- tell readers to follow the product label where a commercial chemical is involved;
- avoid unsupported chemical ratios or concentrations;
- include ventilation/PPE guidance when supported by the source and relevant to the task;
- include a material compatibility warning or patch-test step where damage is plausible;
- clearly separate safe alternatives instead of presenting multiple chemicals as ingredients to combine;
- never imply that stronger means safer or more effective.

## Escalation rules

The article generator should stop automatic publication and mark the draft for review when it detects:

- two or more named cleaning chemicals in one procedure;
- chlorine bleach plus any acid/ammonia/unknown cleaner;
- severe or widespread mold;
- sewage, animal waste, or significant blood contamination;
- electrical hazards involving wet appliances;
- unknown chemicals or unlabeled containers;
- symptoms after chemical exposure;
- a draft that conflicts with a source or product label.

## Material safety

Cleaning advice should account for finish/material differences. When exact compatibility cannot be verified, use cautious language and recommend checking the manufacturer instructions or testing in an inconspicuous area first.

## Editorial rule

SEO value never overrides safety. If the safe answer is shorter, more conditional, or less dramatic than competing content, publish the safer answer.
