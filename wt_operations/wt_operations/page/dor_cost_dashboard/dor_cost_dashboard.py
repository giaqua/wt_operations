# Copyright (c) 2026, HM and contributors
# For license information, please see license.txt
#
# ============================================================
# DOR Cost Dashboard - data API
# ------------------------------------------------------------
# Same cost model as the "DOR Cost Analysis" report:
#     chemical_cost   = SUM(Chemical Usage Table.chemical_used_amount)
#     manpower_cost   = DOR.manpower_cost_per_treated_water
#     spare_part_cost = DOR.spare_part_cost_per_treated_water
#     other_cost      = DOR.other_cost_per_treated_water
#     total_cost      = sum of the four above
#     <category>/M3   = <category cost> / waste_water_treated_volume
#
# Every aggregate (month / project / day / overall / previous period)
# recomputes per-m3 as SUM(cost) / SUM(volume) - never an average of
# daily ratios.
#
# One whitelisted method, get_dashboard_data(filters), returns
# everything the page needs in a single round trip:
#     kpis, previous_kpis, monthly, projects, daily, rows (DOR level),
#     anomalies, period info, currency.
# ============================================================

import statistics

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, getdate, now_datetime

CATEGORIES = ("chemical", "manpower", "spare_part", "other")
CATEGORY_LABELS = {
	"chemical": "Chemical",
	"manpower": "Manpower",
	"spare_part": "Spare Part",
	"other": "Other",
}
COST_FIELDS = (
	"treated_water",
	"chemical_cost",
	"manpower_cost",
	"spare_part_cost",
	"other_cost",
	"total_cost",
)
DETAIL_LIMIT = 2000  # max DOR-level rows sent to the browser
ANOMALY_LIMIT = 15
ANOMALY_MIN_ROWS = 8
ANOMALY_SIGMA = 2


@frappe.whitelist()
def get_dashboard_data(filters=None):
	frappe.has_permission("Daily Operation Report", "read", throw=True)

	filters = frappe._dict(frappe.parse_json(filters) if filters else {})

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("Please set a From Date and To Date"))

	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	if from_date > to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	project = filters.get("project") or None
	exclude_zero = cint(filters.get("exclude_zero"))
	compare = cint(filters.get("compare"))

	rows = fetch_rows(from_date, to_date, project, exclude_zero)

	days = date_diff(to_date, from_date) + 1
	period = {"from_date": str(from_date), "to_date": str(to_date), "days": days}

	previous_period = None
	previous_kpis = None
	if compare:
		prev_to = add_days(from_date, -1)
		prev_from = add_days(prev_to, -(days - 1))
		previous_period = {"from_date": str(prev_from), "to_date": str(prev_to), "days": days}
		previous_kpis = get_overall(fetch_rows(prev_from, prev_to, project, exclude_zero))

	kpis = get_overall(rows)

	monthly = aggregate(
		rows,
		key_fn=lambda r: r["month_sort"],
		label_fn=lambda r: {"month_sort": r["month_sort"], "month_label": r["month_label"]},
	)

	projects = aggregate(
		rows,
		key_fn=lambda r: r["project"] or "",
		label_fn=lambda r: {
			"project": r["project"] or "",
			"project_name": r["project_name"] or r["project"] or _("(No Project)"),
		},
	)
	projects.sort(key=lambda g: g["total_cost"], reverse=True)

	daily = aggregate(
		rows,
		key_fn=lambda r: r["date"],
		label_fn=lambda r: {"date": r["date"]},
	)

	detail = sorted(rows, key=lambda r: (r["date"], r["dor"]), reverse=True)

	return {
		"period": period,
		"previous_period": previous_period,
		"kpis": kpis,
		"previous_kpis": previous_kpis,
		"monthly": monthly,
		"projects": projects,
		"daily": daily,
		"rows": detail[:DETAIL_LIMIT],
		"rows_truncated": len(detail) > DETAIL_LIMIT,
		"row_count": len(detail),
		"anomalies": find_anomalies(rows),
		"currency": frappe.defaults.get_global_default("currency"),
		"generated_at": now_datetime().strftime("%Y-%m-%d %H:%M"),
	}


