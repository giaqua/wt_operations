# Copyright (c) 2026, HM
# For license information, please see license.txt
#
# Report: Daily Off-Spec Report
# Combines:
#   - Daily Operation Report (project, unit, date, waste_water_treated_volume,
#     energy_consumtion, running_hours)
#   - Project Operation Water Sample -> Sample Collection Details
#     (per-parameter values; each Water Sample doc is single-source, tagged
#     by its own `water_source` field = "Inlet" or "Outlet", matched to a
#     DOR by site == project and sampling_date == date)
#   - Chemical Usage Table (per-DOR chemical qty, one column per selected
#     chemical, either "as used" or "after density" qty)
#   - Off-Spec COD Invoice Calculator (+ Tier Tariff Structure child) for the
#     Daily Off-Spec calc - always keyed off the INLET sample's COD value,
#     independent of the Water Source display filter.
#
# Filters:
#   - water_source (Select: "", "Inlet", "Outlet"): "" means show both Inlet
#     and Outlet parameter blocks; "Inlet"/"Outlet" shows only that block.
#   - parameter (MultiSelectList): which parameters to show in the INLET
#     block. The OUTLET block always shows all parameters regardless of this
#     filter (outlet is the "permitted" check, so it's always shown in full).
#   - chemicals (MultiSelectList): which chemicals get their own qty column.
#     Empty selection = no chemical columns.
#   - show_chemical_density_qty (Check): if set, chemical qty columns use
#     `chemical_quantity_used_kg_after_dansity` instead of
#     `chemical_quantity_used_kg`.
#   - hide_calculation_amount_columns (Check): hides the whole off-spec calc
#     block (element_exceeding_percentage, cost_of_treating_noncompliant_water,
#     additional_processing_cost_difference, contractual_limit_cod,
#     base_processing_cost, daily_off_spec). The underlying calculation still
#     runs (kept internally) even when the columns are hidden.
#   - group_by_month (Check): collapses daily rows into one row per
#     Project + Unit + Month. Volumes / daily_off_spec / running_hours /
#     chemical qty: summed. Parameter readings (inlet + outlet): volume-
#     weighted averaged. Tariff/settings-derived fields + energy_consumtion:
#     simple-averaged across the days included in that month.

import frappe
from frappe import _
from frappe.utils import flt, getdate

ALL_PARAMETERS = ["COD", "pH", "TSS", "Turbidity.", "TDS."]

# Settings/tariff-derived fields that get averaged (not summed) when grouping monthly
SETTINGS_DERIVED_FIELDS = [
    "element_exceeding_percentage",
    "cost_of_treating_noncompliant_water",
    "additional_processing_cost_difference",
    "contractual_limit_cod",
    "base_processing_cost",
]

CHEMICAL_QTY_FIELD = "chemical_quantity_used_kg"
CHEMICAL_QTY_FIELD_DENSITY = "chemical_quantity_used_kg_after_dansity"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns, ctx = get_columns(filters)
    data = get_data(filters, ctx)

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))


def param_to_fieldname(param, prefix=""):
    base = param.strip().rstrip(".").lower().replace(" ", "_").replace(".", "")
    return f"{prefix}{base}" if prefix else base


def chemical_to_fieldname(chemical):
    slug = "".join(ch if ch.isalnum() else "_" for ch in (chemical or "").strip().lower())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return "chem_{0}".format(slug.strip("_") or "unknown")


def get_selected_parameters(filters):
    selected_parameters = filters.get("parameter")
    if selected_parameters and isinstance(selected_parameters, str):
        selected_parameters = (
            frappe.parse_json(selected_parameters)
            if selected_parameters.startswith("[")
            else selected_parameters.split(",")
        )
    return selected_parameters or list(ALL_PARAMETERS)


def get_selected_chemicals(filters):
    chemicals = filters.get("chemicals")
    if chemicals and isinstance(chemicals, str):
        chemicals = (
            frappe.parse_json(chemicals) if chemicals.startswith("[") else chemicals.split(",")
        )
    return chemicals or []


