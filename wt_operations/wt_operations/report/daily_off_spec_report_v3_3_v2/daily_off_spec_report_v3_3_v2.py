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

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

ALL_PARAMETERS = ["COD", "pH", "TSS", "Turbidity.", "TDS."]

# Settings/tariff-derived fields that get averaged (not summed) when grouping monthly
SETTINGS_DERIVED_FIELDS = [
    "element_exceeding_percentage",
    "cost_of_treating_noncompliant_water",
    "additional_processing_cost_difference",
    "contractual_limit_cod",
    "base_processing_cost",
]


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
                {"label": _("COD الحد التعاقدي"), "fieldname": "contractual_limit_cod", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("نسبة تجاوز العنصر"), "fieldname": "element_exceeding_percentage", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("تكلفة المعالجة الأساسية"), "fieldname": "base_processing_cost", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("تكلفة معالجة المياه الغير مطابقة"), "fieldname": "cost_of_treating_noncompliant_water", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("فرق تكلفة المعالجة الإضافي"), "fieldname": "additional_processing_cost_difference", "fieldtype": "Float", "precision": 2, "width": 200},
                {"label": _("فرق تكاليف فترة الاحتساب"), "fieldname": "daily_off_spec", "fieldtype": "Currency", "width": 200},
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
    base_processing_cost = flt(tier_tariff) or 0
    element_exceeding_percentage = (flt(cod_value) / 2500) or 0
    cost_of_treating_noncompliant_water = (element_exceeding_percentage * flt(tier_tariff)) or 0
    additional_processing_cost_difference = (cost_of_treating_noncompliant_water - flt(tier_tariff)) or 0
    daily_off_spec = (additional_processing_cost_difference * flt(treated_vol)) or 0

    return [
        daily_off_spec,
        element_exceeding_percentage,
        cost_of_treating_noncompliant_water,
        additional_processing_cost_difference,
        contractual_limit_cod,
        base_processing_cost,
    ]


# ---------------------------------------------------------------------------
# Shared helpers for the print view and the Excel export - both need the
# same "who is this report for" company header info.
# ---------------------------------------------------------------------------


def get_company_info():
    default_company = frappe.defaults.get_global_default("company")
    company = {}
    if default_company:
        company = frappe.db.get_value(
            "Company", default_company, ["company_name", "company_logo"], as_dict=True
        ) or {}

    return {
        "company_name": company.get("company_name"),
        "company_logo": company.get("company_logo"),
    }


def compute_totals(columns, data):
    """Sum every Float/Currency column across the given data - the single
    source of truth for totals, shared by the print view and the Excel export
    so the two can never drift apart."""

    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Float", "Currency"):
            fieldname = col.get("fieldname")
            totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in data))
    return totals


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
    totals = compute_totals(columns, data)

    return {
        "columns": columns,
        "data": data,
        "totals": totals,
        "company": get_company_info(),
        "filters": filters,
    }


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------
# Builds an .xlsx that mirrors the branded print view: same columns, same
# data, same totals (computed once via compute_totals, exactly like
# get_print_data), same optional "Detailed + Monthly Totals" subtotal rows.
# It re-runs get_columns()/get_data() itself rather than depending on
# get_print_data, so it can also be called directly, but every number on the
# sheet comes from the exact same functions the report grid and the print
# view use - nothing is re-derived or re-summed differently here.

HM_BLUE_HEX = "FF010BCE"
HM_RED_HEX = "FFD50000"
HEADER_FILL_HEX = "FFF1F2FB"
ROW_ODD_FILL_HEX = "FFF8F9FD"
SUBTOTAL_FILL_HEX = "FFFDEAEA"


def get_excel_filename(filters, is_monthly, add_monthly_subtotals):
    if is_monthly:
        base = "Daily-Off-Spec-Report-Monthly"
    elif add_monthly_subtotals:
        base = "Daily-Off-Spec-Report-Detailed-Monthly-Totals"
    else:
        base = "Daily-Off-Spec-Report"

    from_date = filters.get("from_date") or ""
    to_date = filters.get("to_date") or ""
    return "{0}_{1}_to_{2}.xlsx".format(base, from_date, to_date)


def get_month_label_from_date(date_val):
    d = getdate(date_val).replace(day=1)
    return d.strftime("%b %Y")


