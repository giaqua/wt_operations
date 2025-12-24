# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data


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

		if row.achieved_operations == 100:
			row.pending_with = "Completed"
			row["__color"] = "#4caf50"
	
	return data