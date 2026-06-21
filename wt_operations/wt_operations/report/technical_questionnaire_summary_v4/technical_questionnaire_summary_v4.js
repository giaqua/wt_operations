frappe.query_reports["Technical Questionnaire Summary V4"] = {
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
            fieldtype: "Check",
            default: 1
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Select",
            options: "\nSales\nTechnical\nLab",
            reqd: 0
        },
        {
            fieldname: "group_by_month",
            label: __("Group by Month"),
            fieldtype: "Check",
            default: 0,
            description: __("Group data by year-month")
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        // If it's a month group row
		
        if (row && data.is_group) {
            if (column.fieldname === "month_display") {
                // Calculate statistics for the month
                const total = data.total_count || 0;
                const completed = data.completed_count || 0;
                const pending = data.pending_count || 0;
                const avgAchieved = data.avg_achieved || 0;
                const avgDelay = data.avg_delay || 0;
                
                // Create progress bar for completion
                const completionPct = total > 0 ? Math.round((completed / total) * 100) : 0;
                const barColor = completionPct >= 70 ? '#1D9E75' : completionPct >= 40 ? '#D97706' : '#E24B4A';
                
                // Format with month name and stats
				console.log("row", row,"value", value,"total", total,"completed", completed,"pending", pending,"avgAchieved", avgAchieved,"avgDelay", avgDelay,"completionPct", completionPct);
                let html = `<div style="display:flex;align-items:center;gap:12px;padding:4px 0;">`;
                html += `<span style="font-weight:700;font-size:14px;color:#1F2937;">📅 ${value}</span>`;
                html += `<span style="background:#F3F4F6;padding:2px 12px;border-radius:12px;font-size:11px;font-weight:600;color:#6B7280;">
                            ${total} TQs
                        </span>`;
                html += `<span style="background:#D1FAE5;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;color:#065F46;">
                            ✓ ${completed} Completed
                        </span>`;
                if (pending > 0) {
                    html += `<span style="background:#FEF3C7;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;color:#92400E;">
                                ⏳ ${pending} Pending
                            </span>`;
                }
                html += `<span style="background:#EFF6FF;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;color:#1D4ED8;">
                            Avg ${avgAchieved}%
                        </span>`;
                html += `<span style="background:#FEE2E2;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;color:#991B1B;">
                            ⏱ ${avgDelay}d avg
                        </span>`;
                html += `<div style="flex:1;min-width:100px;background:#F3F4F6;border-radius:4px;height:6px;overflow:hidden;margin-left:4px;">
                            <div style="width:${completionPct}%;height:100%;background:${barColor};border-radius:4px;transition:width 0.5s;"></div>
                        </div>`;
                html += `<span style="font-size:11px;font-weight:600;color:${barColor};">${completionPct}%</span>`;
                html += `</div>`;
                return html;
            }
            // For other columns in group row, return empty or summary
            if (column.fieldname === "actions") {
                return `<span style="color:#9CA3AF;font-size:11px;">📊 ${data.total_count || 0} items</span>`;
            }
            if (column.fieldname === "pending_with") {
                const completed = data.completed_count || 0;
                const pending = data.pending_count || 0;
                return `<span style="color:#D16105;font-weight:600;">${pending} Pending</span> / <span style="color:#0F6E56;font-weight:600;">${completed} Completed</span>`;
            }
            return '';
        }

        // For detail rows (individual TQs)
        if (row && !row.is_group) {
            if (column.fieldname === "month_display") {
                // Show indented technical questionnaire name
                const indent = row.indent || 0;
                const padding = indent * 20;
                return `<span style="padding-left:${padding}px;display:inline-block;">📄 ${row.technical_questionnaire || ''}</span>`;
            }
        }

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