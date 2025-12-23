# User Guide: Customer Proposal

## What this is
Commercial proposal with options (Supply & Installation, Design-Build, BOOT) built on top of the Technical Proposal.

## When to use
- After the Technical Proposal is approved internally
- To present options, pricing, terms to the customer

## Quickstart (4–6 minutes)
1. Customer Proposal → New
2. Set `customer` and `wwtp_technical_proposal` (required)
3. Click “Auto-fill from Technical Proposal” → seeds technical sections
4. Set dates: `issue_date`, `valid_up_to` (system suggests +60 days)
5. Fill Options:
   - Option 1 (Supply & Installation): add equipment/services in `option_1_table`
   - Option 2 (Design-Build): add design/construction items in `option_2_table`
   - Option 3 (BOOT): set `boot_concession_period`, `boot_operation_period`, terms; add items in `option_3_table`
6. Add scope/terms: `scope_of_work`, `termination_points`, `exclusions`
7. Use “Fetch Roles & Responsibilities” to populate roles table
8. Validate dates/BOOT periods → Submit

## Buttons
- Auto-fill from Technical Proposal
- Fetch Roles & Responsibilities
- Proposal Summary

## Validations & pitfalls
- `valid_up_to` must be after `issue_date`
- `boot_operation_period` must be ≤ `boot_concession_period`
- Ensure each selected option has items

## Tips
- Keep option summaries concise for executive readers
- Confirm warranty/support language with legal
- Align payment terms with finance policy

## Related
- Reference: ../doctypes/customer-proposal.md
- Optional next: ./request-for-proposal.md
