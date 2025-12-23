# User Guide: Site Visit Request

## What this is
Plan and coordinate a site survey: who, when, where, why, with the right priority and equipment.

## When to use
- After a Technical Questionnaire is submitted
- Customer asks for a technical visit

## Quickstart (2–4 minutes)
1. From a submitted TQ, click “Create Site Visit Request”, or go to Site Visit Request → New
2. Set `lead` (required) and `site_visit_date`
3. (Optional) Link `opportunity` and `technical_questionnaire`
4. Set Visit Details:
   - `visit_type`, `priority`, `assigned_to`
5. Fill Location:
   - `site_address`, `city`, `state`, add `latitude_and_longitude` or `maps_location_link`
6. Requirements:
   - `visit_purpose`, `special_requirements`, `equipment_needed`, `estimated_duration`
7. Follow-up (if needed): set `follow_up_required`, `follow_up_date`, notes
8. Submit → status moves from Open to Scheduled

## Buttons & automations
- Auto-fill Contact Details: after picking `lead`
- Sync to External Site / Retry Sync: push to partner site (if configured)
- Create Site Visit: available after submit
- Open External SVR: open synced record URL

## Validations & pitfalls
- `lead` and `site_visit_date` are required
- `follow_up_date` cannot be before `site_visit_date`
- If sync fails, check `external_sync_error`, fix External Site Settings, then Retry

## Checklist
- [ ] Visit purpose is clear and actionable
- [ ] Equipment list covers testing/measurement and PPE
- [ ] Coordinates/map link added
- [ ] Priority aligns with customer expectation

## Related
- Reference: ../doctypes/site-visit-request.md
- Next step: ./site-visit.md
