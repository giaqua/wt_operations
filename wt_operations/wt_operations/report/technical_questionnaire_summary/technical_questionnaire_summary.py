# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	report_summary,primitive_summary = get_summary_data(data, "pending_with")
	# chart = get_chart_data(data)
	message = None
	chart = None
	# frappe.local.response.chart = chart
	return columns, data,message, chart,report_summary,primitive_summary

def get_chart_data(data):
	labels = []
	datasets = [
		{
			"name": "Achieved Operations",
			"values": [],
		},
		{
			"name": "Pending Operations",
			"values": [],
		},
	]

	for row in data:
		# print(row,"=========================",data)
		labels.append(row.technical_questionnaire)
		datasets[0]["values"].append(row.achieved_operations)
		datasets[1]["values"].append(row.pending_operations)

	chart = {
		"data": {
			"labels": labels,
			"datasets": datasets,
		},
		"type": "bar",
		"colors": ["#4caf50", "#f44336"],
	}
	return chart
# def get_chart_data(data):
# 	labels = []
# 	datasets = [
# 		{
# 			"name": "Achieved Operations",
# 			"values": [],
# 		},
# 		{
# 			"name": "Pending Operations",
# 			"values": [],
# 		},
# 	]

# 	for key, values in summary.items():
# 		labels.append(key)
# 		datasets[0]["values"].append(values["achieved_operations"] / values["count"])
# 		datasets[1]["values"].append(values["pending_operations"] / values["count"])

# 	chart = {
# 		"data": {
# 			"labels": labels,
# 			"datasets": datasets,
# 		},
# 		"type": "bar",
# 		"colors": ["#4caf50", "#f44336"],
# 	}
# 	return chart

def get_summary_data(data, group_by):
	summary = {}
	# print(data,"=================data==================")
	total_count = len(data)
	for row in data:
		key = row.get(group_by)
		if key not in summary:
			summary[key] = {
				"achieved_operations": 0,
				"pending_operations": 0,
				"count": 0
			}
		summary[key]["achieved_operations"] += row.get("achieved_operations", 0)
		summary[key]["pending_operations"] += row.get("pending_operations", 0)
		summary[key]["count"] += 1
	all_summary = []
	for key, values in summary.items():
		all_summary.append({
			"value": values["count"],
			"label": key,
			"indicator": "green" if key == "Completed" else "Black",
			"datatype": "float",
		}
	)
	all_summary.append({
			"value": total_count,
			"label": "Total",
			"datatype": "float",
			"indicator": "Blue"
		}
	)
	# print(all_summary,"=================summary==================")
	return all_summary,(total_count)


def get_columns(filters):
	columns = [
		{
			"fieldname": "lead_name",
			"label": "Lead",
			"fieldtype": "Link",
			"options": "Lead",
			"width": 140,
		},
		{
			"fieldname": "technical_questionnaire",
			"label": """Technical Questionnaire""",
			"fieldtype": "Link",
			"options": "WWTP Technical Questionnaire",
			"width": 180,
		},
		{
			"fieldname": "achieved_operations",
			"label": "Achieved Operations",
			"fieldtype": "Percent",
			"width": 140,
			"precision": 1
		},
		{
			"fieldname": "pending_operations",
			"label": "Pending Operations",
			"fieldtype": "Percent",
			"width": 140,
			"precision": 1
		},
		{
			"fieldname": "pending_with",
			"label": "Pending With",
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "visit_request",
			"label": "Visit Request(Sales)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "site_visit",
			"label": "Site Visit(Sales)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "water_sample",
			"label": "Water Sample(Sales)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "lab_test_result",
			"label": "Lab Test Result(Lab)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "technical_proposal",
			"label": "Technical Proposal(Technical)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "customer_proposal",
			"label": "Customer Proposal(Sales)",
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "request_for_proposal",
			"label": "Request For Proposal(Sales)",
			"fieldtype": "Int",
			"width": 140,
		},
	]
	
	department = filters.get("department")
	if department:
		if department == "Sales":
			columns = [col for col in columns if col["fieldname"] not in ["lab_test_result", "technical_proposal"]]
		elif department == "Technical":
			columns = [col for col in columns if col["fieldname"] not in ["visit_request", "site_visit", "water_sample", "lab_test_result", "customer_proposal", "request_for_proposal"]]
		elif department == "Lab":
			columns = [col for col in columns if col["fieldname"] not in ["visit_request", "site_visit", "water_sample", "technical_proposal", "customer_proposal", "request_for_proposal"]]
	
	return columns



