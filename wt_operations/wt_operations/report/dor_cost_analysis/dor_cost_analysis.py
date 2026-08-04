# Copyright (c) 2026, HM and contributors
# For license information, please see license.txt
#
# ============================================================
# DOR Cost Analysis - Script Report
# ------------------------------------------------------------
# Cost model (per Daily Operation Report):
#     chemical_cost   = SUM(Chemical Usage Table.chemical_used_amount)
#     manpower_cost   = DOR.manpower_cost_per_treated_water
#     spare_part_cost = DOR.spare_part_cost_per_treated_water
#     other_cost      = DOR.other_cost_per_treated_water
#     total_cost      = sum of the four above
#     <category>/M3   = <category cost> / waste_water_treated_volume
#
# Filters:
#     from_date, to_date   (used unless filter_month is set)
#     filter_month/year    (Select "January".."December" + year - a
#                           quick way to pick a whole month instead
#                           of setting From/To manually; overrides
#                           from_date/to_date when set)
#     project              (optional Link)
#     exclude_zero_volume  (Check - same as "Cost Dashboard With Qty")
#     display              (Select: "Both" / "Cost Only" / "Cost per M3 Only")
#     group_by             (Select: "None" / "Month" / "Project" / "Month + Project")
#                           aggregates the daily rows into monthly
#                           and/or per-project totals with recomputed
#                           per-m3 rates (never an average of daily
#                           ratios - always SUM(cost) / SUM(volume))
#
# Uses raw SQL (one query, LEFT JOIN against the child table) rather
# than frappe.get_all + per-row queries, so it scales to large date
# ranges without the N-call pattern the client script dialog uses.
#
# PRINT: the "Print" button in dor_cost_analysis.js calls the
# whitelisted get_print_pdf() below via frappe.call - all data
# fetching, grouping, totals math, and HTML/PDF rendering happen
# here in Python. The button only base64-decodes the response.
# ============================================================

import base64
import calendar
import datetime

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, formatdate, get_first_day, get_last_day, get_url, now_datetime
from frappe.utils.pdf import get_pdf

MONTH_NAMES = list(calendar.month_name)  # index 0 = "", 1 = "January", ... 12 = "December"

CATEGORIES = [
	("chemical_cost", "Chemical Cost", "Chemical / M3"),
	("manpower_cost", "Manpower Cost", "Manpower / M3"),
	("spare_part_cost", "Spare Part Cost", "Spare Part / M3"),
	("other_cost", "Other Cost", "Other / M3"),
]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	resolve_filters(filters)

	display = filters.get("display") or "Both"
	show_cost = display in ("Both", "Cost Only")
	show_per_m3 = display in ("Both", "Cost per M3 Only")
	group_by = filters.get("group_by") or "None"

	raw_rows, totals = get_raw_data_and_totals(filters)
	columns = get_columns(show_cost, show_per_m3, group_by)

	data = build_report_rows(raw_rows, group_by)
	if totals:
		totals_row = dict(totals)
		totals_row["is_total_row"] = 1
		apply_totals_labels(totals_row, group_by)
		data.append(totals_row)

	report_summary = get_report_summary(totals)
	chart = get_chart(raw_rows, group_by)

	return columns, data, None, chart, report_summary


# ------------------------------------------------------------
# Filters
# ------------------------------------------------------------
def resolve_filters(filters):
	"""If filter_month is set, it overrides from_date/to_date with
	the full first-to-last-day range of that month/year. Otherwise
	from_date/to_date (set directly by the user) are required."""

	if filters.get("filter_month"):
		month_name = filters.get("filter_month")
		if month_name not in MONTH_NAMES:
			frappe.throw(_("Invalid month filter"))
		month_number = MONTH_NAMES.index(month_name)
		year = int(filters.get("filter_year") or now_datetime().year)

		base_date = datetime.date(year, month_number, 1)
		filters["from_date"] = get_first_day(base_date)
		filters["to_date"] = get_last_day(base_date)
	else:
		if not filters.get("from_date") or not filters.get("to_date"):
			frappe.throw(_("Please set a From Date/To Date range, or use the Month filter"))
		if filters.get("from_date") > filters.get("to_date"):
			frappe.throw(_("From Date cannot be after To Date"))