# ------------------------------------------------------------
# Data
# ------------------------------------------------------------
def fetch_rows(from_date, to_date, project, exclude_zero):
	conditions = ["dor.docstatus = 1", "dor.date BETWEEN %(from_date)s AND %(to_date)s"]
	values = {"from_date": from_date, "to_date": to_date}

	if project:
		conditions.append("dor.project = %(project)s")
		values["project"] = project

	if exclude_zero:
		conditions.append("dor.waste_water_treated_volume > 0")

	where_clause = " AND ".join(conditions)

	raw = frappe.db.sql(
		f"""
		SELECT
			dor.name AS dor,
			dor.date AS date,
			dor.project AS project,
			proj.project_name AS project_name,
			dor.waste_water_treated_volume AS treated_water,
			COALESCE(chem.chemical_cost, 0) AS chemical_cost,
			COALESCE(dor.manpower_cost_per_treated_water, 0) AS manpower_cost,
			COALESCE(dor.spare_part_cost_per_treated_water, 0) AS spare_part_cost,
			COALESCE(dor.other_cost_per_treated_water, 0) AS other_cost
		FROM `tabDaily Operation Report` dor
		LEFT JOIN `tabProject` proj ON proj.name = dor.project
		LEFT JOIN (
			SELECT parent, SUM(chemical_used_amount) AS chemical_cost
			FROM `tabChemical Usage Table`
			GROUP BY parent
		) chem ON chem.parent = dor.name
		WHERE {where_clause}
		ORDER BY dor.date ASC
		""",
		values,
		as_dict=1,
	)

	rows = []
	for r in raw:
		row = {
			"dor": r.dor,
			"date": str(r.date) if r.date else "",
			"project": r.project or "",
			"project_name": r.project_name or "",
			"month_sort": r.date.strftime("%Y-%m") if r.date else "",
			"month_label": r.date.strftime("%b %Y") if r.date else "",
			"treated_water": flt(r.treated_water),
			"chemical_cost": flt(r.chemical_cost),
			"manpower_cost": flt(r.manpower_cost),
			"spare_part_cost": flt(r.spare_part_cost),
			"other_cost": flt(r.other_cost),
		}
		row["total_cost"] = (
			row["chemical_cost"] + row["manpower_cost"] + row["spare_part_cost"] + row["other_cost"]
		)
		finalize(row)
		rows.append(row)

	return rows


def finalize(g):
	"""Add every <category>_cost_per_m3 + total_cost_per_m3 to a dict that
	already holds treated_water and the cost sums."""
	tw = g["treated_water"]
	for category in CATEGORIES:
		key = f"{category}_cost"
		g[f"{key}_per_m3"] = flt(g[key] / tw) if tw else 0
	g["total_cost_per_m3"] = flt(g["total_cost"] / tw) if tw else 0
	return g


def new_group(**labels):
	g = {field: 0 for field in COST_FIELDS}
	g["dor_count"] = 0
	g.update(labels)
	return g


def add_row(g, row):
	for field in COST_FIELDS:
		g[field] += row[field]
	g["dor_count"] += 1


def aggregate(rows, key_fn, label_fn):
	groups = {}
	for row in rows:
		key = key_fn(row)
		g = groups.get(key)
		if g is None:
			g = groups[key] = new_group(**label_fn(row))
		add_row(g, row)
	return [finalize(groups[key]) for key in sorted(groups)]


def get_overall(rows):
	if not rows:
		return None

	g = new_group()
	for row in rows:
		add_row(g, row)
	finalize(g)

	days_with_data = len({row["date"] for row in rows})
	g["days_with_data"] = days_with_data
	g["avg_daily_volume"] = flt(g["treated_water"] / days_with_data) if days_with_data else 0
	return g


# ------------------------------------------------------------
# Anomalies: DORs whose total cost/M3 is more than N sigma above the
# mean of the selected period (needs a minimum number of DORs).
# ------------------------------------------------------------
def find_anomalies(rows):
	valid = [r for r in rows if r["treated_water"] > 0]
	if len(valid) < ANOMALY_MIN_ROWS:
		return {"items": [], "threshold": 0, "mean": 0}

	values = [r["total_cost_per_m3"] for r in valid]
	mean = statistics.fmean(values)
	sd = statistics.pstdev(values)
	if not sd:
		return {"items": [], "threshold": 0, "mean": mean}

	threshold = mean + ANOMALY_SIGMA * sd
	category_means = {
		c: statistics.fmean([r[f"{c}_cost_per_m3"] for r in valid]) for c in CATEGORIES
	}

	items = []
	for r in valid:
		value = r["total_cost_per_m3"]
		if value <= threshold:
			continue
		driver = max(CATEGORIES, key=lambda c: r[f"{c}_cost_per_m3"] - category_means[c])
		items.append(
			{
				"dor": r["dor"],
				"date": r["date"],
				"project": r["project"],
				"project_name": r["project_name"] or r["project"],
				"treated_water": r["treated_water"],
				"total_cost_per_m3": value,
				"mean": mean,
				"pct_above": flt((value - mean) / mean * 100) if mean else 0,
				"driver": _(CATEGORY_LABELS[driver]),
			}
		)

	items.sort(key=lambda x: x["total_cost_per_m3"], reverse=True)
	return {"items": items[:ANOMALY_LIMIT], "threshold": threshold, "mean": mean}