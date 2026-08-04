# Copyright (c) 2026, HM and contributors
# For license information, please see license.txt
#
# ============================================================
# DOR Cost Analysis - Script Report
# ------------------------------------------------------------
# Server-side counterpart of the "DOR Cost Dashboard" client
# script dialog/print view. Same cost model:
#     chemical_cost   = SUM(Chemical Usage Table.chemical_used_amount)
#     manpower_cost    = DOR.manpower_cost_per_treated_water
#     spare_part_cost  = DOR.spare_part_cost_per_treated_water
#     other_cost       = DOR.other_cost_per_treated_water
#     total_cost       = sum of the four above
#     <category>/M3    = <category cost> / waste_water_treated_volume
#
# Filters:
#     from_date, to_date   (required)
#     project              (optional Link)
#     exclude_zero_volume  (Check - same as "Cost Dashboard With Qty")
#     display              (Select: "Both" / "Cost Only" / "Cost per M3 Only")
#                           controls which of the paired columns show up
#
# Uses raw SQL (one query, LEFT JOIN against the child table) rather
# than frappe.get_all + per-row queries, so it scales to large date
# ranges without the N-call pattern the client script dialog uses.
# ============================================================

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	display = filters.get("display") or "Both"
	show_cost = display in ("Both", "Cost Only")
	show_per_m3 = display in ("Both", "Cost per M3 Only")

	columns = get_columns(show_cost, show_per_m3)
	data = get_data(filters)
	report_summary = get_report_summary(data)
	chart = get_chart(data)

	return columns, data, None, chart, report_summary


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("Please set both From Date and To Date"))

	if filters.get("from_date") > filters.get("to_date"):
		frappe.throw(_("From Date cannot be after To Date"))


def get_data(filters):
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

		def per_m3(cost):
			return flt(cost / treated_water) if treated_water else 0

		data.append(
			{
				"dor": row.dor,
				"date": row.date,
				"project": row.project,
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

	# Totals row - computed as SUM(category cost) / SUM(treated_water),
	# never as an average of each day's per-m3 value (that would be an
	# average-of-averages skewed by low-volume days).
	if data:
		totals = {
			"dor": None,
			"date": None,
			"project": _("Total"),
			"treated_water": sum(d["treated_water"] for d in data),
			"chemical_cost": sum(d["chemical_cost"] for d in data),
			"manpower_cost": sum(d["manpower_cost"] for d in data),
			"spare_part_cost": sum(d["spare_part_cost"] for d in data),
			"other_cost": sum(d["other_cost"] for d in data),
			"total_cost": sum(d["total_cost"] for d in data),
		}
		tw = totals["treated_water"]
		totals["chemical_cost_per_m3"] = flt(totals["chemical_cost"] / tw) if tw else 0
		totals["manpower_cost_per_m3"] = flt(totals["manpower_cost"] / tw) if tw else 0
		totals["spare_part_cost_per_m3"] = flt(totals["spare_part_cost"] / tw) if tw else 0
		totals["other_cost_per_m3"] = flt(totals["other_cost"] / tw) if tw else 0
		totals["total_cost_per_m3"] = flt(totals["total_cost"] / tw) if tw else 0
		totals["is_total_row"] = 1
		data.append(totals)

	return data


def get_columns(show_cost, show_per_m3):
	columns = [
		{
			"label": _("DOR"),
			"fieldname": "dor",
			"fieldtype": "Link",
			"options": "Daily Operation Report",
			"width": 130,
		},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 95},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 140,
		},
		{
			"label": _("Treated Water (M3)"),
			"fieldname": "treated_water",
			"fieldtype": "Float",
			"precision": 2,
			"width": 130,
		},
	]

	categories = [
		("chemical_cost", _("Chemical Cost"), _("Chemical / M3")),
		("manpower_cost", _("Manpower Cost"), _("Manpower / M3")),
		("spare_part_cost", _("Spare Part Cost"), _("Spare Part / M3")),
		("other_cost", _("Other Cost"), _("Other / M3")),
	]

	for fieldname, cost_label, per_m3_label in categories:
		if show_cost:
			columns.append(
				{"label": cost_label, "fieldname": fieldname, "fieldtype": "Currency", "width": 120}
			)
		if show_per_m3:
			columns.append(
				{
					"label": per_m3_label,
					"fieldname": f"{fieldname}_per_m3",
					"fieldtype": "Currency",
					"width": 110,
				}
			)

	if show_cost:
		columns.append(
			{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 130}
		)
	if show_per_m3:
		columns.append(
			{
				"label": _("Total Cost / M3"),
				"fieldname": "total_cost_per_m3",
				"fieldtype": "Currency",
				"width": 130,
			}
		)

	return columns


def get_report_summary(data):
	if not data:
		return []

	totals = data[-1]

	return [
		{
			"value": totals["treated_water"],
			"indicator": "Blue",
			"label": _("Total Treated Water (M3)"),
			"datatype": "Float",
			"precision": 2,
		},
		{
			"value": totals["total_cost"],
			"indicator": "Blue",
			"label": _("Total Cost"),
			"datatype": "Currency",
		},
		{
			"value": totals["total_cost_per_m3"],
			"indicator": "Green",
			"label": _("Total Cost / M3"),
			"datatype": "Currency",
		},
		{
			"value": totals["chemical_cost_per_m3"],
			"indicator": "Orange",
			"label": _("Chemical / M3"),
			"datatype": "Currency",
		},
		{
			"value": totals["manpower_cost_per_m3"],
			"indicator": "Orange",
			"label": _("Manpower / M3"),
			"datatype": "Currency",
		},
		{
			"value": totals["spare_part_cost_per_m3"],
			"indicator": "Orange",
			"label": _("Spare Part / M3"),
			"datatype": "Currency",
		},
		{
			"value": totals["other_cost_per_m3"],
			"indicator": "Orange",
			"label": _("Other / M3"),
			"datatype": "Currency",
		},
	]


def get_chart(data):
	# Exclude the totals row from the trend chart
	rows = [d for d in data if not d.get("is_total_row")]
	if not rows:
		return None

	return {
		"data": {
			"labels": [frappe.utils.formatdate(d["date"]) for d in rows],
			"datasets": [
				{"name": _("Total Cost / M3"), "values": [d["total_cost_per_m3"] for d in rows]},
			],
		},
		"type": "line",
		"colors": ["#1976a8"],
	}