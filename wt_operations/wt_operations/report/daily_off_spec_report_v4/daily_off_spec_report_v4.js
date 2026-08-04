// Copyright (c) 2026, HM
// For license information, please see license.txt

frappe.query_reports["Daily Off-Spec Report V4"] = {
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
            fieldname: "group_by_month",
            label: __("Group By Month"),
            fieldtype: "Check",
            default: 0,
            on_change: function (report) {
                // Daily-report / water-sample / sample-process-location columns
                // don't make sense once rows are grouped into a tree, so just
                // re-run the report - the server drops/adjusts those columns.
                report.refresh();
            },
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

    // -----------------------------------------------------------------
    // Trial-Balance-style collapsible tree, active only when the report
    // returns tree-shaped rows (i.e. when "Group By Month" is checked -
    // see daily_off_spec_report_v2.py: build_monthly_tree()). Each row's
    // unique key lives in "particulars" (name_field) and its parent's key
    // in "parent_particulars" (parent_field). Month rows have no parent
    // (root, collapsed by default via initial_depth: 0) and expand to
    // reveal their daily rows as children - exactly like Trial Balance's
    // Group/Account tree.
    //
    // When "Group By Month" is unchecked, rows simply don't carry
    // particulars/parent_particulars/is_group, so this config has no
    // visible effect and the report renders as a normal flat list.
    // -----------------------------------------------------------------
    tree: true,
    name_field: "particulars",
    parent_field: "parent_particulars",
    // initial_depth: 1 means every month row loads already expanded, showing
    // ALL of its daily rows right away - no click needed. Each month can
    // still be individually collapsed afterwards if you want to tuck it
    // away again. (Set this back to 0 if you'd rather months start
    // collapsed and only expand on click.)
    initial_depth: 1,

    formatter: function (value, row, column, data, default_formatter) {
        // Current Frappe passes (value, row, column, data, default_formatter) -
        // NOT the old v10-v12 (row, cell, value, columnDef, dataContext, ...)
        // shape (that mismatch is what threw "Cannot read properties of
        // undefined (reading 'fieldname')" here before).
        if (column.fieldname === "particulars" && data) {
            // Fall back to the raw particulars value if display_label is
            // somehow missing, so we never render the literal text
            // "undefined" in the tree column.
            value = data.display_label !== undefined && data.display_label !== null
                ? data.display_label
                : value;
            column.is_tree = true;
        }

        value = default_formatter(value, row, column, data);

        if (data && data.is_group) {
            value = $(value).css("font-weight", "bold").wrap("<p></p>").parent().html();
        }

        return value;
    },

    onload: function (report) {
        report.page.add_inner_button(
            __("Print Report"),
            function () {
                print_daily_offspec_report(report);
            },
            __("Actions")
        );

        // Shortcut: always prints the monthly roll-up (with daily detail
        // beneath each month), regardless of whether "Group By Month" is
        // currently checked in the report itself.
        report.page.add_inner_button(
            __("Print Report (Monthly)"),
            function () {
                print_daily_offspec_report(report, { group_by_month: 1 });
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
//
// Print is static paper/PDF - there's no click-to-expand there, so when the
// data is tree-shaped (group_by_month), the print view renders it fully
// expanded: each month as a bold subtotal row, its daily rows indented
// directly beneath it - the same information a fully-expanded Trial Balance
// tree would show if printed.
// ---------------------------------------------------------------------------

const HM_BLUE = "#010BCE";
const HM_RED = "#D50000";

// TODO: replace with the actual dotted path to this report's .py module, e.g.
// "your_app.your_module.report.daily_off_spec_report.daily_off_spec_report.get_print_data"
const PRINT_DATA_METHOD =
    "wt_operations.wt_operations.report.daily_off_spec_report_v4.daily_off_spec_report_v4.get_print_data";

function print_daily_offspec_report(report, filter_overrides) {
    const filters = Object.assign({}, frappe.query_report.get_filter_values(), filter_overrides || {});

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
    if (col.fieldtype === "Int") {
        return String(parseInt(value, 10) || 0);
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
    const is_monthly = !!filters.group_by_month;

    const title = is_arabic
        ? is_monthly
            ? "التقرير الشهري لمخالفة المواصفات"
            : "التقرير اليومي لمخالفة المواصفات"
        : is_monthly
        ? "Daily Off-Spec Report (Monthly Summary)"
        : "Daily Off-Spec Report";
    const date_range_label = is_arabic ? "الفترة" : "Period";
    const date_range = `${frappe.datetime.str_to_user(filters.from_date)} - ${frappe.datetime.str_to_user(filters.to_date)}`;
    const generated_label = is_arabic ? "تاريخ الطباعة" : "Generated on";
    const generated_on = frappe.datetime.now_datetime();

    // Column header row
    const header_cells = columns
        .map((col) => `<th>${frappe.utils.escape_html(__(col.label))}</th>`)
        .join("");

    // Data comes straight from the server's get_print_data - it's already the
    // authoritative row list (the same one execute()/get_data() produced). In
    // monthly mode this includes both the month (bold, is_group) rows and
    // their indented daily children, in order, so no client-side de-duping,
    // grouping, or re-summing happens here - just formatting.
    const body_rows = data
        .map((row, idx) => {
            const is_group_row = !!row.is_group;
            const indent = row.indent || 0;

            const cells = columns
                .map((col) => {
                    let raw = row[col.fieldname];

                    // The tree/particulars column shows the friendly label
                    // (month name or formatted date), not the raw tree key,
                    // and gets indented for child (daily) rows.
                    if (col.fieldname === "particulars") {
                        const label = frappe.utils.escape_html(String(row.display_label || ""));
                        const padded = indent
                            ? `<span style="padding-left:${indent * 18}px">${label}</span>`
                            : label;
                        return `<td style="text-align:${is_arabic ? "right" : "left"}">${padded}</td>`;
                    }

                    const align =
                        col.fieldtype === "Float" || col.fieldtype === "Currency" || col.fieldtype === "Int"
                            ? "right"
                            : is_arabic
                            ? "right"
                            : "left";
                    return `<td style="text-align:${align}">${format_cell_value(raw, col)}</td>`;
                })
                .join("");

            const row_class = is_group_row
                ? "row-group"
                : idx % 2 === 0
                ? "row-even"
                : "row-odd";
            return `<tr class="${row_class}">${cells}</tr>`;
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
        tr.row-group td {
            background: #e7e9fb;
            font-weight: 700;
            border-top: 1.5px solid ${HM_BLUE};
        }
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