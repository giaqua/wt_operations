# Copyright (c) 2026, HM
# For license information, please see license.txt
#
# Report: Daily Off-Spec Report
# Combines:
#   - Daily Operation Report (project, unit, date, waste_water_treated_volume)
#   - Project Operation Water Sample -> Sample Collection Details (per-parameter inlet values)
#   - Off-Spec COD Invoice Calculator (+ Tier Tariff Structure child) for the Daily Off-Spec calc
#
# Assumptions (adjust if your schema differs):
#   1. Project Operation Water Sample.site == Daily Operation Report.project
#   2. Project Operation Water Sample.sampling_date == Daily Operation Report.date
#      (i.e. one water sample per project per day - the row used for parameter/COD lookup)
#   3. Off-Spec COD Invoice Calculator has a "project" Link field (one record per project,
#      versioned by effective_from). The record with the latest effective_from <= row date
#      is used for that row's calculation.
#   4. No docstatus filtering is applied beyond docstatus == 1 on Daily Operation Report.
#   5. If "Sample Process Location" or "Result Type" filters are set, only rows with a
#      matching water sample are shown (rows with no matching sample are dropped).
#
# Extra filters:
#   - show_daily_report / show_water_sample / show_sample_process_location (Check):
#     toggle optional columns on/off. These are forced off when group_by_month is set,
#     since a Daily Operation Report / Water Sample no longer maps 1:1 to a grouped row.
#   - sample_process_location (Data): filters rows by a case-insensitive partial match
#     against the water sample's Sample Process Location. Rows without a matching
#     water sample are excluded when this filter is set.
#   - group_by_month (Check): collapses the daily rows into one row per
#     Project + Unit + Month. Volumes and the Daily Off-Spec amount are summed;
#     parameter readings (COD, pH, TSS, Turbidity, TDS) are volume-weighted
#     averaged; tariff/settings-derived fields are simple-averaged across the
#     days included in that month. A "Days" column shows how many daily rows
#     were rolled up into that month.

import io

import frappe
from frappe import _
from frappe.utils import flt, getdate
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ALL_PARAMETERS = ["COD", "pH", "TSS", "Turbidity.", "TDS."]

# Settings/tariff-derived fields that get averaged (not summed) when grouping monthly
SETTINGS_DERIVED_FIELDS = [
    "element_exceeding_percentage",
    "cost_of_treating_noncompliant_water",
    "additional_processing_cost_difference",
    "contractual_limit_cod",
    "base_processing_cost",
]

# ---------------------------------------------------------------------------
# Excel export constants/helpers
# ---------------------------------------------------------------------------

HM_BLUE_HEX = "010BCE"
HM_RED_HEX = "D50000"

ARABIC_MONTHS = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
    7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
}


def get_month_label(date_val, is_arabic):
    d = getdate(date_val)
    return f"{ARABIC_MONTHS[d.month]} {d.year}" if is_arabic else d.strftime("%B %Y")


def format_excel_value(value, col):
    if value in (None, ""):
        return None, None
    fieldtype = col.get("fieldtype")
    if fieldtype in ("Float", "Currency"):
        return flt(value), "#,##0.00"
    if fieldtype == "Int":
        try:
            return int(value), "0"
        except Exception:
            return value, None
    if fieldtype == "Date":
        return frappe.utils.formatdate(value), None
    return str(value), None


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))


def param_to_fieldname(param):
    return param.strip().rstrip(".").lower().replace(" ", "_").replace(".", "")