def get_columns(filters):
    group_by_month = bool(filters.get("group_by_month"))
    water_source = (filters.get("water_source") or "").strip()  # "", "Inlet", "Outlet"
    show_inlet = water_source in ("", "Inlet")
    show_outlet = water_source in ("", "Outlet")
    hide_calc = bool(filters.get("hide_calculation_amount_columns"))
    show_density = bool(filters.get("show_chemical_density_qty"))

    inlet_parameters = get_selected_parameters(filters) if show_inlet else []
    # Outlet always shows ALL parameters - it's the "permitted" check,
    # so the `parameter` filter (which narrows Inlet) doesn't apply here.
    outlet_parameters = list(ALL_PARAMETERS) if show_outlet else []
    selected_chemicals = get_selected_chemicals(filters)

    columns = []
    if not filters.get("show_arabic_report"):
        columns = [
            {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
        ]

    if group_by_month:
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
                    "label": _("Water Sample") + (_(" (Inlet)") if show_inlet and show_outlet else ""),
                    "fieldname": "water_sample",
                    "fieldtype": "Link",
                    "options": "Project Operation Water Sample",
                    "width": 130,
                }
            )
            if show_inlet and show_outlet:
                columns.append(
                    {
                        "label": _("Water Sample (Outlet)"),
                        "fieldname": "water_sample_outlet",
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
    elif not group_by_month and filters.get("show_sample_process_location"):
        columns.append(
            {
                "label": _("Sample Process Location"),
                "fieldname": "sample_process_location",
                "fieldtype": "Data",
                "width": 160,
            }
        )

    # Energy Consumption / Running Hours - always shown
    columns.append(
        {"label": _("Energy Consumption"), "fieldname": "energy_consumtion", "fieldtype": "Float", "precision": 4, "width": 130}
    )
    columns.append(
        {"label": _("Running Hours"), "fieldname": "running_hours", "fieldtype": "Float", "precision": 1, "width": 110}
    )

    # Inlet parameter columns (filtered by "parameter")
    for param in inlet_parameters:
        columns.append(
            {
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param, "in_"),
                "fieldtype": "Float",
                "width": 110,
                "water_group": "inlet",
            }
        )

    # Outlet parameter columns - always ALL_PARAMETERS
    for param in outlet_parameters:
        columns.append(
            {
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param, "out_"),
                "fieldtype": "Float",
                "width": 110,
                "water_group": "outlet",
            }
        )

    # Chemical usage qty columns - one per selected chemical
    density_suffix = " " + str(_("(after density)")) if show_density else ""
    for chemical in selected_chemicals:
        columns.append(
            {
                "label": "{0} {1}{2}".format(chemical, _("Qty (kg)"), density_suffix),
                "fieldname": chemical_to_fieldname(chemical),
                "fieldtype": "Float",
                "precision": 2,
                "width": 140,
                "chemical_group": True,
            }
        )

    if not hide_calc:
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

    ctx = frappe._dict(
        {
            "group_by_month": group_by_month,
            "show_inlet": show_inlet,
            "show_outlet": show_outlet,
            "hide_calc": hide_calc,
            "show_density": show_density,
            "inlet_parameters": inlet_parameters,
            "outlet_parameters": outlet_parameters,
            "selected_chemicals": selected_chemicals,
        }
    )

    return columns, ctx


