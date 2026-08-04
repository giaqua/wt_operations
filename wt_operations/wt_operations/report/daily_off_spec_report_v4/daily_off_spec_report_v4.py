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
#     since a Daily Operation Report / Water Sample no longer maps 1:1 to a row.
#   - sample_process_location (Data): filters rows by a case-insensitive partial match
#     against the water sample's Sample Process Location. Rows without a matching
#     water sample are excluded when this filter is set.
#   - group_by_month (Check): turns the report into a Trial-Balance-style
#     collapsible tree. Each row is a Month (Project + Unit + Month), collapsed
#     by default, showing the month's totals. Expanding a month row reveals the
#     individual Daily Operation Report rows that were rolled into it.
#       - waste_water_treated_volume / daily_off_spec on the month row: SUMMED
#         from its daily children
#       - parameter readings (COD, pH, TSS, ...) on the month row: volume-weighted
#         average of the daily children
#       - tariff/settings-derived fields on the month row: simple average of the
#         daily children
#       - the daily child rows keep their own actual (unaggregated) values

import frappe
from frappe import _
from frappe.utils import flt, getdate

ALL_PARAMETERS = ["COD", "pH", "TSS", "Turbidity.", "TDS."]

# Settings/tariff-derived fields that get averaged (not summed) on month rows
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
    # Tree-configured script reports (tree: true / name_field / parent_field
    # in report.js) can trigger an initial query_report.run call before the
    # report's own filter defaults have been applied client-side, arriving
    # here with from_date/to_date empty. Rather than hard-throw and break
    # that call, fall back to a sensible default window (last 1 month) so
    # the report still renders something - it re-runs correctly once your
    # actual filter values are sent.
    if not filters.get("from_date") or not filters.get("to_date"):
        filters["to_date"] = filters.get("to_date") or frappe.utils.today()
        filters["from_date"] = filters.get("from_date") or frappe.utils.add_months(filters["to_date"], -1)

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
        # Unit isn't shown normally, but once rows are grouped into a tree it's
        # the only thing distinguishing separate month-branches for one project.
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
        # The tree/expand column: month rows show "Jan 2026", daily child rows
        # (once expanded) show their actual date. See report.js: this is the
        # configured name_field, and its display value is overridden there.
        columns.append({"label": _("Month / Date"), "fieldname": "particulars", "fieldtype": "Data", "width": 160})

        # These carry the tree wiring (parent link, pretty label, group/indent
        # flags) that report.js's formatter reads. They MUST be declared as
        # real columns - Frappe's normalize_result() step drops any row key
        # that isn't a declared column fieldname, which is why these were
        # coming back as `undefined` in the browser before being added here.
        columns.append({"label": _("Display Label"), "fieldname": "display_label", "fieldtype": "Data", "hidden": 1})
        columns.append({"label": _("Parent"), "fieldname": "parent_particulars", "fieldtype": "Data", "hidden": 1})
        columns.append({"label": _("Is Group"), "fieldname": "is_group", "fieldtype": "Check", "hidden": 1})
        columns.append({"label": _("Indent"), "fieldname": "indent", "fieldtype": "Int", "hidden": 1})
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

    if group_by_month:
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

    daily_rows = []

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

        daily_rows.append(row)

    if filters.get("group_by_month"):
        return build_monthly_tree(daily_rows, parameters)

    return daily_rows


