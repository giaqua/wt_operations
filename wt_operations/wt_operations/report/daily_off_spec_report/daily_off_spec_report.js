// Copyright (c) 2026, HM
// For license information, please see license.txt

frappe.query_reports["Daily Off-Spec Report"] = {
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
            fieldtype: "Data",
            // If "unit" on Daily Operation Report is actually a Link to a
            // "Project Unit" doctype rather than plain text, change fieldtype
            // to "Link" and add options: "Project Unit" (or your doctype name),
            // and consider filtering it by the selected project.
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "parameter",
            label: __("Parameter"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return [
                    { value: "COD", description: "" },
                    { value: "pH", description: "" },
                    { value: "TSS", description: "" },
                    { value: "Turbidity.", description: "" },
                    { value: "TDS.", description: "" },
                ].filter((d) => d.value.toLowerCase().includes((txt || "").toLowerCase()));
            },
        },
    ],
};