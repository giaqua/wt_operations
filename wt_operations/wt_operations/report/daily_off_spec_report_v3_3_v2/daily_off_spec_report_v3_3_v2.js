// Copyright (c) 2026, HM
// For license information, please see license.txt

frappe.query_reports["Daily Off-Spec Report V3-3 v2"] = {
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
                // don't make sense once rows are rolled up to one-per-month, so
                // just re-run the report - the server drops/adjusts those columns.
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
		{
            fieldname: "hide_project_and_days",
            label: __("Hide Project and Days"),
            fieldtype: "Check",
            default: 1,
        },
		{
            fieldname: "hide_zero_off_spec_rows",
            label: __("Hide Zero Off-Spec Rows"),
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

        // Shortcut: always prints the monthly roll-up, regardless of whether
        // the "Group By Month" filter is currently checked in the report itself.
        report.page.add_inner_button(
            __("Print Report (Monthly)"),
            function () {
                print_daily_offspec_report(report, { group_by_month: 1 });
            },
            __("Actions")
        );

        // New: prints the full daily detail (never rolled up server-side),
        // but adds a subtotal row after every Project + Unit + Month group,
        // totalling only QTY (waste_water_treated_volume) and Daily Off-Spec.
        report.page.add_inner_button(
            __("Print Report (Detailed + Monthly Totals)"),
            function () {
                print_daily_offspec_report(
                    report,
                    { group_by_month: 0 },
                    { add_monthly_subtotals: true }
                );
            },
            __("Actions")
        );

        // ---------------------------------------------------------------
        // Excel export - mirrors the three print variants above exactly.
        // Same filters, same column set, same totals/subtotal logic - the
        // server builds the workbook from the same get_columns()/get_data()
        // functions the report and the print view use, so the .xlsx always
        // matches what's on screen / on the printed page.
        // ---------------------------------------------------------------
        report.page.add_inner_button(
            __("Export to Excel"),
            function () {
                export_daily_offspec_excel(report);
            },
            __("Actions")
        );

        report.page.add_inner_button(
            __("Export to Excel (Monthly)"),
            function () {
                export_daily_offspec_excel(report, { group_by_month: 1 });
            },
            __("Actions")
        );

        report.page.add_inner_button(
            __("Export to Excel (Detailed + Monthly Totals)"),
            function () {
                export_daily_offspec_excel(
                    report,
                    { group_by_month: 0 },
                    { add_monthly_subtotals: true }
                );
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
    "wt_operations.wt_operations.report.daily_off_spec_report_v3_3_v2.daily_off_spec_report_v3_3_v2.get_print_data";

// Same module, the Excel-generating whitelisted method (see the .py file).
// TODO: keep this in sync with PRINT_DATA_METHOD's app/module path above.
const EXCEL_DATA_METHOD =
    "wt_operations.wt_operations.report.daily_off_spec_report_v3_3_v2.daily_off_spec_report_v3_3_v2.get_excel";

function print_daily_offspec_report(report, filter_overrides, options) {
    const filters = Object.assign({}, frappe.query_report.get_filter_values(), filter_overrides || {});
    const opts = options || {};

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
            render_print_window(
                columns,
                data,
                totals,
                server_filters,
                company || {},
                is_arabic,
                !!opts.add_monthly_subtotals
            );
        },
        error: function () {
            frappe.dom.unfreeze();
            frappe.msgprint(
                __("Failed to generate the print view. Check the browser console / server logs.")
            );
        },
    });
}

// Self-contained POST-and-navigate helper. Some Frappe versions don't ship
// frappe.utils.open_url_post, so this builds and submits a plain HTML form
// pointed at a new tab - the browser then handles the binary/file response
// as a normal download, same as frappe.utils.open_url_post would.
function hm_open_url_post(url, args) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url;
    form.target = "_blank";
    form.style.display = "none";

    // CSRF token, same header frappe.call sends automatically
    if (frappe.csrf_token) {
        const csrf_input = document.createElement("input");
        csrf_input.type = "hidden";
        csrf_input.name = "csrf_token";
        csrf_input.value = frappe.csrf_token;
        form.appendChild(csrf_input);
    }

    Object.keys(args || {}).forEach(function (key) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = args[key];
        form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Downloads an .xlsx built server-side from the exact same filters/columns/
// data/totals as the print view. Uses a POST-and-navigate (rather than
// frappe.call) so the browser's normal file-download flow handles the
// binary response - this is the same technique frappe core uses for its
// own report/data exports.
function export_daily_offspec_excel(report, filter_overrides, options) {
    const filters = Object.assign({}, frappe.query_report.get_filter_values(), filter_overrides || {});
    const opts = options || {};

    if (!filters.from_date || !filters.to_date) {
        frappe.msgprint(__("Please select From Date and To Date"));
        return;
    }

    hm_open_url_post("/api/method/" + EXCEL_DATA_METHOD, {
        filters: JSON.stringify(filters),
        add_monthly_subtotals: opts.add_monthly_subtotals ? 1 : 0,
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

// ---------------------------------------------------------------------------
// Monthly subtotal row builder (used by the "Detailed + Monthly Totals" print)
// ---------------------------------------------------------------------------

function get_month_label(date_str, is_arabic) {
    if (!date_str) return "";
    const d = frappe.datetime.str_to_obj(date_str);
    try {
        return d.toLocaleString(is_arabic ? "ar" : "en", { month: "long", year: "numeric" });
    } catch (e) {
        // Fallback if Intl locale isn't available in the print window
        return frappe.datetime.str_to_user(date_str);
    }
}

function build_subtotal_row(columns, label, vol_total, offspec_total, is_arabic) {
    const qty_idx = columns.findIndex((c) => c.fieldname === "waste_water_treated_volume");
    const offspec_idx = columns.findIndex((c) => c.fieldname === "daily_off_spec");
    const label_span = Math.max(qty_idx, 1);

    const cells = [];
    cells.push(
        `<td colspan="${label_span}" style="text-align:${
            is_arabic ? "right" : "left"
        }"><b>${frappe.utils.escape_html(label)}</b></td>`
    );

    for (let idx = label_span; idx < columns.length; idx++) {
        const col = columns[idx];
        if (idx === qty_idx) {
            cells.push(`<td style="text-align:right"><b>${format_total_value(vol_total, col)}</b></td>`);
        } else if (idx === offspec_idx) {
            cells.push(`<td style="text-align:right"><b>${format_total_value(offspec_total, col)}</b></td>`);
        } else {
            cells.push(`<td></td>`);
        }
    }

    return `<tr class="month-subtotal-row">${cells.join("")}</tr>`;
}

function build_body_rows(columns, data, is_arabic) {
    return data
        .map((row, idx) => {
            const cells = columns
                .map((col) => {
                    const raw = row[col.fieldname];
                    const align =
                        col.fieldtype === "Float" || col.fieldtype === "Currency" || col.fieldtype === "Int"
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
}

// Renders daily rows in order, inserting a bold subtotal row (QTY + Daily
// Off-Spec only) every time the Project + Unit + Month key changes.
function build_body_rows_with_monthly_subtotals(columns, data, is_arabic) {
    let html = "";
    let group_key = null;
    let month_label = "";
    let vol_sum = 0;
    let offspec_sum = 0;
    let row_idx = 0;

    const flush_group = () => {
        if (group_key === null) return;
        const label = is_arabic ? `إجمالي - ${month_label}` : `Total - ${month_label}`;
        html += build_subtotal_row(columns, label, vol_sum, offspec_sum, is_arabic);
    };

    data.forEach((row) => {
        const month_key = (row.date || "").slice(0, 7); // "YYYY-MM"
        const key = `${row.project || ""}|${row.unit || ""}|${month_key}`;

        if (group_key !== null && key !== group_key) {
            flush_group();
            vol_sum = 0;
            offspec_sum = 0;
        }

        group_key = key;
        month_label = get_month_label(row.date, is_arabic);
        vol_sum += flt(row.waste_water_treated_volume);
        offspec_sum += flt(row.daily_off_spec);

        const cells = columns
            .map((col) => {
                const raw = row[col.fieldname];
                const align =
                    col.fieldtype === "Float" || col.fieldtype === "Currency" || col.fieldtype === "Int"
                        ? "right"
                        : is_arabic
                        ? "right"
                        : "left";
                return `<td style="text-align:${align}">${format_cell_value(raw, col)}</td>`;
            })
            .join("");
        html += `<tr class="${row_idx % 2 === 0 ? "row-even" : "row-odd"}">${cells}</tr>`;
        row_idx++;
    });

    flush_group(); // last group

    return html;
}

function render_print_window(columns, data, totals, filters, company, is_arabic, add_monthly_subtotals) {
    const logo_url = company.company_logo ? frappe.urllib.get_full_url(company.company_logo) : "";
    const company_name = company.company_name || "";
    const is_monthly = !!filters.group_by_month;

    const title = is_arabic
        ? is_monthly
            ? "التقرير الشهري لمخالفة المواصفات"
            : add_monthly_subtotals
            ? "التقرير اليومي التفصيلي لمخالفة المواصفات مع إجمالي شهري"
            : "التقرير اليومي لمخالفة المواصفات"
        : is_monthly
        ? "Daily Off-Spec Report (Monthly Summary)"
        : add_monthly_subtotals
        ? "Daily Off-Spec Report (Detailed, with Monthly Totals)"
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
    // authoritative row list (the same one execute()/get_data() produced,
    // including the monthly roll-up when group_by_month is set), so no
    // client-side de-duplication, grouping, or re-summing happens here -
    // EXCEPT for the monthly subtotal rows below, which only sum QTY and
    // Daily Off-Spec for display and never touch the underlying data/totals.
    const body_rows =
        add_monthly_subtotals && !is_monthly
            ? build_body_rows_with_monthly_subtotals(columns, data, is_arabic)
            : build_body_rows(columns, data, is_arabic);

    const totals_label_colspan = columns.findIndex(
        (c) => ((c.fieldtype === "Float" || c.fieldtype === "Currency") && (c.fieldname === "waste_water_treated_volume" || c.fieldname === "total_off_spec_count"))
    );
    const totals_row = columns
        .map((col, idx) => {
			console.log("totals_row", totals, col.fieldname, idx, totals_label_colspan);
            if (totals && totals.hasOwnProperty(col.fieldname) && (col.fieldname === "waste_water_treated_volume" || col.fieldname === "daily_off_spec")) {
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
        /* NOTE: no table-footer-group here on purpose - the grand total row
           lives inside <tbody> as the last row so it prints ONCE, at the
           true end of the report, not on every page. */

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

        tr.month-subtotal-row td {
            background: #fdeaea;
            border-top: 2px solid ${HM_RED};
            border-bottom: 1px solid #ccc;
            font-size: 10.5px;
            font-weight: 600;
        }

        /* Grand total row - now a normal tbody row, printed once at the end */
        tr.grand-total-row td {
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
        <tbody>
            ${body_rows}
            <tr class="grand-total-row">${totals_row}</tr>
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