def get_data(filters, ctx):
    dor_filters = {
        "date": ["between", [filters.get("from_date"), filters.get("to_date")]],
        "docstatus": 1,
    }
    if filters.get("project"):
        dor_filters["project"] = filters.get("project")
    if filters.get("unit"):
        dor_filters["unit"] = filters.get("unit")
    if filters.get("hide_zero_off_spec_rows"):
        dor_filters["waste_water_treated_volume"] = [">", 0]

    dor_list = frappe.get_all(
        "Daily Operation Report",
        filters=dor_filters,
        fields=[
            "name",
            "project",
            "unit",
            "date",
            "waste_water_treated_volume",
            "energy_consumtion",
            "running_hours",
        ],
        order_by="project, unit, date",
    )

    if not dor_list:
        return []

    settings_cache = {}
    tier_cache = {}

    data = []

    for dor in dor_list:
        row = {
            "project": dor.project,
            "unit": dor.unit,
            "date": dor.date,
            "waste_water_treated_volume": dor.waste_water_treated_volume,
            "energy_consumtion": dor.energy_consumtion,
            "running_hours": dor.running_hours,
        }

        inlet_sample = None
        outlet_sample = None

        # Fetch Inlet sample whenever it's displayed OR whenever the off-spec
        # calc needs COD (calc always keys off Inlet, even if display is
        # Outlet-only).
        if ctx.show_inlet or not ctx.hide_calc:
            inlet_sample = get_matching_sample(dor, filters, "Inlet")

        if ctx.show_outlet:
            outlet_sample = get_matching_sample(dor, filters, "Outlet")

        inlet_values = get_sample_param_values(inlet_sample, dor.waste_water_treated_volume)
        outlet_values = get_sample_param_values(outlet_sample, dor.waste_water_treated_volume)

        for param in ctx.inlet_parameters:
            row[param_to_fieldname(param, "in_")] = inlet_values.get(param)

        for param in ctx.outlet_parameters:
            row[param_to_fieldname(param, "out_")] = outlet_values.get(param)

        if filters.get("show_daily_report"):
            row["daily_report"] = dor.name

        if filters.get("show_water_sample"):
            row["water_sample"] = inlet_sample.name if inlet_sample else (outlet_sample.name if outlet_sample else None)
            if ctx.show_inlet and ctx.show_outlet:
                row["water_sample_outlet"] = outlet_sample.name if outlet_sample else None

        if not ctx.group_by_month and filters.get("show_sample_process_location"):
            sample_for_location = inlet_sample or outlet_sample
            row["sample_process_location"] = (
                sample_for_location.sample_process_location if sample_for_location else None
            )

        # Chemical usage qty columns
        if ctx.selected_chemicals:
            chem_rows = frappe.get_all(
                "Chemical Usage Table",
                filters={
                    "parent": dor.name,
                    "parenttype": "Daily Operation Report",
                    "chemical": ["in", ctx.selected_chemicals],
                },
                fields=["chemical", CHEMICAL_QTY_FIELD, CHEMICAL_QTY_FIELD_DENSITY],
            )
            chem_by_name = {c.chemical: c for c in chem_rows}
            for chemical in ctx.selected_chemicals:
                c = chem_by_name.get(chemical)
                if c:
                    qty = c.get(CHEMICAL_QTY_FIELD_DENSITY) if ctx.show_density else c.get(CHEMICAL_QTY_FIELD)
                else:
                    qty = None
                row[chemical_to_fieldname(chemical)] = qty

        # Off-spec calculation - always driven by the Inlet sample's COD.
        cod_value = inlet_values.get("COD")
        daily_off_spec_values = calculate_daily_off_spec(
            dor.project,
            dor.date,
            dor.waste_water_treated_volume,
            cod_value,
            settings_cache,
            tier_cache,
        ) or [0, 0, 0, 0, 0, 0]

        row["element_exceeding_percentage"] = daily_off_spec_values[1]
        row["cost_of_treating_noncompliant_water"] = round(daily_off_spec_values[2], 2)
        row["additional_processing_cost_difference"] = round(daily_off_spec_values[3], 2)
        row["contractual_limit_cod"] = round(daily_off_spec_values[4], 2)
        row["base_processing_cost"] = round(daily_off_spec_values[5], 2)
        row["daily_off_spec"] = daily_off_spec_values[0]

        data.append(row)

    if filters.get("group_by_month"):
        data = group_data_by_month(data, ctx)

    return data


