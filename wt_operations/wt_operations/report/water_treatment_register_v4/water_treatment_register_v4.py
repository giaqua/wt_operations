# Copyright (c) 2026, HM
# For license information, please see license.txt
#
# Report: Water Treatment Register
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
#   - hide_zero_qty_chemical_columns (Check, default on): after the report
#     data is built, any chemical qty column whose total across ALL returned
#     rows is 0 (or entirely None) gets dropped from the column list. This
#     runs after `chemicals`/`show_chemicals` resolve which chemicals are
#     candidates in the first place - it only prunes columns that made it
#     into the report but never actually had any usage in the selected
#     date range/project/unit. The underlying row data is untouched; only
#     the column definition (and therefore the rendered column) is removed.
#
# Chemical column grouping:
#   - Multiple Chemical Items can resolve to the SAME display name (the
#     linked stock Item's item_name - see "Chemical column labels" below),
#     e.g. two differently-named Chemical Items that both map to stock item
#     "G.Nano Industrial". Rather than showing one column per Chemical Item
#     (which would duplicate the same label across columns), those are
#     merged into a single column per distinct display name, and the
#     underlying quantities are summed together for each row/month.
#   - `group_chemicals_by_display_name()` builds this grouping once in
#     get_columns() and is reused in get_data() (to sum qty across every
#     Chemical Item sharing a display name) and in group_data_by_month()
#     (to know which merged fieldnames need summing on monthly roll-up).
#
# Print grouping:
#   - Inlet parameter columns, Outlet parameter columns, and Chemical qty
#     columns are each tagged with a "group" key ("inlet" / "outlet" /
#     "chemical"). The print view's JS (build_group_header_row) reads this
#     exact key to render the spanning "Inlet" / "Outlet" / "Chemical Usage"
#     header band above the normal column-header row. All other columns
#     (Project, Date, QTY, etc.) are left untagged and render as blank
#     spacer cells in that band.
#
# Chemical column labels:
#   - `Chemical Usage Table.chemical` stores a Chemical Item name (e.g.
#     "G Nano Stream 1"), which is an internal/operational name and not
#     necessarily what the business wants printed on the register.
#   - Each Chemical Item optionally links to a stock Item via `stock_item`.
#     For display (column headers + the chemical picker's dropdown hint) we
#     resolve Chemical Item -> stock Item -> item_name and show that instead,
#     falling back to the Chemical Item name itself if there's no linked
#     stock Item or the Item has no item_name.
#   - Column fieldnames are now derived from that resolved DISPLAY NAME
#     (see chemical_group_fieldname), not the raw Chemical Item name -
#     see "Chemical column grouping" above for why.

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

    # Default-on: drop chemical qty columns that have zero usage across
    # everything currently in `data`. filters.get(..., 1) so this stays on
    # even if the caller never passed the key (e.g. older bookmarks/links).
    if filters.get("hide_zero_qty_chemical_columns", 1):
        columns = prune_zero_qty_chemical_columns(columns, data)

    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))


def param_to_fieldname(param, prefix=""):
    base = param.strip().rstrip(".").lower().replace(" ", "_").replace(".", "")
    return f"{prefix}{base}" if prefix else base


def slugify(text):
    slug = "".join(ch if ch.isalnum() else "_" for ch in (text or "").strip().lower())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def chemical_group_fieldname(display_name):
    """Fieldname for a merged chemical qty column, derived from the
    resolved DISPLAY NAME (see group_chemicals_by_display_name) rather than
    any single Chemical Item name - all Chemical Items sharing a display
    name share this one fieldname/column."""
    return "chem_{0}".format(slugify(display_name) or "unknown")


def group_chemicals_by_display_name(chemicals, chemical_item_names):
    """Group selected Chemical Item names by their resolved display name
    (the linked stock Item's item_name, falling back to the Chemical Item
    name itself - see get_chemical_item_names). Two or more Chemical Items
    that resolve to the same display name end up in the same group and
    will be rendered as ONE merged column, with quantities summed.

    Returns an ordered dict: display_name -> [chemical_item_name, ...],
    preserving the first-seen order of `chemicals`.
    """
    groups = {}
    for chemical in chemicals:
        display_name = chemical_item_names.get(chemical, chemical)
        groups.setdefault(display_name, []).append(chemical)
    return groups


