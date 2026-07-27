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
#   4. No docstatus filtering is applied (draft + submitted rows are both included).
#      Add docstatus filters below if you only want submitted records.
#   5. If "Sample Process Location" or "Result Type" filters are set, only rows with a
#      matching water sample are shown (rows with no matching sample are dropped).
#
# Extra filters:
#   - show_daily_report / show_water_sample / show_sample_process_location (Check):
#     toggle optional columns on/off.
#   - sample_process_location (Data): filters rows by a case-insensitive partial match
#     against the water sample's Sample Process Location. Rows without a matching
#     water sample are excluded when this filter is set.

import frappe
from frappe import _
from frappe.utils import flt, getdate

ALL_PARAMETERS = ["COD", "pH", "TSS", "Turbidity.", "TDS."]


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
    columns = [
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
        # {"label": _("Unit"), "fieldname": "unit", "fieldtype": "Data", "width": 130},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
    ]

    if filters.get("show_daily_report"):
        columns.append(
            {
                "label": _("Daily Report"),
                "fieldname": "daily_report",
                "fieldtype": "Link",
                "options": "Daily Operation Report",
                "width": 150,
            }
        )

    if filters.get("show_water_sample"):
        columns.append(
            {
                "label": _("Water Sample"),
                "fieldname": "water_sample",
                "fieldtype": "Link",
                "options": "Project Operation Water Sample",
                "width": 150,
            }
        )

    # if filters.get("show_sample_process_location"):
    #     columns.append(
    #         {
    #             "label": _("Sample Process Location"),
    #             "fieldname": "sample_process_location",
    #             "fieldtype": "Data",
    #             "width": 160,
    #         }
    #     )

    columns.append(
        {
            "label": _("Waste Water Treated Vol. (m³)"),
            "fieldname": "waste_water_treated_volume",
            "fieldtype": "Float",
            "width": 170,
        }
    )

    selected_parameters = filters.get("parameter")
    if selected_parameters and isinstance(selected_parameters, str):
        # comes in as JSON-stringified list or comma separated from MultiSelectList
        selected_parameters = frappe.parse_json(selected_parameters) if selected_parameters.startswith("[") else selected_parameters.split(",")

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

    if filters.get("show_sample_process_location"):
        columns.append(
            {
                "label": _("Sample Process Location"),
                "fieldname": "sample_process_location",
                "fieldtype": "Data",
                "width": 160,
            }
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

    data = []

    for dor in dor_list:
        row = {
            "project": dor.project,
            "unit": dor.unit,
            "date": dor.date,
            "waste_water_treated_volume": dor.waste_water_treated_volume,
        }

        pws = get_matching_sample(dor, filters)

        # If the user filtered by Sample Process Location or Result Type,
        # only keep rows that actually have a matching sample.
        if not pws and (filters.get("sample_process_location") or filters.get("result_type")):
            continue

        param_values = {}
        if pws:
            sample_rows = frappe.get_all(
                "Sample Collection Details",
                filters={"parent": pws.name, "parenttype": "Project Operation Water Sample"},
                fields=["parameter", "inlet"],
            )
            for sr in sample_rows:
                param_values[sr.parameter] = flt(sr.inlet)

        for param in parameters:
            row[param_to_fieldname(param)] = param_values.get(param)

        if filters.get("show_daily_report"):
            row["daily_report"] = dor.name

        if filters.get("show_water_sample"):
            row["water_sample"] = pws.name if pws else None

        if filters.get("show_sample_process_location"):
            row["sample_process_location"] = pws.sample_process_location if pws else None

        cod_value = param_values.get("COD")
        row["daily_off_spec"] = calculate_daily_off_spec(
            dor.project,
            dor.date,
            dor.waste_water_treated_volume,
            cod_value,
            settings_cache,
            tier_cache,
        )

        data.append(row)

    return data


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
    return flt(treated_vol) * (flt(cod_value) / baseline) * tier_tariff