def get_columns(filters):
    group_by_month = bool(filters.get("group_by_month"))

    columns = []
    if not filters.get("show_arabic_report"):
        columns = [
            {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
        ]

    if group_by_month:
        # Unit isn't shown normally, but once rows are collapsed to one-per-month
        # it's the only thing distinguishing multiple rows for the same project.
        if not filters.get("hide_project_and_days"):
            columns.append({"label": _("Unit"), "fieldname": "unit", "fieldtype": "Data", "width": 100})
    else:
        if filters.get("show_daily_report"):
            columns.append(
                {
                    "label": _("Daily Report"),
                    "fieldname": "daily_report",
                    "fieldtype": "Link",
                    "options": "Daily Operation Report",
                    "width": 160,
                }
            )

        if filters.get("show_water_sample"):
            columns.append(
                {
                    "label": _("Water Sample"),
                    "fieldname": "water_sample",
                    "fieldtype": "Link",
                    "options": "Project Operation Water Sample",
                    "width": 130,
                }
            )

    if group_by_month:
        columns.append({"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100})
    else:
        columns.append({"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100})

    columns.append(
        {
            "label": _("QTY m3"),
            "fieldname": "waste_water_treated_volume",
            "fieldtype": "Float",
            "width": 170,
        }
    )

    if group_by_month and not filters.get("hide_project_and_days"):
        columns.append({"label": _("Days"), "fieldname": "days_count", "fieldtype": "Int", "width": 80})
        
    elif filters.get("show_sample_process_location"):
        columns.append(
            {
                "label": _("Sample Process Location"),
                "fieldname": "sample_process_location",
                "fieldtype": "Data",
                "width": 160,
            }
        )

    selected_parameters = filters.get("parameter")
    if selected_parameters and isinstance(selected_parameters, str):
        # comes in as JSON-stringified list or comma separated from MultiSelectList
        selected_parameters = (
            frappe.parse_json(selected_parameters)
            if selected_parameters.startswith("[")
            else selected_parameters.split(",")
        )

    parameters = selected_parameters or ALL_PARAMETERS

    for param in parameters:
        columns.append(
            {
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param),
                "fieldtype": "Float",
                "width": 110,
            }
        )

    if filters.get("show_arabic_report"):
        columns.extend(
            [
                # {"label": _("COD الحد التعاقدي"), "fieldname": "contractual_limit_cod", "fieldtype": "Float", "precision": 2, "width": 200},
                # {"label": _("نسبة تجاوز العنصر"), "fieldname": "element_exceeding_percentage", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("Daily Off-Spec"), "fieldname": "base_processing_cost", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("Contractual Allowance"), "fieldname": "cost_of_treating_noncompliant_water", "fieldtype": "Float", "precision": 2, "width": 200},
                # {"label": _("فرق تكلفة المعالجة الإضافي"), "fieldname": "additional_processing_cost_difference", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("Net Billable Off-Spec"), "fieldname": "daily_off_spec", "fieldtype": "Currency", "width": 200},
            ]
        )
    else:
        columns.append(
            {"label": _("Daily Off-Spec (SAR)"), "fieldname": "daily_off_spec", "fieldtype": "Currency", "width": 150}
        )

    return columns, parameters


def get_data(filters, parameters):
    dor_filters = {
        "date": ["between", [filters.get("from_date"), filters.get("to_date")]],
    }
    dor_filters["docstatus"] = 1  # exclude cancelled
    if filters.get("project"):
        dor_filters["project"] = filters.get("project")
    if filters.get("unit"):
        dor_filters["unit"] = filters.get("unit")

    if filters.get("hide_zero_off_spec_rows"):
        dor_filters["waste_water_treated_volume"] = [">", 0]

    dor_list = frappe.get_all(
        "Daily Operation Report",
        filters=dor_filters,
        fields=["name", "project", "unit", "date", "waste_water_treated_volume"],
        order_by="project, unit, date",
    )

    if not dor_list:
        return []

    settings_cache = {}  # project -> list of Off-Spec settings, sorted by effective_from desc
    tier_cache = {}  # settings doc name -> list of tier rows

    data = []

    for dor in dor_list:
        row = {
            "project": dor.project,
            "unit": dor.unit,
            "date": dor.date,
            "waste_water_treated_volume": dor.waste_water_treated_volume,
        }

        pws = get_matching_sample(dor, filters)

        param_values = {}
        if pws:
            sample_rows = frappe.get_all(
                "Sample Collection Details",
                filters={"parent": pws.name, "parenttype": "Project Operation Water Sample"},
                fields=["parameter", "inlet"],
            )
            for sr in sample_rows:
                param_values[sr.parameter] = flt(sr.inlet) if dor.waste_water_treated_volume else 0

        for param in parameters:
            row[param_to_fieldname(param)] = param_values.get(param)

        if filters.get("show_daily_report"):
            row["daily_report"] = dor.name

        if filters.get("show_water_sample"):
            row["water_sample"] = pws.name if pws else None

        if filters.get("show_sample_process_location"):
            row["sample_process_location"] = pws.sample_process_location if pws else None

        cod_value = param_values.get("COD")
        daily_off_spec_values = calculate_daily_off_spec(
            dor.project,
            dor.date,
            dor.waste_water_treated_volume,
            cod_value,
            settings_cache,
            tier_cache,
        ) or [0, 0, 0, 0, 0, 0]

        if len(daily_off_spec_values) > 0:
            row["element_exceeding_percentage"] = daily_off_spec_values[1]
            row["cost_of_treating_noncompliant_water"] = round(daily_off_spec_values[2], 2)
            row["additional_processing_cost_difference"] = round(daily_off_spec_values[3], 2)
            row["contractual_limit_cod"] = round(daily_off_spec_values[4], 2)
            row["base_processing_cost"] = round(daily_off_spec_values[5], 2)
        row["daily_off_spec"] = daily_off_spec_values[0] if len(daily_off_spec_values) > 0 else 0

        data.append(row)

    if filters.get("group_by_month"):
        data = group_data_by_month(data, parameters)

    return data


def group_data_by_month(rows, parameters):
    """Collapse daily rows into one row per Project + Unit + Month.

    - waste_water_treated_volume, daily_off_spec: summed
    - parameter readings (COD, pH, TSS, ...): volume-weighted average
    - tariff/settings-derived fields: simple average across days present
    """
    param_fieldnames = [param_to_fieldname(p) for p in parameters]

    groups = {}
    order = []  # preserves first-seen order of (project, unit, month) for stable sort fallback

    for row in rows:
        month_dt = getdate(row["date"]).replace(day=1)
        month_sort_key = month_dt.strftime("%Y-%m")
        month_label = month_dt.strftime("%b %Y")

        key = (row.get("project"), row.get("unit"), month_sort_key)
        if key not in groups:
            groups[key] = {
                "project": row.get("project"),
                "unit": row.get("unit"),
                "month": month_label,
                "_month_sort": month_sort_key,
                "waste_water_treated_volume": 0.0,
                "days_count": 0,
                "daily_off_spec": 0.0,
                "_param_weighted_sum": {f: 0.0 for f in param_fieldnames},
                "_param_weight": {f: 0.0 for f in param_fieldnames},
                "_settings_sum": {f: 0.0 for f in SETTINGS_DERIVED_FIELDS},
                "_settings_count": {f: 0 for f in SETTINGS_DERIVED_FIELDS},
            }
            order.append(key)

        g = groups[key]
        vol = flt(row.get("waste_water_treated_volume"))
        weight = vol if vol else 1.0

        g["waste_water_treated_volume"] += vol
        g["days_count"] += 1
        g["daily_off_spec"] += flt(row.get("daily_off_spec"))

        for f in param_fieldnames:
            val = row.get(f)
            if val is not None:
                g["_param_weighted_sum"][f] += flt(val) * weight
                g["_param_weight"][f] += weight

        for f in SETTINGS_DERIVED_FIELDS:
            val = row.get(f)
            if val is not None:
                g["_settings_sum"][f] += flt(val)
                g["_settings_count"][f] += 1

    grouped_rows = []
    for key in order:
        g = groups[key]
        out = {
            "project": g["project"],
            "unit": g["unit"],
            "month": g["month"],
            "_month_sort": g["_month_sort"],
            "waste_water_treated_volume": round(g["waste_water_treated_volume"], 2),
            "days_count": g["days_count"],
            "daily_off_spec": round(g["daily_off_spec"], 2),
        }

        for f in param_fieldnames:
            w = g["_param_weight"][f]
            out[f] = round(g["_param_weighted_sum"][f] / w, 2) if w else None

        for f in SETTINGS_DERIVED_FIELDS:
            n = g["_settings_count"][f]
            out[f] = round(g["_settings_sum"][f] / n, 2) if n else None

        grouped_rows.append(out)

    grouped_rows.sort(
        key=lambda r: (r.get("project") or "", r.get("unit") or "", r.get("_month_sort") or "")
    )
    for r in grouped_rows:
        r.pop("_month_sort", None)

    return grouped_rows


def get_matching_sample(dor, filters):
    """Find the Project Operation Water Sample for this DOR's project + date,
    optionally narrowed by Sample Process Location / Result Type text filters."""

    pws_filters = {
        "site": dor.project,
        "sampling_date": dor.date,
    }
    if filters.get("sample_process_location"):
        pws_filters["sample_process_location"] = ["like", "%{0}%".format(filters.get("sample_process_location"))]
    if filters.get("result_type"):
        pws_filters["result_type"] = ["like", "%{0}%".format(filters.get("result_type"))]

    samples = frappe.get_all(
        "Project Operation Water Sample",
        filters=pws_filters,
        fields=["name", "sample_process_location", "result_type"],
        limit_page_length=1,
    )
    return samples[0] if samples else None


def get_applicable_settings(project, date, settings_cache):
    """Latest Off-Spec COD Invoice Calculator record for this project where
    effective_from <= the row's date."""

    if project not in settings_cache:
        settings_cache[project] = frappe.get_all(
            "Off-Spec COD Invoice Calculator",
            filters={"project": project},
            fields=["name", "effective_from", "contractual_cod_baseline_m1ppm"],
            order_by="effective_from desc",
        )

    for setting in settings_cache[project]:
        if setting.effective_from and getdate(setting.effective_from) <= getdate(date):
            return setting

    return None


def get_tier_row(settings_name, cod_value, tier_cache):
    if settings_name not in tier_cache:
        tier_cache[settings_name] = frappe.get_all(
            "Tier Tariff Structure",
            filters={"parent": settings_name, "parenttype": "Off-Spec COD Invoice Calculator"},
            fields=["cod_range_start", "cod_range_end", "tier_tariff", "premium"],
        )

    for tier in tier_cache[settings_name]:
        if tier.cod_range_start <= cod_value <= tier.cod_range_end:
            return tier

    return None


def calculate_daily_off_spec(project, date, treated_vol, cod_value, settings_cache, tier_cache):
    if not cod_value or not treated_vol:
        return 0

    setting = get_applicable_settings(project, date, settings_cache)
    if not setting:
        return 0

    baseline = flt(setting.contractual_cod_baseline_m1ppm)
    if not baseline:
        return 0

    tier = get_tier_row(setting.name, cod_value, tier_cache)
    if not tier:
        return 0

    tier_tariff = flt(tier.tier_tariff) * flt(tier.premium)

    contractual_limit_cod = baseline or 0
    base_processing_cost = flt(treated_vol*cod_value/baseline*tier_tariff) or 0
    element_exceeding_percentage = (flt(cod_value) / 2500) or 0
    # element_exceeding_percentage = flt(tier_tariff*treated_vol) or 0
    cost_of_treating_noncompliant_water = flt(tier_tariff*treated_vol) or 0
    additional_processing_cost_difference = (cost_of_treating_noncompliant_water - flt(tier_tariff)) or 0
    daily_off_spec = (base_processing_cost - cost_of_treating_noncompliant_water) or 0

    return [
        daily_off_spec,
        element_exceeding_percentage,
        cost_of_treating_noncompliant_water,
        additional_processing_cost_difference,
        contractual_limit_cod,
        base_processing_cost,
    ]


# ---------------------------------------------------------------------------
# Print support
# ---------------------------------------------------------------------------
# This is the single source of truth for the print view: it re-runs the exact
# same execute()/get_data() logic used by the report grid (including the
# group_by_month roll-up when that filter is set), then computes the column
# totals ONCE, server-side, directly from that data list. The client
# (report.js) no longer re-derives or re-sums anything - it just renders
# whatever this method returns. This removes any possibility of the print
# totals drifting from (or doubling relative to) what the report itself shows.


@frappe.whitelist()
def get_print_data(filters=None):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)

    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)

    # Compute totals once, from this exact data list - no client-side re-summing.
    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Float", "Currency"):
            fieldname = col.get("fieldname")
            totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in data))

    default_company = frappe.defaults.get_global_default("company")
    company = {}
    if default_company:
        company = frappe.db.get_value(
            "Company", default_company, ["company_name", "company_logo"], as_dict=True
        ) or {}

    return {
        "columns": columns,
        "data": data,
        "totals": totals,
        "company": {
            "company_name": company.get("company_name"),
            "company_logo": company.get("company_logo"),
        },
        "filters": filters,
    }


