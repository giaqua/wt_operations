# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data, 


def get_columns(filters):
	if filters.get("show_Lead_Id"):
		columns = [
			{"label": "Lead Id", "fieldname": "lead_id", "fieldtype": "Link", "options": "Lead", "width": 100},
			{"label": "Lead", "fieldname": "lead_name", "fieldtype": "Link", "options": "Lead", "width": 200},
			{"label": "No", "fieldname": "no", "fieldtype": "Int", "width": 50},
			{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 120},
			{"label": "Action", "fieldname": "action", "fieldtype": "Data", "width": 150},
			{"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Link", "options": "Employee", "width": 150},
			{"label": "Status", "fieldname": "status", "fieldtype": "Link", "options": "Lead Action Status", "width": 100},
			{"label": "Feedback Status", "fieldname": "feedback_status", "fieldtype": "Data", "width": 120},
			{"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 80},
			{"label": "Feedback", "fieldname": "feedback", "fieldtype": "Data", "width": 200},

		]
	else:
		columns = [
			{"label": "Lead", "fieldname": "lead_name", "fieldtype": "Link", "options": "Lead", "width": 200},
			{"label": "No", "fieldname": "no", "fieldtype": "Int", "width": 50},
			{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 120},
			{"label": "Action", "fieldname": "action", "fieldtype": "Data", "width": 150},
			{"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Link", "options": "Employee", "width": 150},
			{"label": "Status", "fieldname": "status", "fieldtype": "Link", "options": "Lead Action Status", "width": 100},
			{"label": "Feedback Status", "fieldname": "feedback_status", "fieldtype": "Data", "width": 120},
			{"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 80},
			{"label": "Feedback", "fieldname": "feedback", "fieldtype": "Data", "width": 200},

		]
	if filters.get("show_details"):
		columns.append({"label": "Action Details", "fieldname": "action_details", "fieldtype": "Text Editor", "width": 200})
	# if filters.get("include_feedback_details"):
		columns.append({"label": "Feedback Details", "fieldname": "feedback_details", "fieldtype": "Data", "width": 200})

	return columns


def get_data(filters):
	conditions = get_conditions(filters)
	sql = """SELECT
		leads.company_name AS lead_name,
		leads.name AS lead_id,
		actions.action,
		actions.due_date,
		actions.idx AS no,
		actions.priority AS priority,
		emp.employee_name AS sales_person,
		actions.status AS status,
		actions.feedback_status AS feedback_status,
		actions.feedback AS feedback,
		actions.action_details AS action_details,
		actions.feedback_details AS feedback_details
	FROM
		`tabLead` leads,`tabLead Actions` actions
		LEFT JOIN `tabEmployee` emp ON actions.sales_person = emp.name
	WHERE
		leads.name = actions.parent
	"""
	sql += conditions
	data = frappe.db.sql(sql, as_dict=True)
	return data


def get_conditions(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	sales_person = filters.get("sales_person")
	lead = filters.get("lead")
	feedback_status = filters.get("feedback_status")
	status = filters.get("status")
	priority = filters.get("priority")
	conditions = ""
	if filters.get("from_date"):
		conditions += " AND actions.due_date >= " + "'" + from_date + "'"
	if filters.get("to_date"):
		conditions += " AND actions.due_date <= " + "'" + to_date + "'"
	if filters.get("sales_person"):
		conditions += " AND actions.sales_person = " + "'" + sales_person + "'"
	if filters.get("lead"):
		conditions += " AND actions.parent = " + "'" + lead + "'"
	if filters.get("feedback_status"):
		conditions += " AND actions.feedback_status = " + "'" + feedback_status + "'"
	if filters.get("status"):
		conditions += " AND actions.status = " + "'" + status + "'"
	if filters.get("priority"):
		conditions += " AND actions.priority = " + "'" + priority + "'"
	return conditions