def build_monthly_subtotal_groups(data):
    """Same grouping the print view's JS does client-side for the "Detailed
    + Monthly Totals" print: walks the daily rows in order and returns them
    interleaved with (position, label, vol_total, offspec_total) subtotal
    markers every time the Project + Unit + Month key changes."""

    groups = []  # list of dicts: {"rows": [...], "label": str, "vol": x, "offspec": x}
    current = None
    current_key = None

    for row in data:
        month_key = getdate(row.get("date")).strftime("%Y-%m") if row.get("date") else ""
        key = (row.get("project"), row.get("unit"), month_key)

        if key != current_key:
            if current is not None:
                groups.append(current)
            current = {
                "rows": [],
                "label": get_month_label_from_date(row.get("date")) if row.get("date") else "",
                "vol": 0.0,
                "offspec": 0.0,
            }
            current_key = key

        current["rows"].append(row)
        current["vol"] += flt(row.get("waste_water_treated_volume"))
        current["offspec"] += flt(row.get("daily_off_spec"))

    if current is not None:
        groups.append(current)

    return groups


def _col_number_format(col):
    if col.get("fieldtype") == "Currency":
        return "#,##0.00"
    if col.get("fieldtype") == "Float":
        return "0.00"
    if col.get("fieldtype") == "Int":
        return "0"
    if col.get("fieldtype") == "Date":
        return "yyyy-mm-dd"
    return "General"


def _col_alignment(col, is_arabic):
    numeric = col.get("fieldtype") in ("Float", "Currency", "Int")
    if numeric:
        return "right"
    return "right" if is_arabic else "left"