def get_chemical_item_names(chemicals):
    """Map Chemical Item name -> linked stock Item's item_name, for display
    purposes only (column labels, picker hint text).

    - Chemical Item.stock_item links to an Item.
    - Falls back to the Chemical Item name itself if there's no stock_item
      link, the linked Item doesn't exist, or it has no item_name.
    """
    if not chemicals:
        return {}

    chem_rows = frappe.get_all(
        "Chemical Item",
        filters={"name": ["in", chemicals]},
        fields=["name", "stock_item"],
    )

    stock_items = [r.stock_item for r in chem_rows if r.stock_item]
    item_names = {}
    if stock_items:
        item_names = {
            i.name: i.item_name
            for i in frappe.get_all(
                "Item", filters={"name": ["in", stock_items]}, fields=["name", "item_name"]
            )
        }

    return {r.name: (item_names.get(r.stock_item) or r.name) for r in chem_rows}


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
    """Resolve which chemicals get their own qty column.

    - `show_chemicals` unchecked -> no chemical columns at all, regardless
      of anything selected in the `chemicals` filter.
    - `show_chemicals` checked + specific chemicals picked in `chemicals`
      -> only those chemicals.
    - `show_chemicals` checked + `chemicals` left empty -> every chemical
      actually used within the current project/unit/date-range filters
      (see get_chemicals_in_scope).
    """
    if not filters.get("show_chemicals"):
        return []

    chemicals = filters.get("chemicals")
    if chemicals and isinstance(chemicals, str):
        chemicals = (
            frappe.parse_json(chemicals) if chemicals.startswith("[") else chemicals.split(",")
        )
    if chemicals:
        return chemicals

    return get_chemicals_in_scope(filters)


def get_chemicals_in_scope(filters):
    """Distinct chemical names used in Chemical Usage Table rows on DORs
    that match the current project/unit/date-range/hide-zero filters.
    Powers the "show every chemical used" behaviour when `show_chemicals`
    is checked but the `chemicals` MultiSelectList is left empty."""

    conditions = ["dor.docstatus = 1", "dor.date between %(from_date)s and %(to_date)s"]
    values = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }
    if filters.get("project"):
        conditions.append("dor.project = %(project)s")
        values["project"] = filters.get("project")
    if filters.get("unit"):
        conditions.append("dor.unit = %(unit)s")
        values["unit"] = filters.get("unit")
    if filters.get("hide_zero_off_spec_rows"):
        conditions.append("dor.waste_water_treated_volume > 0")

    rows = frappe.db.sql(
        """
        select distinct cut.chemical
        from `tabChemical Usage Table` cut
        inner join `tabDaily Operation Report` dor on dor.name = cut.parent
        where cut.parenttype = 'Daily Operation Report'
        and {conditions}
        order by cut.chemical asc
        """.format(conditions=" and ".join(conditions)),
        values,
        as_dict=True,
    )
    return [r.chemical for r in rows if r.chemical]


