// Copyright (c) 2026, Takamol and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Operation Summery"] = {
	"filters": [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			reqd: 0
		},
		{
			fieldname: "project_unit_assignment",
			label: __("Project Unit Assignment"),
			fieldtype: "Link",
			options: "Project Unit Assignment",
			reqd: 0,
			get_query: () => {
				if (frappe.query_report.get_filter_value('project')) {
					let project = frappe.query_report.get_filter_value('project');
					return {
						filters: {
							'project': project
						}
					};
				}
			}
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 0
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 0
		}
	]
};
