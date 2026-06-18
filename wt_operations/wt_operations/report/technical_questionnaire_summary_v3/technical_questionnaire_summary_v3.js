frappe.query_reports["Technical Questionnaire Summary V3"] = {
    "filters": [
        {
            fieldname: "technical_qquestionnaire",
            label: __("Technical Questionnaire"),
            fieldtype: "Link",
            options: "WWTP Technical Questionnaire",
            reqd: 0
        },
        {
            fieldname: "lead",
            label: __("Lead"),
            fieldtype: "Link",
            options: "Lead",
            reqd: 0
        },
        {
            fieldname: "hide_completed_operations",
            label: __("Hide Completed Operations"),
            fieldtype: "Check"
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Select",
            options: "\nSales\nTechnical\nLab",
            reqd: 0
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        // Pending with — color-coded badge
        if (column.fieldname === "pending_with" && value) {
            const map = {
                "Sales":     { bg: "#DBEAFE", color: "#1D4ED8" },
                "Technical": { bg: "#EDE9FE", color: "#5B21B6" },
                "Lab":       { bg: "#FEF3C7", color: "#92400E" },
                "Completed": { bg: "#D1FAE5", color: "#065F46" },
            };
            const style = map[value] || { bg: "#F3F4F6", color: "#374151" };
            return `<span style="background:${style.bg};color:${style.color};padding:2px 9px;border-radius:4px;font-size:11px;font-weight:600;">${value}</span>`;
        }

        // Numeric step columns — green badge if > 0, red zero if 0
        const stepCols = ["visit_request","site_visit","water_sample","lab_test_result","technical_proposal","customer_proposal","request_for_proposal"];
        if (stepCols.includes(column.fieldname)) {
            if ((value ?? 0) > 0) {
                return `<span style="background:#D1FAE5;color:#065F46;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">${value}</span>`;
            } else {
                return `<span style="background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">0</span>`;
            }
        }

        if (column.fieldname === "achieved_operations") {
            const v = parseFloat(value) || 0;
            const color = v === 100 ? "#059669" : v >= 50 ? "#D97706" : "#DC2626";
            return `<span style="color:${color};font-weight:700;">${v}%</span>`;
        }

        if (column.fieldname === "pending_operations") {
            return `<span style="color:#DC2626;font-weight:700;">${parseFloat(value)||0}%</span>`;
        }

        if (column.fieldname === "delay_days") {
            const v = parseInt(value) || 0;
            const color = v > 15 ? "#DC2626" : v > 5 ? "#D97706" : "#059669";
            return `<span style="color:${color};font-weight:700;">${v}</span>`;
        }

        return default_formatter(value, row, column, data);
    },

    "onload": function(report) {
        report.page.add_inner_button(__("Export to Excel"), function() {
            frappe.query_report.export_report();
        });
    }
};