def build_workbook(columns, data, totals, filters, company, is_arabic, is_monthly, add_monthly_subtotals):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Off-Spec Report"
    if is_arabic:
        ws.sheet_view.rightToLeft = True

    n_cols = len(columns)

    title = (
        ("التقرير الشهري لمخالفة المواصفات" if is_monthly else
         "التقرير اليومي التفصيلي لمخالفة المواصفات مع إجمالي شهري" if add_monthly_subtotals else
         "التقرير اليومي لمخالفة المواصفات")
        if is_arabic else
        ("Daily Off-Spec Report (Monthly Summary)" if is_monthly else
         "Daily Off-Spec Report (Detailed, with Monthly Totals)" if add_monthly_subtotals else
         "Daily Off-Spec Report")
    )
    company_name = company.get("company_name") or ""
    period_label = "الفترة" if is_arabic else "Period"
    generated_label = "تاريخ الطباعة" if is_arabic else "Generated on"
    period_value = "{0} - {1}".format(filters.get("from_date") or "", filters.get("to_date") or "")
    generated_value = frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M")

    blue_fill = PatternFill("solid", fgColor=HM_BLUE_HEX)
    red_top_border = Border(top=Side(style="medium", color=HM_RED_HEX))
    header_fill = PatternFill("solid", fgColor=HEADER_FILL_HEX)
    row_odd_fill = PatternFill("solid", fgColor=ROW_ODD_FILL_HEX)
    subtotal_fill = PatternFill("solid", fgColor=SUBTOTAL_FILL_HEX)
    thin_border = Border(
        left=Side(style="thin", color="FFDDDDDD"),
        right=Side(style="thin", color="FFDDDDDD"),
        top=Side(style="thin", color="FFDDDDDD"),
        bottom=Side(style="thin", color="FFDDDDDD"),
    )

    white_bold = Font(color="FFFFFFFF", bold=True, size=12)
    white_regular = Font(color="FFFFFFFF", size=9)
    header_font = Font(color=HM_BLUE_HEX[2:], bold=True, size=10)  # drop leading alpha for RGB font color
    body_font = Font(size=10)
    bold_font = Font(size=10, bold=True)

    row_num = 1

    # Row 1: company + title, on the HM blue brand bar
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=n_cols)
    cell = ws.cell(row=row_num, column=1, value="{0} - {1}".format(company_name, title) if company_name else title)
    cell.font = white_bold
    cell.fill = blue_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row_num].height = 26
    row_num += 1

    # Row 2: period / generated-on meta, still on the brand bar
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=n_cols)
    meta_text = "{0}: {1}    |    {2}: {3}".format(period_label, period_value, generated_label, generated_value)
    cell = ws.cell(row=row_num, column=1, value=meta_text)
    cell.font = white_regular
    cell.fill = blue_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row_num].height = 16
    row_num += 1

    header_row_num = row_num
    for col_idx, col in enumerate(columns, start=1):
        cell = ws.cell(row=header_row_num, column=col_idx, value=str(col.get("label") or ""))
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(
            horizontal=_col_alignment(col, is_arabic), vertical="center", wrap_text=True
        )
    ws.row_dimensions[header_row_num].height = 26
    row_num += 1

    def write_data_row(r, row_data, zebra_odd, bold=False):
        for col_idx, col in enumerate(columns, start=1):
            fieldname = col.get("fieldname")
            raw = row_data.get(fieldname)
            cell = ws.cell(row=r, column=col_idx, value=(flt(raw) if col.get("fieldtype") in ("Float", "Currency", "Int") and raw not in (None, "") else (raw if raw not in (None, "") else None)))
            cell.font = bold_font if bold else body_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal=_col_alignment(col, is_arabic), vertical="center")
            if col.get("fieldtype") in ("Float", "Currency", "Int") and raw not in (None, ""):
                cell.number_format = _col_number_format(col)
            if zebra_odd:
                cell.fill = row_odd_fill

    def write_subtotal_row(r, label, vol_total, offspec_total):
        qty_field = "waste_water_treated_volume"
        offspec_field = "daily_off_spec"
        label_col_end = max(
            next((i for i, c in enumerate(columns, start=1) if c.get("fieldname") == qty_field), 2) - 1, 1
        )
        if label_col_end > 1:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=label_col_end)
        cell = ws.cell(row=r, column=1, value=label)
        cell.font = bold_font
        cell.fill = subtotal_fill
        cell.border = red_top_border
        cell.alignment = Alignment(horizontal="right" if is_arabic else "left", vertical="center")

        for col_idx, col in enumerate(columns, start=1):
            if col_idx <= label_col_end:
                if col_idx > 1:
                    c = ws.cell(row=r, column=col_idx)
                    c.fill = subtotal_fill
                    c.border = red_top_border
                continue
            fieldname = col.get("fieldname")
            c = ws.cell(row=r, column=col_idx)
            c.fill = subtotal_fill
            c.border = red_top_border
            c.font = bold_font
            if fieldname == qty_field:
                c.value = flt(vol_total)
                c.number_format = _col_number_format(col)
                c.alignment = Alignment(horizontal="right", vertical="center")
            elif fieldname == offspec_field:
                c.value = flt(offspec_total)
                c.number_format = _col_number_format(col)
                c.alignment = Alignment(horizontal="right", vertical="center")

    if add_monthly_subtotals and not is_monthly:
        groups = build_monthly_subtotal_groups(data)
        zebra_idx = 0
        for group in groups:
            for row_data in group["rows"]:
                write_data_row(row_num, row_data, zebra_odd=(zebra_idx % 2 == 1))
                zebra_idx += 1
                row_num += 1
            label = ("إجمالي - " if is_arabic else "Total - ") + group["label"]
            write_subtotal_row(row_num, label, group["vol"], group["offspec"])
            row_num += 1
    else:
        for idx, row_data in enumerate(data):
            write_data_row(row_num, row_data, zebra_odd=(idx % 2 == 1))
            row_num += 1

    # Grand total row - once, at the true end, same fields as the print view
    # (waste_water_treated_volume + daily_off_spec), computed via compute_totals.
    total_label_col = max(
        next((i for i, c in enumerate(columns, start=1) if c.get("fieldname") == "waste_water_treated_volume"), 2) - 1,
        1,
    )
    if total_label_col > 1:
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=total_label_col)
    cell = ws.cell(row=row_num, column=1, value=("الإجمالي" if is_arabic else "Total"))
    cell.font = bold_font
    cell.fill = header_fill
    cell.border = red_top_border
    cell.alignment = Alignment(horizontal="right" if is_arabic else "left", vertical="center")

    for col_idx, col in enumerate(columns, start=1):
        c = ws.cell(row=row_num, column=col_idx)
        c.fill = header_fill
        c.border = red_top_border
        c.font = bold_font
        if col_idx <= total_label_col:
            continue
        fieldname = col.get("fieldname")
        if totals and fieldname in totals and fieldname in ("waste_water_treated_volume", "daily_off_spec"):
            c.value = flt(totals[fieldname])
            c.number_format = _col_number_format(col)
            c.alignment = Alignment(horizontal="right", vertical="center")

    # Column widths - roughly translate the report's pixel widths to Excel's
    # character-width units (~7px per unit), with sane min/max bounds.
    for col_idx, col in enumerate(columns, start=1):
        px_width = col.get("width") or 100
        excel_width = max(10, min(45, round(px_width / 7)))
        ws.column_dimensions[get_column_letter(col_idx)].width = excel_width

    ws.freeze_panes = ws.cell(row=header_row_num + 1, column=1)

    return wb


@frappe.whitelist()
def get_excel(filters=None, add_monthly_subtotals=0):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)
    add_monthly_subtotals = cint(add_monthly_subtotals)

    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)
    totals = compute_totals(columns, data)

    is_arabic = bool(filters.get("show_arabic_report"))
    is_monthly = bool(filters.get("group_by_month"))
    company = get_company_info()

    if not data:
        frappe.throw(_("No data to export. Please adjust your filters."))

    from io import BytesIO

    wb = build_workbook(
        columns,
        data,
        totals,
        filters,
        company,
        is_arabic,
        is_monthly,
        add_monthly_subtotals and not is_monthly,
    )

    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)

    frappe.response["filename"] = get_excel_filename(filters, is_monthly, add_monthly_subtotals)
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"] = "binary"