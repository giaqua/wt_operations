# User Guide: WWTP Technical Questionnaire

## What this is
The starting document for every WWTP engagement. Capture customer context, site constraints, influent/effluent expectations, and trigger downstream actions (Site Visit Request, Proposals).

## When to use
- New lead/opportunity needs a technical assessment
- Existing facility requires upgrade study
- Pre-RFP scoping with basic requirements

## Quickstart (3–5 minutes)
1. Go to WT Operations → WWTP Technical Questionnaire → New
2. Set `lead` (required) and optionally `opportunity`
3. Set `date`
4. Enter project basics:
   - `wastewater_generator_type`
   - `capacity` (m³/day)
   - Site footprint/location notes
5. Pick `please_pick_the_target_effluent_type` → system auto-fills effluent parameters (pH, TSS, BOD5, …)
6. Set `number_of_streams` if applicable → rows auto-create in Influent Streams table
7. Review/adjust `roles_and_responsibilities` (auto-populated from Scope of Work)
8. Flag `site_visit_required` and/or `sample_collection_required` if needed
9. Submit

## Key fields to get right
- `wastewater_generator_type`: drives defaults and language in downstream docs
- `capacity` and `daily_flow`: inform sizing and timeline
- `please_pick_the_target_effluent_type`: unlocks effluent auto-population
- `site_visit_required`, `sample_collection_required`: determine next workflow step

## Common actions
- Create Site Visit Request: click “Create Site Visit Request” (post-submit)
- Refresh effluent targets: click “Refresh Effluent Parameters” after changing target type

## Tips
- Prefer linking an `opportunity`—it improves traceability into Sales
- Use coordinates and map link in location notes to prevent survey delays
- Keep comments concise; proposals will reuse this language

## Validation & pitfalls
- Capacity must be positive; effluent target must be selected for auto-fill
- If follow-up integrations fail, re-open and re-trigger after fixing External Site Settings

## Related
- Reference: ../doctypes/wwtp-technical-questionnaire.md
- Next step: ./site-visit-request.md
