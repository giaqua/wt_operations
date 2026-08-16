# Water Sample Comprehensive Report — install notes

## 1. Where to put these files

Copy the inner `water_sample_comprehensive_report/` folder into:

```
apps/wt_operations/wt_operations/wt_operations/report/water_sample_comprehensive_report/
```

(i.e. it should sit alongside your other reports like the Water Treatment Register report.)

Final structure should look like:

```
wt_operations/wt_operations/report/water_sample_comprehensive_report/
├── __init__.py
├── water_sample_comprehensive_report.json
├── water_sample_comprehensive_report.py
├── water_sample_comprehensive_report.js
├── print_template.html
└── monthly_print_template.html
```

## 2. Migrate

```bash
cd frappe-bench-15
bench --site <your-site> migrate
bench build --app wt_operations
bench restart
```

The report will show up under Report List / from the "Project Operation Water Sample" doctype's report view, module "Wt Operations".

## 3. Things to check / adjust before go-live

- **`module` in the .json`** — set to `"Wt Operations"`. If your app's module name is spelled differently (check `wt_operations/modules.txt`), fix this or the report won't load.
- **Roles** — I put `System Manager` and `Water Treatment Manager`. If that second role doesn't exist in your site, remove it or the report record will fail to import; add whatever role should have access instead.
- **Compliance logic (`get_compliance_status`)** — I used a placeholder rule: any parameter is "Exceeds" if `inlet > contract_inlet`, except pH which I hardcoded as an acceptable range of 6–9. Your actual sample (PWS-808) has `contract_inlet = 9` for pH with an inlet of 3.89 — that's a range-based limit, not a single ceiling, so I couldn't infer the real rule from the JSON alone. Tell me the actual pass/fail rule per parameter (or send a couple more samples) and I'll tighten this.
- **`sample_type` / `parameter` filter option lists** in the `.js` — I used the values I could see in your sample (`Industrial`, `COD`, `pH`, `TSS`, `Turbidity.`, `TDS.`). Update these `Select` options to match the full list actually used in your Select fields on the doctype, or I can pull them dynamically from `Sample Collection Details` if you'd rather not hardcode.
- **Letterhead/branding** — the print and Excel layouts currently use a plain navy header (`#1F4E78`) with no logo, since there wasn't an existing print format to match. Send your logo/company colors if you want it branded like your other Excel exports (e.g. Water Treatment Register).

## 4. How the buttons work

- **Print** and **Export to Excel** call `GET /api/method/...download_print_pdf` / `...download_excel` with the current report filters as a JSON query param, and open the file directly (no frappe.call/JSON round-trip, so large PDFs/Excel files stream straight to the browser).
- **Monthly Print (Detailed)** opens a small dialog (month, year, optional site), then hits `download_monthly_pdf`, which groups all readings for that month by sample and includes a summary line (total readings / how many exceeded limits).

All three are plain Python functions decorated `@frappe.whitelist()` in `water_sample_comprehensive_report.py` — easy to extend (e.g. add a "Send by WhatsApp" button reusing your `wa_messaging` app, since the PDF bytes are already in hand).