def get_data(filters):	
	technical_questionnaire = filters.get("technical_qquestionnaire")
	lead = filters.get("lead")
	hide_completed_operations = filters.get("hide_completed_operations")
	sql = """
		Select
			ld.company_name as lead_name,
			wtq.name as technical_questionnaire,
			wtq.site_visit_required as site_visit_required,
			wtq.sample_collection_required as sample_collection_required,
			wtq.opportunity as opportunity,
			count(svr.name) as visit_request,
			count(sv.name) as site_visit,
			count(ws.name) as water_sample,
			count(ltr.name) as lab_test_result,
			count(wtp.name) as technical_proposal,
			count(cp.name) as customer_proposal,
			count(rfp.name) as request_for_proposal,
			ROUND((count(svr.name)+count(sv.name)+count(ws.name)+count(ltr.name)+count(wtp.name)+count(rfp.name)+count(cp.name))/7*100, 1) as achieved_operations,
			(100-ROUND((count(svr.name)+count(sv.name)+count(ws.name)+count(ltr.name)+count(wtp.name)+count(rfp.name)+count(cp.name))/7*100, 1)) as pending_operations
		From
			`tabLead` ld, `tabWWTP Technical Questionnaire` wtq
			LEFT JOIN `tabSite Visit Request` svr 
			ON wtq.name = svr.technical_questionnaire and svr.docstatus = 1
			LEFT JOIN `tabSite Visit` sv 
			On wtq.name = sv.wwtp_technical_questionnaire and sv.docstatus = 1
			LEFT JOIN `tabWater Sample` ws
			On wtq.name = ws.wwtp_technical_questionnaire and ws.docstatus = 1
			LEFT JOIN `tabLab Test Result` ltr
			On ws.name = ltr.sample_tag and ws.docstatus = 1
			LEFT JOIN `tabWWTP Technical Proposal` wtp
			On wtq.name = wtp.wwtp_technical_questionnaire and wtp.docstatus = 1
			LEFT JOIN `tabCustomer Proposal` cp
			On  wtp.name = cp.wwtp_technical_proposal
			LEFT JOIN `tabRequest For Proposal` rfp
			On  wtq.name = rfp.technical_questionnaire and rfp.docstatus = 1
		Where
			wtq.lead = ld.name and wtq.docstatus = 1
		"""
	if technical_questionnaire:
		sql += " and wtq.name = %(technical_questionnaire)s"
	if lead:
		sql += " and ld.name = %(lead)s"
	
	
	sql = sql + " group by wtq.name"

	if hide_completed_operations:
		sql += " HAVING  ((count(svr.name)+count(sv.name)+count(ws.name)+count(ltr.name)+count(wtp.name)+count(rfp.name)+count(cp.name))/7*100) < '100'"
	data = frappe.db.sql(sql,
			{"technical_questionnaire": technical_questionnaire, "lead": lead},
			as_dict=1,
		)

	print(data)

	for row in data:
		print(row.site_visit_required,"========row.site_visit_required=========",row)
		if row.site_visit_required and row.sample_collection_required:
			print("========if=========")
			if row.visit_request == 0:
				row.pending_with = "Sales"
			elif row.site_visit == 0 and row.site_visit == 0:
				row.pending_with = "Sales"
			elif row.water_sample == 0 and row.water_sample == 0:
				row.pending_with = "Sales"
			elif row.lab_test_result == 0 and row.lab_test_result == 0:
				row.pending_with = "Lab"
			elif row.technical_proposal == 0:
				row.pending_with = "Technical"
			elif row.customer_proposal == 0 and row.customer_proposal == 0:
				row.pending_with = "Sales"
		
		else:
			if row.technical_proposal == 0:
				row.pending_with = "Technical"
			elif row.customer_proposal == 0 and row.customer_proposal == 0:
				row.pending_with = "Sales"

		if row.achieved_operations == 100:
			row.pending_with = "Completed"
			row["__color"] = "#4caf50"

		# department = filters.get("department")
		# if department:
		# 	if department == "Sales" and row.pending_with not in ["Sales"]:
		# 		data.remove(row)
		# 	elif department == "Technical" and row.pending_with not in ["Technical"]:
		# 		data.remove(row)
		# 	elif department == "Lab" and row.pending_with not in ["Lab"]:
		# 		data.remove(row)
	
	return data