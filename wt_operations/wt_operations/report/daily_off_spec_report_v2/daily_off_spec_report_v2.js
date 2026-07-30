// Copyright (c) 2026, HM
// For license information, please see license.txt

frappe.query_reports["Daily Off-Spec Report V2"] = {
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
            default: ["COD"],
        },
        {
            fieldname: "sample_process_location",
            label: __("Sample Process Location"),
            fieldtype: "Data",
            default: "lift",
        },
        {
            fieldname: "result_type",
            label: __("Result Type"),
            fieldtype: "Select",
            options: ["", "Internal", "External"],
        },
        {
            fieldname: "show_daily_report",
            label: __("Show Daily Report"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "show_water_sample",
            label: __("Show Water Sample"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "show_sample_process_location",
            label: __("Show Sample Process Location"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "show_arabic_report",
            label: __("Show Arabic Report"),
            fieldtype: "Check",
            default: 1,
        },
    ],

    onload: function (report) {
        report.page.add_inner_button(
            __("Print Report"),
            function () {
                print_daily_offspec_report(report);
            },
            __("Actions")
        );
    },
};

// ---------------------------------------------------------------------------
// Branded print view
// Uses the <thead> "display: table-header-group" trick so the header block
// (logo + company + report title + column headers) repeats on every printed
// page. Works for both browser Print and "Save as PDF" from the print dialog.
// ---------------------------------------------------------------------------

const HM_BLUE = "#010BCE";
const HM_RED = "#D50000";

// TODO: replace with the actual dotted path to this report's .py module, e.g.
// "your_app.your_module.report.daily_off_spec_report.daily_off_spec_report.get_print_data"
const PRINT_DATA_METHOD =
    "wt_operations.wt_operations.report.daily_off_spec_report_v2.daily_off_spec_report_v2.get_print_data";

function print_daily_offspec_report(report) {
    const filters = frappe.query_report.get_filter_values();

    frappe.dom.freeze(__("Preparing print view..."));

    frappe.call({
        method: PRINT_DATA_METHOD,
        args: { filters },
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

            // const is_arabic = !!server_filters.show_arabic_report;
			const is_arabic = 0;
            render_print_window(columns, data, totals, server_filters, company || {}, is_arabic);
        },
        error: function () {
            frappe.dom.unfreeze();
            frappe.msgprint(
                __("Failed to generate the print view. Check the browser console / server logs.")
            );
        },
    });
}

function format_cell_value(value, col) {
    if (value === null || value === undefined || value === "") return "";

    if (col.fieldtype === "Currency") {
        return frappe.format(value, { fieldtype: "Currency" }, { always_show_decimals: true });
    }
    if (col.fieldtype === "Float") {
        return flt(value).toFixed(2);
    }
    if (col.fieldtype === "Date") {
        return frappe.datetime.str_to_user(value);
    }
    return frappe.utils.escape_html(String(value));
}

// Totals now come pre-computed from the server (see `totals` param below) -
// this only formats them for display, at 2 decimal places.
function format_total_value(value, col) {
    const num = flt(value) || 0;
    const fixed = num.toFixed(2);

    if (col.fieldtype === "Currency") {
        const parts = fixed.split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
    }
    return fixed;
}

