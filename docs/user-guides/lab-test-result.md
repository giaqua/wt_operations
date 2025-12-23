# User Guide: Lab Test Result

## What this is
Record laboratory analysis for collected samples and assess compliance.

## When to use
- After a Water Sample is submitted and analyzed by the lab

## Quickstart (3–5 minutes)
1. Lab Test Result → New
2. Set `sample_tag` (unique), link `site_visit` (optional)
3. Dates & people:
   - `date_sample_received`, `report_date`, `test_by`, `approved_by`
4. Fill parameters table (per lab report):
   - Physical: pH, Temperature, Turbidity, TSS, TDS
   - Chemical: BOD5, COD, Oil & Grease, nutrients, metals
   - Biological: E. coli, coliforms, helminths
5. Add `test_method`, `quality_control`, `test_report` ID
6. Calculate or set `compliance_status`; add `test_summary`, `recommendations`
7. Submit

## Tips
- Keep units consistent with `Treatment parameter` masters
- Attach the lab PDF for auditability
- Add short rationale when marking non-compliance

## Related
- Reference: ../doctypes/lab-test-result.md
- Upstream: ./water-sample.md