def get_columns(filters):
    group_by_month = bool(filters.get("group_by_month"))
    water_source = (filters.get("water_source") or "").strip()  # "", "Inlet", "Outlet"
    show_inlet = water_source in ("", "Inlet")
    show_outlet = water_source in ("", "Outlet")
    hide_calc = bool(filters.get("hide_calculation_and_amount"))
    show_density = bool(filters.get("show_chemical_density_qty"))

    inlet_parameters = get_selected_parameters(filters) if show_inlet else []
    # Outlet always shows ALL parameters - it's the "permitted" check,
    # so the `parameter` filter (which narrows Inlet) doesn't apply here.
    outlet_parameters = list(ALL_PARAMETERS) if show_outlet else []
    selected_chemicals = get_selected_chemicals(filters)
    # Display-only: Chemical Item name -> linked stock Item's item_name.
    chemical_item_names = get_chemical_item_names(selected_chemicals)
    # Multiple Chemical Items can share the same display name (e.g. two
    # Chemical Items both linked to stock item "G.Nano Industrial") - group
    # them so they render as a single merged column instead of duplicates.
    chemical_groups = group_chemicals_by_display_name(selected_chemicals, chemical_item_names)

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
    # columns.append(
    #     {"label": _("Running Hours"), "fieldname": "running_hours", "fieldtype": "Float", "precision": 1, "width": 110}
    # )

    # Inlet parameter columns (filtered by "parameter")
    # NOTE: "group": "inlet" is what drives the spanning "Inlet" header band
    # in the print view (water_treatment_register.js -> build_group_header_row
    # reads col.group). Previously this was "water_group", which the JS never
    # read, so the Inlet band silently never rendered.
    for param in inlet_parameters:
        columns.append(
            {
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param, "in_"),
                "fieldtype": "Float",
                "width": 110,
                "group": "inlet",
            }
        )

    # Outlet parameter columns - always ALL_PARAMETERS
    # Same fix: "group": "outlet" (was "water_group").
    for param in outlet_parameters:
        columns.append(
            {
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param, "out_"),
                "fieldtype": "Float",
                "width": 110,
                "group": "outlet",
            }
        )

    # Chemical usage qty columns - ONE per distinct display name (Chemical
    # Items sharing a display name are merged into a single column; their
    # quantities get summed together in get_data / group_data_by_month).
    # Same group fix as above: "group": "chemical" (was "chemical_group": True).
    density_suffix = " " + str(_("(after density)")) if show_density else ""
    for display_name in chemical_groups.keys():
        columns.append(
            {
                "label": "{0} {1}{2}".format(display_name, _("Qty (kg)"), density_suffix),
                "fieldname": chemical_group_fieldname(display_name),
                "fieldtype": "Float",
                "precision": 2,
                "width": 140,
                "group": "chemical",
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
            "chemical_groups": chemical_groups,
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
            "energy_consumtion": dor.energy_consumtion*dor.waste_water_treated_volume or 0,
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

        # Chemical usage qty columns - summed per display-name group (so
        # Chemical Items sharing a display name combine into one value).
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
            for display_name, chemical_names in ctx.chemical_groups.items():
                total_qty = None
                for chemical in chemical_names:
                    c = chem_by_name.get(chemical)
                    if not c:
                        continue
                    qty = c.get(CHEMICAL_QTY_FIELD_DENSITY) if filters.get("show_density") else c.get(CHEMICAL_QTY_FIELD)
                    if qty is not None:
                        total_qty = (total_qty or 0) + flt(qty)
                row[chemical_group_fieldname(display_name)] = total_qty

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
    chem_fieldnames = [chemical_group_fieldname(display_name) for display_name in ctx.chemical_groups.keys()]

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


def prune_zero_qty_chemical_columns(columns, data):
    """Drop any column tagged group == "chemical" whose total across all
    rows in `data` is 0 (or every value is None). Runs after data has been
    built (and, if applicable, monthly-grouped) so it reflects the actual
    totals being shown - a chemical selected via the filter but never
    actually used in range simply won't get a column."""
    kept = []
    for col in columns:
        if col.get("group") == "chemical":
            total = sum(flt(row.get(col["fieldname"])) for row in data)
            if not total:
                continue
        kept.append(col)
    return kept


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

    if filters.get("hide_zero_qty_chemical_columns", 1):
        columns = prune_zero_qty_chemical_columns(columns, data)

    # totals = {}
    # for col in columns:
    #     if col.get("fieldtype") in ("Float", "Currency"):
    #         fieldname = col.get("fieldname")
    #         print("Calculating total for fieldname:", fieldname)
    #         totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in data))
    
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
def get_chemical_options(txt=None):
    """Distinct chemical names across all DOR Chemical Usage Table rows -
    powers the "Chemicals (Qty Columns)" MultiSelectList filter's dropdown.

    Returns [{"value": <Chemical Item name>, "description": <linked stock
    Item's item_name>}, ...] - the value stored/filtered on is still the
    Chemical Item name (matches Chemical Usage Table.chemical), the
    description is just a display hint so users can tell which stock item
    each chemical maps to while picking.

    NOTE: this name must match the method called from
    water_treatment_register.js (REPORT_METHOD_PATH + ".get_chemical_options").
    It was previously named get_chemical_list, which the JS never actually
    called, so the dropdown silently returned nothing."""
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

    item_names = get_chemical_item_names(names)
    return [{"value": n, "description": item_names.get(n, "")} for n in names]