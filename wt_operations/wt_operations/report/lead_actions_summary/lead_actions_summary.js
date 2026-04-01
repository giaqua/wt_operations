// Copyright (c) 2026, Takamol and contributors
// For license information, please see license.txt

frappe.query_reports["Lead Actions Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Employee",
			"query": "frappe.desk.search.search_link",
			"get_query": function() {
				return {
					filters: {
						department: "Sales - GIS",
						status: "Active"
					}
				};
			}
		},
		{
			"fieldname": "lead",
			"label": __("Lead"),
			"fieldtype": "Link",
			"options": "Lead"
		},
		{
			"fieldname": "feedback_status",
			"label": __("Feedback Status"),
			"fieldtype": "Select",
			"options": "\nPending\nRejected\nApproved"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Link",
			"options": "Lead Action Status"
		},
		{
			"fieldname": "priority",
			"label": __("Priority"),
			"fieldtype": "Select",
			"options": "\nLow\nMedium\nHigh"
		},
		{
			"fieldname": "show_details",
			"label": __("Show Details"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "show_Lead_Id",
			"label": __("Show Lead Id"),
			"fieldtype": "Check",
			"default": 1
		}
	]
};