function render_print_window(columns, data, totals, filters, company, is_arabic) {
    const logo_url = company.company_logo ? frappe.urllib.get_full_url(company.company_logo) : "";
    const company_name = company.company_name || "";

    const title = is_arabic ? "التقرير اليومي لمخالفة المواصفات" : "Daily Off-Spec Report";
    const date_range_label = is_arabic ? "الفترة" : "Period";
    const date_range = `${frappe.datetime.str_to_user(filters.from_date)} - ${frappe.datetime.str_to_user(filters.to_date)}`;
    const generated_label = is_arabic ? "تاريخ الطباعة" : "Generated on";
    const generated_on = frappe.datetime.now_datetime();

    // Column header row
    const header_cells = columns
        .map((col) => `<th>${frappe.utils.escape_html(__(col.label))}</th>`)
        .join("");

    // Data comes straight from the server's get_print_data - it's already the
    // authoritative row list (the same one execute()/get_data() produced), so
    // no client-side de-duplication or re-summing happens here.
    const body_rows = data
        .map((row, idx) => {
            const cells = columns
                .map((col) => {
                    const raw = row[col.fieldname];
                    const align =
                        col.fieldtype === "Float" || col.fieldtype === "Currency"
                            ? "right"
                            : is_arabic
                            ? "right"
                            : "left";
                    return `<td style="text-align:${align}">${format_cell_value(raw, col)}</td>`;
                })
                .join("");
            return `<tr class="${idx % 2 === 0 ? "row-even" : "row-odd"}">${cells}</tr>`;
        })
        .join("");

    const totals_label_colspan = columns.findIndex(
        (c) => c.fieldtype === "Float" || c.fieldtype === "Currency"
    );
    const totals_row = columns
        .map((col, idx) => {
            if (totals && totals.hasOwnProperty(col.fieldname)) {
                return `<td style="text-align:right;white-space:nowrap"><b>${format_total_value(
                    totals[col.fieldname],
                    col
                )}</b></td>`;
            }
            if (idx === Math.max(totals_label_colspan - 1, 0)) {
                return `<td style="text-align:${is_arabic ? "right" : "left"}"><b>${
                    is_arabic ? "الإجمالي" : "Total"
                }</b></td>`;
            }
            return "<td></td>";
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
            font-size: 11px;
        }

        table.report-table {
            width: 100%;
            border-collapse: collapse;
        }

        /* This is the key trick: a thead inside a table repeats on every
           printed page in all major browsers (Chrome, Edge, Firefox). */
        thead.report-header { display: table-header-group; }
        tfoot.report-footer { display: table-footer-group; }

        .brand-bar {
            background: ${HM_BLUE};
            color: #fff;
            padding: 10px 14px;
        }
        .brand-bar-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .brand-bar img.logo {
            max-height: 42px;
            max-width: 160px;
            background: #fff;
            padding: 3px 6px;
            border-radius: 3px;
        }
        .brand-bar .company-name {
            font-size: 15px;
            font-weight: 600;
        }
        .brand-bar .report-title {
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            flex: 1;
        }
        .brand-bar .meta {
            font-size: 10px;
            text-align: ${is_arabic ? "left" : "right"};
            line-height: 1.5;
        }
        .accent-strip {
            height: 4px;
            background: ${HM_RED};
        }

        thead.report-header th {
            background: #f1f2fb;
            color: ${HM_BLUE};
            border: 1px solid #ccc;
            padding: 6px 8px;
            font-size: 10.5px;
            font-weight: 700;
            white-space: nowrap;
        }

        tbody td {
            border: 1px solid #ddd;
            padding: 5px 8px;
            font-size: 10.5px;
        }
        tr.row-even td { background: #ffffff; }
        tr.row-odd td { background: #f8f9fd; }
        tr { page-break-inside: avoid; }

        tfoot.report-footer td {
            border: 1px solid #ccc;
            border-top: 2px solid ${HM_RED};
            padding: 6px 8px;
            background: #f1f2fb;
            font-size: 10.5px;
        }

        .print-toolbar {
            position: fixed;
            top: 8px;
            right: 8px;
            z-index: 999;
        }
        .print-toolbar button {
            background: ${HM_BLUE};
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
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
                            <div class="company-name"></div>
                            <div class="report-title">
                                ${frappe.utils.escape_html(company_name)}
                                <br>
                                ${title}
                            </div>
                            <div class="meta">
                                ${date_range_label}: ${date_range}<br>
                                ${generated_label}: ${generated_on}
                            </div>
                        </div>
                    </div>
                    <div class="accent-strip"></div>
                </th>
            </tr>
            <tr>${header_cells}</tr>
        </thead>
        <tfoot class="report-footer">
            <tr>${totals_row}</tr>
        </tfoot>
        <tbody>
            ${body_rows}
        </tbody>
    </table>

    <script>
        // Auto-trigger print once the logo (if any) has loaded, so the
        // print dialog opens with the image already rendered.
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