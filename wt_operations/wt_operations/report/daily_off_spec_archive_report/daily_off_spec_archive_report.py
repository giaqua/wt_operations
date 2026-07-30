# Copyright (c) 2026, HM
# For license information, please see license.txt
#
# Report: Daily Off-Spec Archive Report
#
# Same tiered off-spec COD calculation as "Daily Off-Spec Report", but sourced
# directly from "Daily Operation Report Archive" records instead of joining
# Daily Operation Report + Project Operation Water Sample. Only two fields are
# read from the Archive doctype to drive the calculation itself:
#   - inlet_treated_vol  -> treated volume (m3)
#   - cod                -> inlet COD value used for the tiered tariff lookup
#
# Assumptions (adjust fieldnames below if your schema differs):
#   1. "Daily Operation Report Archive" has a "project" Link field (to Project)
#      used to look up the applicable Off-Spec COD Invoice Calculator record -
#      same as the live report. Confirmed present, just not in the sample
#      JSON you shared.
#   2. Off-Spec COD Invoice Calculator has a "project" Link field (one record
#      per project, versioned by effective_from). The record with the latest
#      effective_from <= row date is used for that row's calculation.
#   3. No docstatus filtering is applied by default, since Archive rows may
#      not follow a submit workflow (the sample record had docstatus 0). Add
#      a docstatus filter in get_data() below if you need one.
#   4. Any other fields on the Archive doctype (ph, tss, turbidity,
#      oil_and_grease, or its own pre-stored daily_offspec_amount etc.) are
#      intentionally ignored - this report recalculates from cod +
#      inlet_treated_vol only, per your request, rather than trusting
#      whatever was stored on the archive record at the time.

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))


def get_columns(filters):
    is_arabic = bool(filters.get("show_arabic_report"))

    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("QTY m3"), "fieldname": "inlet_treated_vol", "fieldtype": "Float", "width": 120},
        {"label": _("COD"), "fieldname": "cod", "fieldtype": "Float", "width": 110},
    ]
    if filters.get("show_other_info"):
        columns = [
				{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
				{
					"label": _("Archive Record"),
					"fieldname": "name",
					"fieldtype": "Link",
					"options": "Daily Operation Report Archive",
					"width": 130,
				},
				{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
				{"label": _("QTY m3"), "fieldname": "inlet_treated_vol", "fieldtype": "Float", "width": 120},
				{"label": _("COD"), "fieldname": "cod", "fieldtype": "Float", "width": 110},
			]

    if is_arabic:
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

    return columns


def get_data(filters):
    archive_filters = {
        "date": ["between", [filters.get("from_date"), filters.get("to_date")]],
    }
    if filters.get("project"):
        archive_filters["project"] = filters.get("project")

    archive_list = frappe.get_all(
        "Daily Operation Report Archive",
        filters=archive_filters,
        fields=["name", "project", "date", "inlet_treated_vol", "cod"],
        order_by="project, date",
    )

    if not archive_list:
        return []

    settings_cache = {}  # project -> list of Off-Spec settings, sorted by effective_from desc
    tier_cache = {}  # settings doc name -> list of tier rows

    data = []

    for arc in archive_list:
        row = {
            "name": arc.name,
            "project": arc.project,
            "date": arc.date,
            "inlet_treated_vol": arc.inlet_treated_vol,
            "cod": arc.cod,
        }

        daily_off_spec_values = calculate_daily_off_spec(
            arc.project,
            arc.date,
            arc.inlet_treated_vol,
            arc.cod,
            settings_cache,
            tier_cache,
        )

        row["element_exceeding_percentage"] = daily_off_spec_values[1]
        row["cost_of_treating_noncompliant_water"] = round(daily_off_spec_values[2], 2)
        row["additional_processing_cost_difference"] = round(daily_off_spec_values[3], 2)
        row["contractual_limit_cod"] = round(daily_off_spec_values[4], 2)
        row["base_processing_cost"] = round(daily_off_spec_values[5], 2)
        row["daily_off_spec"] = daily_off_spec_values[0]

        data.append(row)

    return data


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
        return [0, 0, 0, 0, 0, 0]

    setting = get_applicable_settings(project, date, settings_cache)
    if not setting:
        return [0, 0, 0, 0, 0, 0]

    baseline = flt(setting.contractual_cod_baseline_m1ppm)
    if not baseline:
        return [0, 0, 0, 0, 0, 0]

    tier = get_tier_row(setting.name, cod_value, tier_cache)
    if not tier:
        return [0, 0, 0, 0, 0, 0]

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
# Print support (server is the single source of truth - see the sibling
# Daily Off-Spec Report for the rationale)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_print_data(filters=None):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns(filters)
    data = get_data(filters)

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