def group_data_by_month(rows, ctx):
    """Collapse daily rows into one row per Project + Unit + Month.

    - waste_water_treated_volume, daily_off_spec, running_hours, chemical
      qty columns: summed
    - parameter readings (inlet + outlet): volume-weighted average
    - tariff/settings-derived fields, energy_consumtion: simple average
      across days present
    """
    param_fieldnames = [param_to_fieldname(p, "in_") for p in ctx.inlet_parameters] + [
        param_to_fieldname(p, "out_") for p in ctx.outlet_parameters
    ]
    chem_fieldnames = [chemical_to_fieldname(c) for c in ctx.selected_chemicals]

    groups = {}
    order = []

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
                "running_hours": 0.0,
                "_energy_sum": 0.0,
                "_energy_count": 0,
                "_param_weighted_sum": {f: 0.0 for f in param_fieldnames},
                "_param_weight": {f: 0.0 for f in param_fieldnames},
                "_settings_sum": {f: 0.0 for f in SETTINGS_DERIVED_FIELDS},
                "_settings_count": {f: 0 for f in SETTINGS_DERIVED_FIELDS},
                "_chem_sum": {f: 0.0 for f in chem_fieldnames},
                "_chem_count": {f: 0 for f in chem_fieldnames},
            }
            order.append(key)

        g = groups[key]
        vol = flt(row.get("waste_water_treated_volume"))
        weight = vol if vol else 1.0

        g["waste_water_treated_volume"] += vol
        g["days_count"] += 1
        g["daily_off_spec"] += flt(row.get("daily_off_spec"))
        g["running_hours"] += flt(row.get("running_hours"))

        if row.get("energy_consumtion") is not None:
            g["_energy_sum"] += flt(row.get("energy_consumtion"))
            g["_energy_count"] += 1

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

        for f in chem_fieldnames:
            val = row.get(f)
            if val is not None:
                g["_chem_sum"][f] += flt(val)
                g["_chem_count"][f] += 1

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
            "running_hours": round(g["running_hours"], 2),
            "energy_consumtion": round(g["_energy_sum"] / g["_energy_count"], 4) if g["_energy_count"] else None,
        }

        for f in param_fieldnames:
            w = g["_param_weight"][f]
            out[f] = round(g["_param_weighted_sum"][f] / w, 2) if w else None

        for f in SETTINGS_DERIVED_FIELDS:
            n = g["_settings_count"][f]
            out[f] = round(g["_settings_sum"][f] / n, 2) if n else None

        for f in chem_fieldnames:
            n = g["_chem_count"][f]
            out[f] = round(g["_chem_sum"][f], 2) if n else None

        grouped_rows.append(out)

    grouped_rows.sort(
        key=lambda r: (r.get("project") or "", r.get("unit") or "", r.get("_month_sort") or "")
    )
    for r in grouped_rows:
        r.pop("_month_sort", None)

    return grouped_rows


def get_matching_sample(dor, filters, water_source):
    """Find the single-source Project Operation Water Sample for this DOR's
    project + date + water_source ("Inlet" or "Outlet")."""

    pws_filters = {
        "site": dor.project,
        "sampling_date": dor.date,
        "water_source": water_source,
    }
    if filters.get("sample_process_location"):
        pws_filters["sample_process_location"] = ["like", "%{0}%".format(filters.get("sample_process_location"))]
    if filters.get("result_type"):
        pws_filters["result_type"] = ["like", "%{0}%".format(filters.get("result_type"))]

    samples = frappe.get_all(
        "Project Operation Water Sample",
        filters=pws_filters,
        fields=["name", "sample_process_location", "result_type"],
        order_by="modified desc",
        limit_page_length=1,
    )
    return samples[0] if samples else None


def get_sample_param_values(sample, treated_vol):
    if not sample:
        return {}

    sample_rows = frappe.get_all(
        "Sample Collection Details",
        filters={"parent": sample.name, "parenttype": "Project Operation Water Sample"},
        fields=["parameter", "inlet"],
    )
    # NOTE: the child table field is always literally named "inlet" - that's
    # just the DocField name on Sample Collection Details, and it holds the
    # sampled value whether the parent doc's water_source is Inlet or Outlet.
    return {r.parameter: (flt(r.inlet) if treated_vol else 0) for r in sample_rows}


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


@frappe.whitelist()
def get_print_data(filters=None):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)

    columns, ctx = get_columns(filters)
    data = get_data(filters, ctx)

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


@frappe.whitelist()
def get_chemical_list(txt=None):
    """Distinct chemical names across all DOR Chemical Usage Table rows -
    powers the "Chemicals" MultiSelectList filter."""
    chemicals = frappe.get_all(
        "Chemical Usage Table",
        filters={"parenttype": "Daily Operation Report"},
        fields=["chemical"],
        distinct=True,
        order_by="chemical asc",
    )
    names = [c.chemical for c in chemicals if c.chemical]
    if txt:
        names = [n for n in names if txt.lower() in n.lower()]
    return names