# ---------------------------------------------------------------------------
# Excel export support
# ---------------------------------------------------------------------------
# Reuses execute()/get_data() exactly like get_print_data() does, so the
# workbook's rows, monthly roll-up, and totals can never drift from the
# report grid or the branded print view. build_excel_workbook() mirrors the
# layout logic in report.js (render_print_window / build_body_rows_with_
# monthly_subtotals) as closely as HTML->XLSX allows: same title/period/
# generated-on header block, same monthly subtotal rows (QTY + Daily Off-Spec
# only), same single grand-total row at the end.


def build_excel_workbook(columns, data, totals, filters, company, is_arabic, add_monthly_subtotals):
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    if is_arabic:
        ws.sheet_view.rightToLeft = True

    n_cols = len(columns)
    header_fill = PatternFill("solid", fgColor="F1F2FB")
    subtotal_fill = PatternFill("solid", fgColor="FDEAEA")
    blue_font = Font(color=HM_BLUE_HEX, bold=True, size=11)
    title_font = Font(bold=True, size=13)
    meta_font = Font(size=9, italic=True)
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    is_monthly = bool(filters.get("group_by_month"))
    if is_arabic:
        title = (
            "التقرير الشهري لمخالفة المواصفات" if is_monthly
            else "التقرير اليومي التفصيلي لمخالفة المواصفات مع إجمالي شهري" if add_monthly_subtotals
            else "التقرير اليومي لمخالفة المواصفات"
        )
    else:
        title = (
            "Daily Off-Spec Report (Monthly Summary)" if is_monthly
            else "Daily Off-Spec Report (Detailed, with Monthly Totals)" if add_monthly_subtotals
            else "Daily Off-Spec Report"
        )

    row_cursor = 1

    # Company name (title row)
    ws.merge_cells(start_row=row_cursor, start_column=1, end_row=row_cursor, end_column=n_cols)
    c = ws.cell(row=row_cursor, column=1, value=company.get("company_name") or "")
    c.font, c.alignment = title_font, Alignment(horizontal="center")
    row_cursor += 1

    # Report title
    ws.merge_cells(start_row=row_cursor, start_column=1, end_row=row_cursor, end_column=n_cols)
    c = ws.cell(row=row_cursor, column=1, value=title)
    c.font, c.alignment = blue_font, Alignment(horizontal="center")
    row_cursor += 1

    # Period / generated-on meta line
    date_label = "الفترة" if is_arabic else "Period"
    gen_label = "تاريخ الطباعة" if is_arabic else "Generated on"
    meta_text = (
        f"{date_label}: {frappe.utils.formatdate(filters.get('from_date'))} - "
        f"{frappe.utils.formatdate(filters.get('to_date'))}    |    "
        f"{gen_label}: {frappe.utils.now_datetime().strftime('%Y-%m-%d %H:%M')}"
    )
    ws.merge_cells(start_row=row_cursor, start_column=1, end_row=row_cursor, end_column=n_cols)
    c = ws.cell(row=row_cursor, column=1, value=meta_text)
    c.font, c.alignment = meta_font, Alignment(horizontal="center")
    row_cursor += 1

    # Logo (best-effort - never let a missing/broken logo break the export)
    if company.get("company_logo"):
        try:
            from frappe.utils.file_manager import get_file_path

            img = XLImage(get_file_path(company["company_logo"]))
            img.height, img.width = 45, 110
            ws.add_image(img, "A1")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Excel export logo embed failed")

    row_cursor += 1  # spacer row

    # Column header row
    header_row_idx = row_cursor
    for idx, col in enumerate(columns, start=1):
        c = ws.cell(row=header_row_idx, column=idx, value=_(col.get("label")))
        c.font, c.fill, c.border = blue_font, header_fill, border
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    row_cursor += 1

    def write_row(row_idx, row_data, bold=False, fill=None):
        for idx, col in enumerate(columns, start=1):
            value, fmt = format_excel_value(row_data.get(col.get("fieldname")), col)
            c = ws.cell(row=row_idx, column=idx, value=value)
            c.border = border
            if fmt:
                c.number_format = fmt
            if bold:
                c.font = Font(bold=True)
            if fill:
                c.fill = fill
            is_num = col.get("fieldtype") in ("Float", "Currency", "Int")
            c.alignment = Alignment(horizontal="right" if (is_num or is_arabic) else "left")

    qty_field, offspec_field = "waste_water_treated_volume", "daily_off_spec"
    qty_idx = next((i for i, col in enumerate(columns) if col.get("fieldname") == qty_field), 0)
    label_span = max(qty_idx, 1)

    def write_subtotal(row_idx, label, vol_sum, offspec_sum):
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=label_span)
        c = ws.cell(row=row_idx, column=1, value=label)
        c.font, c.fill, c.border = Font(bold=True), subtotal_fill, border
        c.alignment = Alignment(horizontal="right" if is_arabic else "left")
        for idx, col in enumerate(columns, start=1):
            cell = ws.cell(row=row_idx, column=idx)
            cell.fill, cell.border = subtotal_fill, border
            fname = col.get("fieldname")
            if fname == qty_field:
                cell.value, cell.number_format = round(vol_sum, 2), "#,##0.00"
            elif fname == offspec_field:
                cell.value, cell.number_format = round(offspec_sum, 2), "#,##0.00"
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="right")

    if add_monthly_subtotals and not is_monthly:
        # Same grouping logic as build_body_rows_with_monthly_subtotals() in
        # report.js: insert a bold subtotal row every time the
        # Project + Unit + Month key changes.
        group_key, month_label, vol_sum, offspec_sum = None, "", 0.0, 0.0
        for row in data:
            month_key = str(row.get("date") or "")[:7]
            key = f"{row.get('project') or ''}|{row.get('unit') or ''}|{month_key}"
            if group_key is not None and key != group_key:
                label = f"إجمالي - {month_label}" if is_arabic else f"Total - {month_label}"
                write_subtotal(row_cursor, label, vol_sum, offspec_sum)
                row_cursor += 1
                vol_sum, offspec_sum = 0.0, 0.0
            group_key = key
            month_label = get_month_label(row.get("date"), is_arabic)
            vol_sum += flt(row.get(qty_field))
            offspec_sum += flt(row.get(offspec_field))
            write_row(row_cursor, row)
            row_cursor += 1
        if group_key is not None:
            label = f"إجمالي - {month_label}" if is_arabic else f"Total - {month_label}"
            write_subtotal(row_cursor, label, vol_sum, offspec_sum)
            row_cursor += 1
    else:
        for row in data:
            write_row(row_cursor, row)
            row_cursor += 1

    # Grand total row (once, at the very end - mirrors tr.grand-total-row)
    totals_label = "الإجمالي" if is_arabic else "Total"
    ws.merge_cells(start_row=row_cursor, start_column=1, end_row=row_cursor, end_column=label_span)
    c = ws.cell(row=row_cursor, column=1, value=totals_label)
    c.font, c.fill, c.border = Font(bold=True, color=HM_BLUE_HEX), header_fill, border
    c.alignment = Alignment(horizontal="right" if is_arabic else "left")
    for idx, col in enumerate(columns, start=1):
        cell = ws.cell(row=row_cursor, column=idx)
        cell.fill, cell.border = header_fill, border
        fname = col.get("fieldname")
        if totals and fname in totals and fname in (qty_field, offspec_field):
            cell.value = round(flt(totals[fname]), 2)
            cell.font = Font(bold=True, color=HM_BLUE_HEX)
            cell.number_format = "#,##0.00"
            cell.alignment = Alignment(horizontal="right")

    # Column widths + freeze panes (freeze header, not the brand block)
    for idx, col in enumerate(columns, start=1):
        width = col.get("width") or 100
        ws.column_dimensions[get_column_letter(idx)].width = max(10, min(40, width / 7))
    ws.freeze_panes = ws.cell(row=header_row_idx + 1, column=1)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


