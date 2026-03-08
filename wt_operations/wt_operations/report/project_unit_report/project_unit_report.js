frappe.query_reports["Project unit Report"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
           
        },
        {
            fieldname: "unit",
            label: __("Unit"),
            fieldtype: "Link",
            options: "Project Unit",
            
        },
        {
            fieldname: "year",
            label: __("Year"),
            fieldtype: "Int",
            default: new Date().getFullYear(),
            reqd: 1
        },
        {
            fieldname: "month",
            label: __("Month"),
            fieldtype: "Select",
            options: [
                "01", "02", "03", "04", "05", "06",
                "07", "08", "09", "10", "11", "12"
            ],
            default: ("0" + (new Date().getMonth() + 1)).slice(-2),
            reqd: 1
        }
    ],
    onload: function(report) {
        // Automatically run the report on load
        frappe.query_report.refresh();
    }
};