def build_monthly_tree(daily_rows, parameters):
    """Build a Trial-Balance-style tree: one collapsible row per
    Project + Unit + Month (the totals), each with its underlying daily rows
    as children (only visible once the month row is expanded in the UI).

    Tree linkage uses "particulars" (unique per row) / "parent_particulars"
    (the parent's "particulars" value) - see report.js `name_field` /
    `parent_field` config, mirroring how core reports like Trial Balance /
    Inventory Balance implement their collapsible tree views.
    """
    param_fieldnames = [param_to_fieldname(p) for p in parameters]

    groups = {}
    order = []  # preserves first-seen (project, unit, month) order

    for row in daily_rows:
        date = row["date"]
        month_dt = getdate(date).replace(day=1)
        month_sort_key = month_dt.strftime("%Y-%m")
        month_label = month_dt.strftime("%b %Y")

        project = row.get("project")
        unit = row.get("unit")
        key = (project, unit, month_sort_key)

        if key not in groups:
            particulars_key = "{0}::{1}::{2}".format(project or "", unit or "", month_sort_key)
            groups[key] = {
                "particulars_key": particulars_key,
                "month_label": month_label,
                "project": project,
                "unit": unit,
                "waste_water_treated_volume": 0.0,
                "daily_off_spec": 0.0,
                "days_count": 0,
                "_param_weighted_sum": {f: 0.0 for f in param_fieldnames},
                "_param_weight": {f: 0.0 for f in param_fieldnames},
                "_settings_sum": {f: 0.0 for f in SETTINGS_DERIVED_FIELDS},
                "_settings_count": {f: 0 for f in SETTINGS_DERIVED_FIELDS},
                "children": [],
            }
            order.append(key)

        g = groups[key]
        vol = flt(row.get("waste_water_treated_volume"))
        weight = vol if vol else 1.0

        g["waste_water_treated_volume"] += vol
        g["daily_off_spec"] += flt(row.get("daily_off_spec"))
        g["days_count"] += 1

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

        child = {
            "particulars": "{0}::{1}".format(g["particulars_key"], date),
            "parent_particulars": g["particulars_key"],
            "display_label": getdate(date).strftime("%d %b %Y"),
            "is_group": 0,
            "indent": 1,
            "project": project,
            "unit": unit,
            "waste_water_treated_volume": row.get("waste_water_treated_volume"),
            "daily_off_spec": row.get("daily_off_spec"),
            "days_count": None,
        }
        for f in param_fieldnames:
            child[f] = row.get(f)
        for f in SETTINGS_DERIVED_FIELDS:
            child[f] = row.get(f)

        g["children"].append(child)

    tree_rows = []
    for key in order:
        g = groups[key]
        group_row = {
            "particulars": g["particulars_key"],
            "parent_particulars": "",
            "display_label": g["month_label"],
            "is_group": 1,
            "indent": 0,
            "project": g["project"],
            "unit": g["unit"],
            "waste_water_treated_volume": round(g["waste_water_treated_volume"], 2),
            "daily_off_spec": round(g["daily_off_spec"], 2),
            "days_count": g["days_count"],
        }

        for f in param_fieldnames:
            w = g["_param_weight"][f]
            group_row[f] = round(g["_param_weighted_sum"][f] / w, 2) if w else None

        for f in SETTINGS_DERIVED_FIELDS:
            n = g["_settings_count"][f]
            group_row[f] = round(g["_settings_sum"][f] / n, 2) if n else None

        tree_rows.append(group_row)
        tree_rows.extend(sorted(g["children"], key=lambda c: c["particulars"]))

    return tree_rows


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
# Print support
# ---------------------------------------------------------------------------
# This is the single source of truth for the print view: it re-runs the exact
# same execute()/get_data() logic used by the report grid (including the
# month/day tree when group_by_month is set), then computes the column totals
# ONCE, server-side, directly from that data list. The client (report.js) no
# longer re-derives or re-sums anything - it just renders whatever this
# method returns.
#
# IMPORTANT: when group_by_month is set, `data` contains BOTH the month rows
# (is_group=1) AND their daily children (is_group=0) so the tree can expand.
# Totals must only be computed from the month (is_group) rows, or the daily
# children would be double-counted on top of the month totals they already
# feed into. `row.get("is_group", 1)` defaults to True for the ordinary
# (non-grouped) flat mode, where every row should count as before.


@frappe.whitelist()
def get_print_data(filters=None):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)

    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)

    rows_for_totals = [row for row in data if row.get("is_group", 1)]

    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Float", "Currency"):
            fieldname = col.get("fieldname")
            totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in rows_for_totals))

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