# ------------------------------------------------------------
# Data
# ------------------------------------------------------------
def get_raw_data_and_totals(filters):
	conditions = ["dor.docstatus = 1", "dor.date BETWEEN %(from_date)s AND %(to_date)s"]

	if filters.get("project"):
		conditions.append("dor.project = %(project)s")

	if filters.get("exclude_zero_volume"):
		conditions.append("dor.waste_water_treated_volume > 0")

	where_clause = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT
			dor.name AS dor,
			dor.date AS date,
			dor.project AS project,
			dor.waste_water_treated_volume AS treated_water,
			COALESCE(chem.chemical_cost, 0) AS chemical_cost,
			COALESCE(dor.manpower_cost_per_treated_water, 0) AS manpower_cost,
			COALESCE(dor.spare_part_cost_per_treated_water, 0) AS spare_part_cost,
			COALESCE(dor.other_cost_per_treated_water, 0) AS other_cost
		FROM `tabDaily Operation Report` dor
		LEFT JOIN (
			SELECT parent, SUM(chemical_used_amount) AS chemical_cost
			FROM `tabChemical Usage Table`
			GROUP BY parent
		) chem ON chem.parent = dor.name
		WHERE {where_clause}
		ORDER BY dor.date ASC
		""",
		filters,
		as_dict=1,
	)

	data = []
	for row in rows:
		treated_water = flt(row.treated_water)
		chemical_cost = flt(row.chemical_cost)
		manpower_cost = flt(row.manpower_cost)
		spare_part_cost = flt(row.spare_part_cost)
		other_cost = flt(row.other_cost)
		total_cost = chemical_cost + manpower_cost + spare_part_cost + other_cost

		def per_m3(cost, tw=treated_water):
			return flt(cost / tw) if tw else 0

		data.append(
			{
				"dor": row.dor,
				"date": row.date,
				"project": row.project,
				"month_label": row.date.strftime("%B %Y") if row.date else "",
				"month_sort": row.date.strftime("%Y-%m") if row.date else "",
				"treated_water": treated_water,
				"chemical_cost": chemical_cost,
				"chemical_cost_per_m3": per_m3(chemical_cost),
				"manpower_cost": manpower_cost,
				"manpower_cost_per_m3": per_m3(manpower_cost),
				"spare_part_cost": spare_part_cost,
				"spare_part_cost_per_m3": per_m3(spare_part_cost),
				"other_cost": other_cost,
				"other_cost_per_m3": per_m3(other_cost),
				"total_cost": total_cost,
				"total_cost_per_m3": per_m3(total_cost),
			}
		)

	totals = None
	if data:
		totals = {
			"dor": None,
			"date": None,
			"project": None,
			"month_label": None,
			"treated_water": sum(d["treated_water"] for d in data),
			"chemical_cost": sum(d["chemical_cost"] for d in data),
			"manpower_cost": sum(d["manpower_cost"] for d in data),
			"spare_part_cost": sum(d["spare_part_cost"] for d in data),
			"other_cost": sum(d["other_cost"] for d in data),
			"total_cost": sum(d["total_cost"] for d in data),
			"dor_count": len(data),
		}
		tw = totals["treated_water"]
		totals["chemical_cost_per_m3"] = flt(totals["chemical_cost"] / tw) if tw else 0
		totals["manpower_cost_per_m3"] = flt(totals["manpower_cost"] / tw) if tw else 0
		totals["spare_part_cost_per_m3"] = flt(totals["spare_part_cost"] / tw) if tw else 0
		totals["other_cost_per_m3"] = flt(totals["other_cost"] / tw) if tw else 0
		totals["total_cost_per_m3"] = flt(totals["total_cost"] / tw) if tw else 0

	return data, totals


def apply_totals_labels(totals_row, group_by):
	"""Set the display label(s) on the totals row to match whichever
	label column(s) are showing for the current group_by mode."""
	if group_by == "None":
		totals_row["project"] = _("Total")
	elif group_by == "Month":
		totals_row["month_label"] = _("Total")
	elif group_by == "Project":
		totals_row["project"] = _("Total")
	elif group_by == "Month + Project":
		totals_row["month_label"] = _("Total")
		totals_row["project"] = ""


# ------------------------------------------------------------
# Grouping (shared by the on-screen grid, the print PDF, and the chart)
# ------------------------------------------------------------
def group_rows(raw_rows, key_fn, label_fn):
	"""Aggregate raw daily rows by an arbitrary key, recomputing every
	per-m3 rate as SUM(category cost) / SUM(treated water) for the
	group - never an average of the individual daily ratios."""
	groups = {}

	for row in raw_rows:
		key = key_fn(row)
		if key not in groups:
			groups[key] = {
				"treated_water": 0,
				"chemical_cost": 0,
				"manpower_cost": 0,
				"spare_part_cost": 0,
				"other_cost": 0,
				"total_cost": 0,
				"dor_count": 0,
			}
			groups[key].update(label_fn(row))
		g = groups[key]
		g["treated_water"] += row["treated_water"]
		g["chemical_cost"] += row["chemical_cost"]
		g["manpower_cost"] += row["manpower_cost"]
		g["spare_part_cost"] += row["spare_part_cost"]
		g["other_cost"] += row["other_cost"]
		g["total_cost"] += row["total_cost"]
		g["dor_count"] += 1

	grouped = []
	for key in sorted(groups.keys()):
		g = groups[key]
		tw = g["treated_water"]
		g["chemical_cost_per_m3"] = flt(g["chemical_cost"] / tw) if tw else 0
		g["manpower_cost_per_m3"] = flt(g["manpower_cost"] / tw) if tw else 0
		g["spare_part_cost_per_m3"] = flt(g["spare_part_cost"] / tw) if tw else 0
		g["other_cost_per_m3"] = flt(g["other_cost"] / tw) if tw else 0
		g["total_cost_per_m3"] = flt(g["total_cost"] / tw) if tw else 0
		grouped.append(g)

	return grouped


def build_report_rows(raw_rows, group_by):
	if not raw_rows:
		return []

	if group_by == "Month":
		return group_rows(
			raw_rows,
			key_fn=lambda r: r["month_sort"],
			label_fn=lambda r: {"month_label": r["month_label"]},
		)

	if group_by == "Project":
		return group_rows(
			raw_rows,
			key_fn=lambda r: r["project"] or _("(No Project)"),
			label_fn=lambda r: {"project": r["project"] or _("(No Project)")},
		)

	if group_by == "Month + Project":
		return group_rows(
			raw_rows,
			key_fn=lambda r: (r["month_sort"], r["project"] or _("(No Project)")),
			label_fn=lambda r: {
				"month_label": r["month_label"],
				"project": r["project"] or _("(No Project)"),
			},
		)

	return list(raw_rows)


# ------------------------------------------------------------
# Columns
# ------------------------------------------------------------
def get_columns(show_cost, show_per_m3, group_by):
	columns = []

	if group_by == "None":
		columns += [
			{"label": _("DOR"), "fieldname": "dor", "fieldtype": "Link", "options": "Daily Operation Report", "width": 130},
			{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 95},
			{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 140},
		]
	else:
		if group_by in ("Month", "Month + Project"):
			columns.append({"label": _("Month"), "fieldname": "month_label", "fieldtype": "Data", "width": 110})
		if group_by in ("Project", "Month + Project"):
			columns.append({"label": _("Project"), "fieldname": "project", "fieldtype": "Data", "width": 140})
		columns.append({"label": _("DOR Count"), "fieldname": "dor_count", "fieldtype": "Int", "width": 90})

	columns.append(
		{"label": _("Treated Water (M3)"), "fieldname": "treated_water", "fieldtype": "Float", "precision": 2, "width": 130}
	)

	for fieldname, cost_label, per_m3_label in CATEGORIES:
		if show_cost:
			columns.append({"label": _(cost_label), "fieldname": fieldname, "fieldtype": "Currency", "width": 120})
		if show_per_m3:
			columns.append(
				{"label": _(per_m3_label), "fieldname": f"{fieldname}_per_m3", "fieldtype": "Currency", "width": 110}
			)

	if show_cost:
		columns.append({"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 130})
	if show_per_m3:
		columns.append(
			{"label": _("Total Cost / M3"), "fieldname": "total_cost_per_m3", "fieldtype": "Currency", "width": 130}
		)

	return columns


def get_report_summary(totals):
	if not totals:
		return []

	return [
		{"value": totals["treated_water"], "indicator": "Blue", "label": _("Total Treated Water (M3)"), "datatype": "Float", "precision": 2},
		{"value": totals["total_cost"], "indicator": "Blue", "label": _("Total Cost"), "datatype": "Currency"},
		{"value": totals["total_cost_per_m3"], "indicator": "Green", "label": _("Total Cost / M3"), "datatype": "Currency"},
		{"value": totals["chemical_cost_per_m3"], "indicator": "Orange", "label": _("Chemical / M3"), "datatype": "Currency"},
		{"value": totals["manpower_cost_per_m3"], "indicator": "Orange", "label": _("Manpower / M3"), "datatype": "Currency"},
		{"value": totals["spare_part_cost_per_m3"], "indicator": "Orange", "label": _("Spare Part / M3"), "datatype": "Currency"},
		{"value": totals["other_cost_per_m3"], "indicator": "Orange", "label": _("Other / M3"), "datatype": "Currency"},
	]


def get_chart(raw_rows, group_by):
	if not raw_rows:
		return None

	if group_by == "Project":
		grouped = group_rows(
			raw_rows,
			key_fn=lambda r: r["project"] or _("(No Project)"),
			label_fn=lambda r: {"project": r["project"] or _("(No Project)")},
		)
		return {
			"data": {
				"labels": [g["project"] for g in grouped],
				"datasets": [{"name": _("Total Cost / M3"), "values": [g["total_cost_per_m3"] for g in grouped]}],
			},
			"type": "bar",
			"colors": ["#1976a8"],
		}

	# "None", "Month", and "Month + Project" all get a monthly trend line
	monthly = group_rows(
		raw_rows,
		key_fn=lambda r: r["month_sort"],
		label_fn=lambda r: {"month_label": r["month_label"]},
	)
	return {
		"data": {
			"labels": [g["month_label"] for g in monthly],
			"datasets": [{"name": _("Total Cost / M3"), "values": [g["total_cost_per_m3"] for g in monthly]}],
		},
		"type": "line",
		"colors": ["#1976a8"],
	}


# ============================================================
# PRINT / PDF
# Called by the "Print" button (dor_cost_analysis.js) via
# frappe.call. Reuses resolve_filters()/get_raw_data_and_totals()/
# build_report_rows() so the printed numbers - grouped or not -
# can never drift from what's on screen.
# ============================================================


@frappe.whitelist()
def get_print_pdf(filters=None):
	"""Build the branded print HTML and return it as a base64-encoded PDF."""
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	filters = frappe._dict(filters or {})
	resolve_filters(filters)

	display = filters.get("display") or "Both"
	show_cost = display in ("Both", "Cost Only")
	show_per_m3 = display in ("Both", "Cost per M3 Only")
	group_by = filters.get("group_by") or "None"

	raw_rows, totals = get_raw_data_and_totals(filters)
	if not raw_rows:
		frappe.throw(_("No data found for the selected filters"))

	rows = build_report_rows(raw_rows, group_by)

	company = get_company_info()
	html = build_print_html(rows, totals, filters, company, show_cost, show_per_m3, group_by)

	pdf_content = get_pdf(html, {"orientation": "Landscape"})
	return base64.b64encode(pdf_content).decode("utf-8")


def get_company_info():
	"""Fetch company name + logo (absolute URL) for the print header."""
	company = frappe.defaults.get_user_default("company") or frappe.defaults.get_global_default("company")
	info = {"name": company or "", "logo": ""}

	if company:
		company_doc = frappe.db.get_value("Company", company, ["company_name", "company_logo"], as_dict=True)
		if company_doc:
			info["name"] = company_doc.company_name or company
			if company_doc.company_logo:
				logo = company_doc.company_logo
				info["logo"] = logo if logo.startswith("http") else get_url(logo)

	return info


def _currency(value):
	return fmt_money(flt(value), currency=frappe.defaults.get_global_default("currency"))


def _number(value):
	return "{:,.2f}".format(flt(value))


def _label_header_cells(group_by):
	if group_by == "None":
		return f"<th>{_('Date')}</th><th>{_('Project')}</th>"

	cells = ""
	if group_by in ("Month", "Month + Project"):
		cells += f"<th>{_('Month')}</th>"
	if group_by in ("Project", "Month + Project"):
		cells += f"<th>{_('Project')}</th>"
	cells += f"<th class='text-right'>{_('DOR Count')}</th>"
	return cells


def _label_row_cells(row, group_by):
	if group_by == "None":
		return (
			f"<td>{formatdate(row['date']) if row.get('date') else ''}</td>"
			f"<td>{frappe.utils.escape_html(row.get('project') or '')}</td>"
		)

	cells = ""
	if group_by in ("Month", "Month + Project"):
		cells += f"<td>{frappe.utils.escape_html(row.get('month_label') or '')}</td>"
	if group_by in ("Project", "Month + Project"):
		cells += f"<td>{frappe.utils.escape_html(row.get('project') or '')}</td>"
	cells += f"<td class='text-right'>{row.get('dor_count', '')}</td>"
	return cells


def _totals_label_cells(totals, group_by):
	if group_by == "None":
		return f"<td>{_('Total')}</td><td></td>"

	cells = ""
	if group_by in ("Month", "Month + Project"):
		cells += f"<td>{_('Total')}</td>"
	if group_by == "Project":
		cells += f"<td>{_('Total')}</td>"
	elif group_by == "Month + Project":
		cells += "<td></td>"
	cells += f"<td class='text-right'>{totals.get('dor_count', '')}</td>"
	return cells


def _value_cells(row, show_cost, show_per_m3):
	cells = f"<td class='text-right'>{_number(row['treated_water'])}</td>"
	for fieldname, _cost_label, _per_m3_label in CATEGORIES:
		if show_cost:
			cells += f"<td class='text-right'>{_currency(row[fieldname])}</td>"
		if show_per_m3:
			cells += f"<td class='text-right col-per-m3'>{_currency(row[f'{fieldname}_per_m3'])}</td>"
	if show_cost:
		cells += f"<td class='text-right'>{_currency(row['total_cost'])}</td>"
	if show_per_m3:
		cells += f"<td class='text-right col-per-m3'>{_currency(row['total_cost_per_m3'])}</td>"
	return cells


def build_print_html(rows, totals, filters, company, show_cost, show_per_m3, group_by):
	"""Render the same visual language as the client-script print view
	(gradient header band, logo, KPI cards, tinted /M3 columns) but
	server-side, so get_pdf() can turn it straight into a PDF."""

	project_line = (
		f"{_('Project')}: <strong>{frappe.utils.escape_html(filters.get('project'))}</strong> &nbsp;|&nbsp; "
		if filters.get("project")
		else ""
	)
	group_by_line = (
		f"{_('Grouped by')}: <strong>{frappe.utils.escape_html(_(group_by))}</strong> &nbsp;|&nbsp; "
		if group_by != "None"
		else ""
	)
	filter_line = (
		f"{project_line}{group_by_line}"
		f"{_('From')}: <strong>{formatdate(filters.get('from_date'))}</strong>"
		f" &nbsp;&rarr;&nbsp; "
		f"{_('To')}: <strong>{formatdate(filters.get('to_date'))}</strong>"
	)

	kpi_cards_html = f"""
		<div class="kpi-row">
			<div class="kpi-card kpi-primary">
				<div class="kpi-label">{_('Treated Water')}</div>
				<div class="kpi-value">{_number(totals['treated_water'])} <span class="kpi-unit">m&sup3;</span></div>
			</div>
			<div class="kpi-card kpi-primary">
				<div class="kpi-label">{_('Total Cost')}</div>
				<div class="kpi-value">{_currency(totals['total_cost'])}</div>
			</div>
			<div class="kpi-card kpi-primary">
				<div class="kpi-label">{_('Total Cost / m&sup3;')}</div>
				<div class="kpi-value">{_currency(totals['total_cost_per_m3'])}</div>
			</div>
		</div>
		<div class="kpi-row kpi-row-secondary">
			<div class="kpi-card kpi-small">
				<div class="kpi-label">{_('Chemical / m&sup3;')}</div>
				<div class="kpi-value kpi-value-sm">{_currency(totals['chemical_cost_per_m3'])}</div>
			</div>
			<div class="kpi-card kpi-small">
				<div class="kpi-label">{_('Manpower / m&sup3;')}</div>
				<div class="kpi-value kpi-value-sm">{_currency(totals['manpower_cost_per_m3'])}</div>
			</div>
			<div class="kpi-card kpi-small">
				<div class="kpi-label">{_('Spare Part / m&sup3;')}</div>
				<div class="kpi-value kpi-value-sm">{_currency(totals['spare_part_cost_per_m3'])}</div>
			</div>
			<div class="kpi-card kpi-small">
				<div class="kpi-label">{_('Other / m&sup3;')}</div>
				<div class="kpi-value kpi-value-sm">{_currency(totals['other_cost_per_m3'])}</div>
			</div>
		</div>"""

	header_cells = _label_header_cells(group_by) + f"<th class='text-right'>{_('Treated Water (M3)')}</th>"
	for fieldname, cost_label, per_m3_label in CATEGORIES:
		if show_cost:
			header_cells += f"<th class='text-right'>{_(cost_label)}</th>"
		if show_per_m3:
			header_cells += f"<th class='text-right col-per-m3'>{_(per_m3_label)}</th>"
	if show_cost:
		header_cells += f"<th class='text-right'>{_('Total Cost')}</th>"
	if show_per_m3:
		header_cells += f"<th class='text-right col-per-m3'>{_('Total Cost / M3')}</th>"

	body_rows_html = "".join(
		f"<tr>{_label_row_cells(row, group_by)}{_value_cells(row, show_cost, show_per_m3)}</tr>" for row in rows
	)
	totals_row_html = (
		f"<tr class='totals-row'>{_totals_label_cells(totals, group_by)}{_value_cells(totals, show_cost, show_per_m3)}</tr>"
	)

	logo_html = f"<img src='{company['logo']}' class='company-logo' />" if company.get("logo") else ""

	return f"""
	<html>
	<head>
		<meta charset="utf-8" />
		<style>
			:root {{
				--brand-dark: #0b3d5c;
				--brand-blue: #1976a8;
				--brand-light: #eaf4fa;
				--accent: #2e9e6f;
			}}
			* {{ box-sizing: border-box; }}
			body {{
				font-family: "Segoe UI", Arial, sans-serif;
				margin: 0;
				padding: 0;
				color: #222;
			}}
			.page {{ padding: 14px 20px 30px; }}

			.print-header {{
				display: flex;
				align-items: center;
				justify-content: space-between;
				background: linear-gradient(135deg, var(--brand-dark), var(--brand-blue));
				color: #fff;
				padding: 14px 20px;
				border-radius: 8px;
				margin-bottom: 14px;
				-webkit-print-color-adjust: exact;
				print-color-adjust: exact;
			}}
			.print-header .left {{ display: flex; align-items: center; gap: 12px; }}
			.company-logo {{ max-height: 42px; max-width: 130px; background: #fff; padding: 4px 8px; border-radius: 6px; }}
			.company-name {{ font-size: 16px; font-weight: 600; }}
			.report-title {{ font-size: 11px; opacity: 0.9; margin-top: 2px; }}
			.print-header .right {{ text-align: right; }}
			.report-heading {{ font-size: 18px; font-weight: 700; }}
			.report-subheading {{ font-size: 10px; opacity: 0.9; margin-top: 4px; }}

			.filter-bar {{
				background: var(--brand-light);
				border-left: 4px solid var(--brand-blue);
				padding: 7px 12px;
				font-size: 11px;
				color: var(--brand-dark);
				border-radius: 4px;
				margin-bottom: 14px;
			}}

			.kpi-row {{ display: flex; gap: 10px; margin-bottom: 10px; }}
			.kpi-row-secondary {{ margin-bottom: 18px; }}
			.kpi-card {{
				flex: 1;
				border: 1px solid #e0e6ea;
				border-top: 3px solid var(--brand-blue);
				border-radius: 6px;
				padding: 8px 12px;
				-webkit-print-color-adjust: exact;
				print-color-adjust: exact;
			}}
			.kpi-card.kpi-small {{ border-top: 3px solid var(--accent); background: #f7fdfb; padding: 6px 10px; }}
			.kpi-label {{ font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7c85; margin-bottom: 3px; }}
			.kpi-value {{ font-size: 15px; font-weight: 700; color: var(--brand-dark); }}
			.kpi-value-sm {{ font-size: 12.5px; color: var(--accent); }}
			.kpi-unit {{ font-size: 10px; font-weight: 400; color: #6b7c85; }}

			table {{ width: 100%; border-collapse: collapse; font-size: 10.5px; }}
			thead th {{
				background: var(--brand-dark);
				color: #fff;
				padding: 6px 8px;
				text-align: left;
				font-weight: 600;
				-webkit-print-color-adjust: exact;
				print-color-adjust: exact;
			}}
			tbody td {{ padding: 5px 8px; border-bottom: 1px solid #e6ebee; }}
			tbody tr:nth-child(even) {{ background: #f7fafc; }}
			.col-per-m3 {{
				color: var(--brand-blue);
				background: #f4fafd;
				font-weight: 600;
				-webkit-print-color-adjust: exact;
				print-color-adjust: exact;
			}}
			thead .col-per-m3 {{ background: var(--brand-dark); color: #fff; }}
			.totals-row td {{
				background: var(--brand-light) !important;
				font-weight: 700;
				border-top: 2px solid var(--brand-blue);
				color: var(--brand-dark);
				-webkit-print-color-adjust: exact;
				print-color-adjust: exact;
			}}
			.totals-row td.col-per-m3 {{
				background: var(--brand-blue) !important;
				color: #fff !important;
			}}
			.text-right {{ text-align: right; }}

			.print-footer {{
				margin-top: 14px;
				padding-top: 6px;
				border-top: 1px solid #e0e6ea;
				font-size: 9px;
				color: #8a97a0;
				display: flex;
				justify-content: space-between;
			}}
		</style>
	</head>
	<body>
		<div class="page">
			<div class="print-header">
				<div class="left">
					{logo_html}
					<div>
						<div class="company-name">{frappe.utils.escape_html(company.get('name') or '')}</div>
						<div class="report-title">{_('Water Treatment Operations')}</div>
					</div>
				</div>
				<div class="right">
					<div class="report-heading">{_('DOR Cost Analysis')}</div>
					<div class="report-subheading">{_('Generated')}: {now_datetime().strftime('%Y-%m-%d %H:%M')}</div>
				</div>
			</div>

			<div class="filter-bar">{filter_line}</div>

			{kpi_cards_html}

			<table>
				<thead><tr>{header_cells}</tr></thead>
				<tbody>
					{body_rows_html}
					{totals_row_html}
				</tbody>
			</table>

			<div class="print-footer">
				<span>{frappe.utils.escape_html(company.get('name') or '')}</span>
				<span>{_('Page generated by ERPNext')}</span>
			</div>
		</div>
	</body>
	</html>
	"""