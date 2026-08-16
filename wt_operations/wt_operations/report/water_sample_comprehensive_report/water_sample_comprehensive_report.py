# Copyright (c) 2026, HM
# Water Sample Comprehensive Report
# One row per (sample x parameter) reading, with compliance vs contract limit.

import io
import json
from calendar import monthrange

import frappe
from frappe import _
from frappe.utils.pdf import get_pdf


def execute(filters=None):
	filters = filters or {}
	data = get_data(filters)
	columns, rows = get_pivoted_columns_and_rows(data)
	return columns, rows


def param_fieldname(param):
	"""Turns a parameter name like 'Turbidity.' or 'pH' into a safe dict key,
	e.g. 'param_turbidity', 'param_ph'."""
	import re

	slug = re.sub(r"[^0-9a-zA-Z]+", "_", param.strip().lower()).strip("_")
	return "param_{0}".format(slug)


def get_pivoted_columns_and_rows(data):
	"""Builds the report grid as one row per SAMPLE, with one column per
	distinct PARAMETER (e.g. COD, pH, TSS, ...) instead of one row per
	(sample x parameter) reading."""
	parameters = sorted({row.get("parameter") for row in data if row.get("parameter")})

	columns = [
		{"label": _("Sample ID"), "fieldname": "sample_id", "fieldtype": "Link",
			"options": "Project Operation Water Sample", "width": 110},
		{"label": _("Site/Project"), "fieldname": "site", "fieldtype": "Link",
			"options": "Project", "width": 110},
		{"label": _("Sampling Date"), "fieldname": "sampling_date", "fieldtype": "Date", "width": 100},
		{"label": _("Sample Process Location"), "fieldname": "sample_process_location", "fieldtype": "Data", "width": 150},
		{"label": _("Water Source"), "fieldname": "water_source", "fieldtype": "Data", "width": 90},
		{"label": _("Sample Type"), "fieldname": "sample_type", "fieldtype": "Data", "width": 90},
		{"label": _("Workflow State"), "fieldname": "workflow_state", "fieldtype": "Data", "width": 100},
		# {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		# {"label": _("Responsible"), "fieldname": "responsible", "fieldtype": "Link",
		# 	"options": "User", "width": 130},
		{"label": _("Result Shared"), "fieldname": "result_shared_date", "fieldtype": "Date", "width": 100},
	]
	for param in parameters:
		columns.append({
			"label": param,
			"fieldname": param_fieldname(param),
			"fieldtype": "Float",
			"width": 95,
			"precision": 2,
		})

	from collections import OrderedDict

	samples = OrderedDict()
	for row in data:
		sid = row["sample_id"]
		if sid not in samples:
			samples[sid] = {
				"sample_id": sid,
				"site": row.get("site"),
				"sampling_date": row.get("sampling_date"),
				"sample_process_location": row.get("sample_process_location"),
				"water_source": row.get("water_source"),
				"sample_type": row.get("sample_type"),
				"workflow_state": row.get("workflow_state"),
				"status": row.get("status"),
				"responsible": row.get("responsible"),
				"result_shared_date": row.get("result_shared_date"),
			}
		samples[sid][param_fieldname(row["parameter"])] = row.get("inlet")

	rows = list(samples.values())
	rows.sort(key=lambda r: (r.get("sampling_date") or frappe.utils.getdate("1900-01-01")), reverse=True)

	return columns, rows


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("site"):
		conditions.append("p.site = %(site)s")
		values["site"] = filters.get("site")

	if filters.get("from_date"):
		conditions.append("p.sampling_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("p.sampling_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("water_source"):
		conditions.append("p.water_source = %(water_source)s")
		values["water_source"] = filters.get("water_source")

	if filters.get("sample_process_location"):
		conditions.append("p.sample_process_location like %(sample_process_location)s")
		values["sample_process_location"] = "%{0}%".format(filters.get("sample_process_location"))

	if filters.get("sample_type"):
		conditions.append("p.sample_type = %(sample_type)s")
		values["sample_type"] = filters.get("sample_type")

	if filters.get("parameter"):
		conditions.append("d.parameter = %(parameter)s")
		values["parameter"] = filters.get("parameter")

	if filters.get("workflow_state"):
		conditions.append("p.workflow_state = %(workflow_state)s")
		values["workflow_state"] = filters.get("workflow_state")

	if filters.get("status"):
		conditions.append("p.status = %(status)s")
		values["status"] = filters.get("status")

	if filters.get("responsible"):
		conditions.append("p.responsible = %(responsible)s")
		values["responsible"] = filters.get("responsible")

	condition_str = (" and " + " and ".join(conditions)) if conditions else ""
	return condition_str, values


def get_data(filters):
	condition_str, values = get_conditions(filters)

	query = """
		select
			p.name as sample_id,
			p.site,
			p.sampling_date,
			p.sample_process_location,
			p.water_source,
			p.sample_type,
			p.reason,
			p.responsible,
			p.status,
			p.workflow_state,
			p.result_shared_date,
			p.lab_receiving_date,
			d.parameter,
			d.unit,
			d.inlet,
			d.contract_inlet
		from `tabProject Operation Water Sample` p
		inner join `tabSample Collection Details` d on d.parent = p.name
		where 1=1 {conditions}
		order by p.sampling_date desc, p.name, d.idx
	""".format(conditions=condition_str)

	data = frappe.db.sql(query, values, as_dict=True)

	for row in data:
		row["compliance_status"] = get_compliance_status(row)

	# compliance is computed post-query (not a raw column), so filter here
	if filters.get("compliance_status"):
		data = [r for r in data if r.get("compliance_status") == filters.get("compliance_status")]

	return data


def get_compliance_status(row):
	"""
	NOTE: adjust this logic to match your actual QC rules.
	Default assumption: higher result than contract_inlet = Exceeds (fail),
	except pH which is treated as an acceptable range of 6-9.
	"""
	param = (row.get("parameter") or "").strip().lower().rstrip(".")
	inlet = row.get("inlet")
	limit = row.get("contract_inlet")

	if inlet is None:
		return ""

	if param == "ph":
		if inlet < 6 or inlet > 9:
			return "Exceeds"
		return "Pass"

	if limit in (None, 0):
		return ""

	if inlet > limit:
		return "Exceeds"
	return "Pass"


def build_pivot(data):
	"""Pivots the flat (sample x parameter) rows into a wide format:
	one row per sample, one column per parameter.
	Returns (months, parameters) where:
	  parameters = sorted list of distinct parameter names (used as column titles)
	  months = [ { month_label: 'April 2026', samples: [
			{ sample_id, site, sampling_date, ..., values: { 'COD': {inlet, unit, compliance_status}, ... } }
	  ] } ] sorted chronologically."""
	from collections import OrderedDict

	parameters = sorted({row.get("parameter") for row in data if row.get("parameter")})

	months = OrderedDict()
	for row in data:
		d = row.get("sampling_date")
		if d:
			dt = frappe.utils.getdate(d) if isinstance(d, str) else d
			month_key = dt.strftime("%Y-%m")
			month_label = dt.strftime("%B %Y")
		else:
			month_key = "0000-00"
			month_label = "No Date"

		if month_key not in months:
			months[month_key] = {"month_label": month_label, "samples": OrderedDict()}

		sid = row["sample_id"]
		if sid not in months[month_key]["samples"]:
			months[month_key]["samples"][sid] = {
				"sample_id": sid,
				"site": row.get("site"),
				"sampling_date": row.get("sampling_date"),
				"sample_process_location": row.get("sample_process_location"),
				"water_source": row.get("water_source"),
				"sample_type": row.get("sample_type"),
				"workflow_state": row.get("workflow_state"),
				"responsible": row.get("responsible"),
				"values": {},
			}
		months[month_key]["samples"][sid]["values"][row["parameter"]] = {
			"inlet": row.get("inlet"),
			"unit": row.get("unit"),
			"compliance_status": row.get("compliance_status"),
		}

	month_list = []
	for month_key in sorted(months.keys()):
		entry = months[month_key]
		samples = list(entry["samples"].values())
		# fill every parameter for every sample (defaulting to None) so the
		# template can use plain subscript access - Frappe's sandboxed Jinja
		# blocks calling dict.get() directly inside templates
		for s in samples:
			for param in parameters:
				s["values"].setdefault(param, None)
		entry["samples"] = samples
		month_list.append(entry)

	return month_list, parameters


# ---------------------------------------------------------------------------
# Print (PDF) - server-side generation, triggered from a page button
# ---------------------------------------------------------------------------
#
# get_print_pdf_base64() is a normal @frappe.whitelist() python function called
# via frappe.call() (POST, JSON) from the client - not a raw download link.
# It builds the PDF server-side and hands the browser back base64 bytes, which
# the client turns into a blob and opens in a new tab with the browser's native
# print dialog triggered automatically.
#
# The PDF groups all results by month (e.g. "April 2026") with every sample
# for that month listed underneath, and pivots parameters into columns (one
# column per parameter, e.g. COD / pH / TSS / ...) instead of one row each.

@frappe.whitelist()
def get_print_pdf_base64(filters=None):
	import base64

	filters = json.loads(filters) if filters else {}
	data = get_data(filters)
	months, parameters = build_pivot(data)

	html = frappe.render_template(
		"wt_operations/wt_operations/report/water_sample_comprehensive_report/print_template.html",
		{
			"months": months,
			"parameters": parameters,
			"filters": filters,
			"total_readings": len(data),
			"exceed_count": len([r for r in data if r.get("compliance_status") == "Exceeds"]),
			"generated_on": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M"),
		},
	)

	pdf = get_pdf(html)
	return base64.b64encode(pdf).decode("utf-8")


@frappe.whitelist()
def download_print_pdf(filters=None):
	"""Kept as a plain GET download link too, in case you want a direct
	'save as PDF' link somewhere instead of the print-dialog flow above."""
	filters = json.loads(filters) if filters else {}
	data = get_data(filters)
	months, parameters = build_pivot(data)

	html = frappe.render_template(
		"wt_operations/wt_operations/report/water_sample_comprehensive_report/print_template.html",
		{
			"months": months,
			"parameters": parameters,
			"filters": filters,
			"total_readings": len(data),
			"exceed_count": len([r for r in data if r.get("compliance_status") == "Exceeds"]),
			"generated_on": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M"),
		},
	)

	pdf = get_pdf(html)
	frappe.local.response.filename = "Water_Sample_Report_{0}.pdf".format(frappe.utils.nowdate())
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


# ---------------------------------------------------------------------------
# Export to Excel - openpyxl, styled to mirror the print layout
# ---------------------------------------------------------------------------

@frappe.whitelist()
def download_excel(filters=None):
	filters = json.loads(filters) if filters else {}
	data = get_data(filters)
	months, parameters = build_pivot(data)

	from openpyxl import Workbook
	from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
	from openpyxl.utils import get_column_letter

	wb = Workbook()
	ws = wb.active
	ws.title = "Water Sample Report"

	header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
	month_fill = PatternFill(start_color="12324F", end_color="12324F", fill_type="solid")
	header_font = Font(color="FFFFFF", bold=True, size=10)
	title_font = Font(bold=True, size=14, color="1F4E78")
	thin = Side(style="thin", color="B7B7B7")
	border = Border(left=thin, right=thin, top=thin, bottom=thin)

	fixed_cols = ["Sample ID", "Date", "Location", "Source", "Type", "State", "Responsible"]
	all_cols = fixed_cols + parameters
	ncols = len(all_cols)

	fail_fill = PatternFill(start_color="FCE4E4", end_color="FCE4E4", fill_type="solid")
	pass_fill = PatternFill(start_color="E4F7E4", end_color="E4F7E4", fill_type="solid")

	ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
	title_cell = ws.cell(row=1, column=1, value="Water Sample Comprehensive Report")
	title_cell.font = title_font
	title_cell.alignment = Alignment(horizontal="center")

	ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
	sub_cell = ws.cell(
		row=2, column=1,
		value="Generated on {0}".format(frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M")),
	)
	sub_cell.alignment = Alignment(horizontal="center")
	sub_cell.font = Font(italic=True, size=9, color="666666")

	row_num = 4
	for m in months:
		ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=ncols)
		month_cell = ws.cell(row=row_num, column=1, value=m["month_label"])
		month_cell.fill = month_fill
		month_cell.font = Font(color="FFFFFF", bold=True, size=11)
		month_cell.alignment = Alignment(horizontal="left", vertical="center")
		row_num += 1

		header_row = row_num
		for idx, col_label in enumerate(all_cols, start=1):
			cell = ws.cell(row=header_row, column=idx, value=col_label)
			cell.fill = header_fill
			cell.font = header_font
			cell.alignment = Alignment(horizontal="center", vertical="center")
			cell.border = border
		row_num += 1

		for s in m["samples"]:
			fixed_values = [
				s["sample_id"], s["sampling_date"], s["sample_process_location"],
				s["water_source"], s["sample_type"], s["workflow_state"], s["responsible"],
			]
			for idx, value in enumerate(fixed_values, start=1):
				cell = ws.cell(row=row_num, column=idx, value=value)
				cell.border = border

			for offset, param in enumerate(parameters, start=1):
				idx = len(fixed_cols) + offset
				v = s["values"].get(param)
				cell = ws.cell(row=row_num, column=idx, value=(v["inlet"] if v else None))
				cell.border = border
				if v:
					if v["compliance_status"] == "Exceeds":
						cell.fill = fail_fill
						cell.font = Font(color="C00000", bold=True)
					elif v["compliance_status"] == "Pass":
						cell.fill = pass_fill
						cell.font = Font(color="1E7B1E", bold=True)
			row_num += 1

		row_num += 1  # blank spacer row between months

	for idx in range(1, ncols + 1):
		ws.column_dimensions[get_column_letter(idx)].width = 16

	ws.freeze_panes = "A5"

	buffer = io.BytesIO()
	wb.save(buffer)
	buffer.seek(0)

	frappe.response["filename"] = "Water_Sample_Report_{0}.xlsx".format(frappe.utils.nowdate())
	frappe.response["filecontent"] = buffer.getvalue()
	frappe.response["type"] = "binary"


# ---------------------------------------------------------------------------
# Monthly Print (Detailed) - all samples for a given month, grouped by sample
# ---------------------------------------------------------------------------

@frappe.whitelist()
def download_monthly_pdf(month, year, site=None):
	month = int(month)
	year = int(year)

	start_date = "{0}-{1:02d}-01".format(year, month)
	end_date = "{0}-{1:02d}-{2}".format(year, month, monthrange(year, month)[1])

	filters = {"from_date": start_date, "to_date": end_date}
	if site:
		filters["site"] = site

	data = get_data(filters)
	months, parameters = build_pivot(data)

	total_readings = len(data)
	exceed_count = len([r for r in data if r.get("compliance_status") == "Exceeds"])

	html = frappe.render_template(
		"wt_operations/wt_operations/report/water_sample_comprehensive_report/print_template.html",
		{
			"months": months,
			"parameters": parameters,
			"total_readings": total_readings,
			"exceed_count": exceed_count,
			"generated_on": frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M"),
		},
	)

	pdf = get_pdf(html)
	frappe.local.response.filename = "Water_Sample_Monthly_Report_{0}_{1:02d}.pdf".format(year, month)
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"