@frappe.whitelist()
def export_excel(filters=None, add_monthly_subtotals=0):
    """Same source-of-truth pattern as get_print_data(): re-run execute()/
    get_data(), compute totals once from that exact data list, then hand off
    to build_excel_workbook() for layout. Returns a binary xlsx download."""

    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)

    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)

    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Float", "Currency"):
            fieldname = col.get("fieldname")
            totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in data))

    default_company = frappe.defaults.get_global_default("company")
    company = {}
    if default_company:
        company = frappe.db.get_value(
            "Company", default_company, ["company_name", "company_logo"], as_dict=True
        ) or {}

    is_arabic = bool(filters.get("show_arabic_report"))
    add_monthly_subtotals = frappe.utils.cint(add_monthly_subtotals)

    xlsx_data = build_excel_workbook(
        columns,
        data,
        totals,
        filters,
        {
            "company_name": company.get("company_name"),
            "company_logo": company.get("company_logo"),
        },
        is_arabic,
        bool(add_monthly_subtotals),
    )

    is_monthly = bool(filters.get("group_by_month"))
    suffix = "Monthly" if is_monthly else ("Detailed_Monthly_Totals" if add_monthly_subtotals else "Daily")
    filename = f"Daily_Off_Spec_Report_{suffix}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"

    frappe.response["filename"] = filename
    frappe.response["filecontent"] = xlsx_data
    frappe.response["type"] = "binary"