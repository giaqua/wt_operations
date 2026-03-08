frappe.query_reports["Daily Operation Summary Report"] = {
    filters: [
        {
            fieldname: "start_date",
            label: "Start Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "end_date",
            label: "End Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "project",
            label: "Project",
            fieldtype: "Link",
            options: "Project"
        },
        {
            fieldname: "unit",
            label: "Unit",
            fieldtype: "Link",
            options: "Project Unit"
        },
        {
            fieldname: "unit_assignment_record",
            label: "Project Unit Assignment",
            fieldtype: "Link",
            options: "Project Unit Assignment"
        },
        
        {
            fieldname: "group_by",
            label: "Group By",
            fieldtype: "Select",
            options: "\nproject\nunit",
            default: "project"
        }
    ]
};
