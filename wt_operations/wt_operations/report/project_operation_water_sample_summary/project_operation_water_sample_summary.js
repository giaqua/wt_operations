// Copyright (c) 2026, GiaquaTech and contributors
// For license information, please see license.txt

frappe.query_reports["Project Operation Water Sample Summary"] = {
    filters: [
        {
            fieldname: "name",
            label: __("Sample ID"),
            fieldtype: "Link",
            options: "Project Operation Water Sample",
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
            fieldname: "site",
            label: __("Site"),
            fieldtype: "Link",
            options: "Project",
            get_query: function() {
                return {
                    filters: {
                        status: "Active"
                    }
                };
            }
        },
        {
            fieldname: "sample_type",
            label: __("Sample Type"),
            fieldtype: "Select",
            options: ["", "Domestic", "Industrial", "Mixed", "Other"],
        },
        {
            fieldname: "water_source",
            label: __("Water Source"),
            fieldtype: "Select",
            options: ["", "Inlet", "Outlet", "Process", "Other"],
        },
        {
            fieldname: "workflow_state",
            label: __("Status"),
            fieldtype: "Select",
            options: ["", "Draft", "Submitted", "Completed", "Cancelled"],
        },
        {
            fieldname: "result_type",
            label: __("Result Type"),
            fieldtype: "Select",
            options: ["", "Internal", "External", "Both"],
        },
        {
            fieldname: "responsible",
            label: __("Responsible"),
            fieldtype: "Link",
            options: "User",
        },
        {
            fieldname: "parameter",
            label: __("Parameter"),
            fieldtype: "MultiSelectList",
            get_data: function (txt) {
                return [
                    { value: "TDS.", description: "Total Dissolved Solids" },
                    { value: "COD", description: "Chemical Oxygen Demand" },
                    { value: "TSS", description: "Total Suspended Solids" },
                    { value: "pH", description: "pH Level" },
                    { value: "Turbidity.", description: "Turbidity" },
                    { value: "Ammonia", description: "Ammonia" },
                    { value: "Oil & Grease", description: "Oil and Grease" },
                    { value: "BOD", description: "Biological Oxygen Demand" },
                    { value: "E.coli", description: "E. Coli" },
                    { value: "Total chlorine", description: "Total Chlorine" },
                ].filter((d) => d.value.toLowerCase().includes((txt || "").toLowerCase()));
            },
            default: ["TDS.", "COD", "TSS", "pH"],
        },
        {
            fieldname: "show_arabic_report",
            label: __("Show Arabic Report"),
            fieldtype: "Check",
            default: 0,
        },
    ],

    onload: function (report) {
        // Print buttons
        report.page.add_inner_button(
            __("Print Report"),
            function () {
                print_water_sample_report(report);
            },
            __("Actions")
        );

        // Excel export
        report.page.add_inner_button(
            __("Export to Excel"),
            function () {
                export_water_sample_excel(report);
            },
            __("Actions")
        );
    },

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Color code status
        if (column.fieldname == "workflow_state") {
            if (value == "Completed") {
                return `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else if (value == "Draft") {
                return `<span style="color: orange; font-weight: bold;">${value}</span>`;
            } else if (value == "Submitted") {
                return `<span style="color: blue; font-weight: bold;">${value}</span>`;
            } else if (value == "Cancelled") {
                return `<span style="color: red; font-weight: bold;">${value}</span>`;
            }
        }
        
        // Color code compliance
        if (column.fieldname == "compliance") {
            if (value && value.includes("Pass")) {
                return `<span style="color: green; font-weight: bold;">✓ Pass</span>`;
            } else if (value && value.includes("Fail")) {
                return `<span style="color: red; font-weight: bold;">✗ ${value}</span>`;
            }
        }
        
        return value;
    }
};

// ============================
// PRINT FUNCTIONALITY
// ============================

const PRINT_DATA_METHOD = "wt_operations.wt_operations.report.project_operation_water_sample_summary.project_operation_water_sample_summary.get_print_data";

function print_water_sample_report(report) {
    const filters = frappe.query_report.get_filter_values();
    
    frappe.dom.freeze(__("Preparing print view..."));
    
    frappe.call({
        method: PRINT_DATA_METHOD,
        args: { filters: JSON.stringify(filters) },
        callback: function (r) {
            frappe.dom.unfreeze();
            
            if (!r.message) {
                frappe.msgprint(__("Could not load print data."));
                return;
            }
            
            const { columns, data, totals, company, filters: server_filters } = r.message;
            
            if (!data || !data.length) {
                frappe.msgprint(__("No data to print. Please adjust your filters."));
                return;
            }
            
            render_print_window(
                columns,
                data,
                totals,
                server_filters,
                company || {}
            );
        },
        error: function () {
            frappe.dom.unfreeze();
            frappe.msgprint(
                __("Failed to generate the print view. Check the browser console / server logs.")
            );
        }
    });
}

function render_print_window(columns, data, totals, filters, company) {
    const is_arabic = !!filters.show_arabic_report;
    const logo_url = company.company_logo ? frappe.urllib.get_full_url(company.company_logo) : "";
    const company_name = company.company_name || "";
    
    const title = is_arabic ? "تقرير ملخص عينات المياه" : "Water Sample Summary Report";
    const date_range = `${frappe.datetime.str_to_user(filters.from_date)} - ${frappe.datetime.str_to_user(filters.to_date)}`;
    const generated_on = frappe.datetime.now_datetime();
    
    // Column headers
    const header_cells = columns
        .map((col) => `<th>${frappe.utils.escape_html(__(col.label))}</th>`)
        .join("");
    
    // Data rows
    const body_rows = data
        .map((row, idx) => {
            const cells = columns
                .map((col) => {
                    let raw = row[col.fieldname];
                    let value = raw;
                    
                    if (raw === null || raw === undefined) {
                        value = "";
                    } else if (col.fieldtype === "Float" || col.fieldtype === "Currency") {
                        value = flt(raw).toFixed(2);
                    } else if (col.fieldtype === "Date") {
                        value = frappe.datetime.str_to_user(raw);
                    } else {
                        value = frappe.utils.escape_html(String(raw));
                    }
                    
                    // Style compliance
                    if (col.fieldname === "compliance" && value) {
                        if (value.includes("Pass")) {
                            value = `<span style="color: green; font-weight: bold;">✓ ${value}</span>`;
                        } else if (value.includes("Fail")) {
                            value = `<span style="color: red; font-weight: bold;">✗ ${value}</span>`;
                        }
                    }
                    
                    // Style status
                    if (col.fieldname === "workflow_state" && value) {
                        const status_class = value.toLowerCase();
                        value = `<span class="status-${status_class}">${value}</span>`;
                    }
                    
                    const align = (col.fieldtype === "Float" || col.fieldtype === "Currency") 
                        ? "right" 
                        : (is_arabic ? "right" : "left");
                    
                    return `<td style="text-align:${align}">${value}</td>`;
                })
                .join("");
            
            return `<tr class="${idx % 2 === 0 ? "row-even" : "row-odd"}">${cells}</tr>`;
        })
        .join("");
    
    // Totals row
    const total_cells = columns
        .map((col, idx) => {
            const fieldname = col.fieldname;
            if (totals && totals[fieldname] !== undefined && (col.fieldtype === "Float" || col.fieldtype === "Currency")) {
                const value = flt(totals[fieldname]).toFixed(2);
                return `<td style="text-align:right;font-weight:bold;">${value}</td>`;
            } else if (idx === 0) {
                return `<td style="text-align:${is_arabic ? "right" : "left"};font-weight:bold;">${is_arabic ? "الإجمالي" : "Total"}</td>`;
            } else {
                return "<td></td>";
            }
        })
        .join("");
    
    const html = `
    <!DOCTYPE html>
    <html lang="${is_arabic ? "ar" : "en"}" dir="${is_arabic ? "rtl" : "ltr"}">
    <head>
    <meta charset="UTF-8">
    <title>${title}</title>
    <style>
        @page { size: A4 landscape; margin: 14mm 10mm 16mm 10mm; }
        
        * { box-sizing: border-box; }
        body {
            font-family: ${is_arabic ? "'Tahoma','Arial',sans-serif" : "'Segoe UI','Arial',sans-serif"};
            color: #1a1a1a;
            margin: 0;
            font-size: 10px;
        }
        
        table.report-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead.report-header { display: table-header-group; }
        
        .brand-bar {
            background: #010BCE;
            color: #fff;
            padding: 8px 12px;
        }
        .brand-bar-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .brand-bar img.logo {
            max-height: 40px;
            max-width: 150px;
            background: #fff;
            padding: 2px 5px;
            border-radius: 3px;
        }
        .brand-bar .company-name {
            font-size: 14px;
            font-weight: 600;
        }
        .brand-bar .report-title {
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            flex: 1;
        }
        .brand-bar .meta {
            font-size: 9px;
            text-align: ${is_arabic ? "left" : "right"};
            line-height: 1.4;
        }
        .accent-strip {
            height: 3px;
            background: #D50000;
        }
        
        thead.report-header th {
            background: #f1f2fb;
            color: #010BCE;
            border: 1px solid #ccc;
            padding: 5px 6px;
            font-size: 9.5px;
            font-weight: 700;
            white-space: nowrap;
        }
        
        tbody td {
            border: 1px solid #ddd;
            padding: 4px 6px;
            font-size: 9.5px;
        }
        tr.row-even td { background: #ffffff; }
        tr.row-odd td { background: #f8f9fd; }
        tr { page-break-inside: avoid; }
        
        tr.grand-total-row td {
            border: 1px solid #ccc;
            border-top: 2px solid #D50000;
            padding: 5px 6px;
            background: #f1f2fb;
            font-size: 10px;
        }
        
        .status-completed { color: green; font-weight: bold; }
        .status-draft { color: orange; font-weight: bold; }
        .status-submitted { color: blue; font-weight: bold; }
        .status-cancelled { color: red; font-weight: bold; }
        
        .print-toolbar {
            position: fixed;
            top: 8px;
            right: 8px;
            z-index: 999;
        }
        .print-toolbar button {
            background: #010BCE;
            color: #fff;
            border: none;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
        }
        @media print {
            .print-toolbar { display: none; }
        }
    </style>
    </head>
    <body>
    
    <div class="print-toolbar">
        <button onclick="window.print()">${is_arabic ? "طباعة" : "Print"}</button>
    </div>
    
    <table class="report-table">
        <thead class="report-header">
            <tr>
                <th colspan="${columns.length}" style="padding:0;border:none">
                    <div class="brand-bar">
                        <div class="brand-bar-inner">
                            ${logo_url ? `<img class="logo" src="${logo_url}">` : "<div></div>"}
                            <div class="company-name">${frappe.utils.escape_html(company_name)}</div>
                            <div class="report-title">${title}</div>
                            <div class="meta">
                                ${is_arabic ? "الفترة" : "Period"}: ${date_range}<br>
                                ${is_arabic ? "تاريخ الطباعة" : "Generated on"}: ${generated_on}
                            </div>
                        </div>
                    </div>
                    <div class="accent-strip"></div>
                </th>
            </tr>
            <tr>${header_cells}</tr>
        </thead>
        <tbody>
            ${body_rows}
            <tr class="grand-total-row">${total_cells}</tr>
        </tbody>
    </table>
    
    <script>
        window.addEventListener("load", function () {
            setTimeout(function () { window.print(); }, 300);
        });
    </script>
    </body>
    </html>
    `;
    
    const print_window = window.open("", "_blank");
    if (!print_window) {
        frappe.msgprint(__("Please allow pop-ups for this site to print the report."));
        return;
    }
    print_window.document.open();
    print_window.document.write(html);
    print_window.document.close();
}

// ============================
// EXCEL EXPORT FUNCTIONALITY
// ============================

const EXCEL_DATA_METHOD = "wt_operations.wt_operations.report.project_operation_water_sample_summary.project_operation_water_sample_summary.get_excel";

function export_water_sample_excel(report) {
    const filters = frappe.query_report.get_filter_values();
    
    if (!filters.from_date || !filters.to_date) {
        frappe.msgprint(__("Please select From Date and To Date"));
        return;
    }
    
    // Use POST form submission for file download
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/method/" + EXCEL_DATA_METHOD;
    form.target = "_blank";
    form.style.display = "none";
    
    // CSRF token
    if (frappe.csrf_token) {
        const csrf_input = document.createElement("input");
        csrf_input.type = "hidden";
        csrf_input.name = "csrf_token";
        csrf_input.value = frappe.csrf_token;
        form.appendChild(csrf_input);
    }
    
    // Filters
    const filters_input = document.createElement("input");
    filters_input.type = "hidden";
    filters_input.name = "filters";
    filters_input.value = JSON.stringify(filters);
    form.appendChild(filters_input);
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}