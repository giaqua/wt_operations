// Copyright (c) 2026, HM
// For license information, please see license.txt

// TODO: replace with the actual dotted path to this report's .py module
const REPORT_METHOD_PATH =
    "wt_operations.wt_operations.report.water_treatment_register_v5.water_treatment_register_v5";

frappe.query_reports["Water Treatment Register V5"] = {
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
            fieldname: "water_source",
            label: __("Water Source"),
            fieldtype: "Select",
            options: ["", "Inlet", "Outlet"],
            default: "",
            description: __("Empty shows both Inlet and Outlet blocks side by side"),
        },
        {
            fieldname: "parameter",
            label: __("Parameter (Inlet)"),
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
            description: __("Controls the Inlet block only - Outlet always shows all parameters"),
        },
        {
            fieldname: "show_chemicals",
            label: __("Show Chemicals"),
            fieldtype: "Check",
            default: 0,
            description: __(
                "When checked with no specific chemicals selected below, every chemical used in the date range gets its own qty column"
            ),
            on_change: function (report) {
                // Toggling this changes which columns exist server-side
                // (all-chemicals vs none), so re-run the report.
                report.refresh();
            },
        },
        {
            fieldname: "chemical",
            label: __("Chemicals (Qty Columns)"),
            fieldtype: "MultiSelectList",
            depends_on: "eval:frappe.query_report.get_filter_value('show_chemicals')",
            get_data: function (txt) {
                // Server returns [{value: <Chemical Item name>, description:
                // <linked stock Item's item_name>}, ...] - pass it straight
                // through so the picker shows the item name as a hint next
                // to the Chemical Item name being selected.
                return frappe
                    .call({
                        method: `${REPORT_METHOD_PATH}.get_chemical_options`,
                        args: { txt: txt || "" },
                    })
                    .then((r) => r.message || []);
            },
            default: [],
            description: __("Leave empty (with Show Chemicals checked) to show every chemical used instead of a specific list"),
        },
        {
            fieldname: "show_density",
            label: __("Use Quantity After Density"),
            fieldtype: "Check",
            default: 1,
            description: __("When checked, chemical qty columns use 'Chemical Quantity Used (kg) After Density'"),
        },
        {
            fieldname: "hide_zero_qty_chemical_columns",
            label: __("Hide Zero-Qty Chemical Columns"),
            fieldtype: "Check",
            default: 1,
            description: __("Drops any chemical qty column whose total across the current results is 0"),
            on_change: function (report) {
                // Which columns exist changes server-side, so re-run.
                report.refresh();
            },
        },
        {
            fieldname: "sample_process_location",
            label: __("Sample Process Location"),
            fieldtype: "Data",
            // default: "lift",
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
        {
            fieldname: "hide_calculation_and_amount",
            label: __("Hide Calculation & Amount Columns"),
            fieldtype: "Check",
            default: 1,
            description: __("Hides the whole off-spec calculation block, including Daily Off-Spec"),
        },
		 {
            fieldname: "hide_fresh_water_consumption",
            label: __("Hide Fresh Water Consumption"),
            fieldtype: "Check",
            default: 0,
            description: __("Hides the fresh water consumption column"),
        },
    ],

    onload: function (report) {
        report.page.add_inner_button(
            __("Print Report"),
            function () {
                print_water_treatment_register(report);
            },
            __("Actions")
        );

        // Shortcut: always prints the monthly roll-up, regardless of whether
        // the "Group By Month" filter is currently checked in the report itself.
        report.page.add_inner_button(
            __("Print Report (Monthly)"),
            function () {
                print_water_treatment_register(report, { group_by_month: 1 });
            },
            __("Actions")
        );

        // Prints the full daily detail (never rolled up server-side), but adds
        // a subtotal row after every Project + Unit + Month group, totalling
        // QTY (waste_water_treated_volume), Fresh Water Consumption, Daily
        // Off-Spec, and every chemical qty column.
        report.page.add_inner_button(
            __("Print Report (Detailed + Monthly Totals)"),
            function () {
                print_water_treatment_register(
                    report,
                    { group_by_month: 0 },
                    { add_monthly_subtotals: true }
                );
            },
            __("Actions")
        );

        // Excel exports - same three variants as the print buttons above,
        // rendered server-side with the same branded layout (see
        // download_excel / build_water_treatment_workbook in the .py file).
        report.page.add_inner_button(
            __("Export to Excel"),
            function () {
                export_water_treatment_excel(report);
            },
            __("Actions")
        );

        report.page.add_inner_button(
            __("Export to Excel (Monthly)"),
            function () {
                export_water_treatment_excel(report, { group_by_month: 1 });
            },
            __("Actions")
        );

        report.page.add_inner_button(
            __("Export to Excel (Detailed + Monthly Totals)"),
            function () {
                export_water_treatment_excel(
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
// page. The grand-total row is a normal LAST ROW OF <tbody> (not a repeating
// tfoot), so it prints exactly once, at the true end of the report.
// ---------------------------------------------------------------------------

const HM_BLUE = "#010BCE";
const HM_RED = "#D50000";

const PRINT_DATA_METHOD = `${REPORT_METHOD_PATH}.get_print_data`;
const EXCEL_DOWNLOAD_METHOD = `${REPORT_METHOD_PATH}.download_excel`;

// Triggers a browser download of the server-rendered .xlsx (see
// download_excel in the .py file). Uses the same open_url_post(cmd, args)
// pattern Frappe core itself uses for report/list exports - it submits a
// hidden form POST to /api/method/, which lets the browser handle the
// binary response + Content-Disposition download normally (a plain
// frappe.call/XHR can't trigger a file-save dialog the same way).
function export_water_treatment_excel(report, filter_overrides, options) {
    const filters = Object.assign({}, frappe.query_report.get_filter_values(), filter_overrides || {});
    const opts = options || {};

    const args = {
        cmd: EXCEL_DOWNLOAD_METHOD,
        filters: JSON.stringify(filters),
        add_monthly_subtotals: opts.add_monthly_subtotals ? 1 : 0,
    };

    open_url_post(frappe.request.url, args);
}

function print_water_treatment_register(report, filter_overrides, options) {
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

            const { columns, data, totals, company, filters: server_filters, ctx } = r.message;

            if (!data || !data.length) {
                frappe.msgprint(__("No data to print. Please adjust your filters."));
                return;
            }

            const is_arabic = 0;
            render_print_window(
                columns,
                data,
                totals,
                server_filters,
                company || {},
                is_arabic,
                !!opts.add_monthly_subtotals,
                ctx || {}
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

// Totals come pre-computed from the server (see `totals` param below) -
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
// Inlet / Outlet / Chemical spanning group-header row
// Built from each column's `group` tag (set server-side in get_columns).
// Consecutive columns sharing the same group get merged into one <th
// colspan="N">. Columns with no group tag render as an empty spacer cell.
// ---------------------------------------------------------------------------

function group_label(group, is_arabic) {
    if (group === "inlet") return is_arabic ? "المدخل (Inlet)" : "Inlet";
    if (group === "outlet") return is_arabic ? "المخرج (Outlet)" : "Outlet";
    if (group === "chemical") return is_arabic ? "استهلاك الكيماويات" : "Chemical Consumption";
    return "";
}

function build_group_header_row(columns, is_arabic) {
    let cells = "";
    let i = 0;
    let has_group = false;

    while (i < columns.length) {
        const group = columns[i].group || null;
        let span = 1;
        while (i + span < columns.length && (columns[i + span].group || null) === group) {
            span++;
        }

        if (group) {
            has_group = true;
            cells += `<th colspan="${span}" class="group-header-${group}">${group_label(
                group,
                is_arabic
            )}</th>`;
        } else {
            cells += `<th colspan="${span}" class="group-header-none"></th>`;
        }

        i += span;
    }

    return has_group ? `<tr class="group-header-row">${cells}</tr>` : "";
}

// ---------------------------------------------------------------------------
// Monthly subtotal row builder (used by the "Detailed + Monthly Totals" print)
// Sums QTY (waste_water_treated_volume), Fresh Water Consumption, Daily
// Off-Spec, and every chemical qty column - nothing else is subtotalled.
// If a given column is hidden by its own filter (e.g. Daily Off-Spec when
// hide_calculation_and_amount is on), it simply won't be found in `columns`
// and that part of the row is skipped.
// ---------------------------------------------------------------------------

function get_month_label(date_str, is_arabic) {
    if (!date_str) return "";
    const d = frappe.datetime.str_to_obj(date_str);
    try {
        return d.toLocaleString(is_arabic ? "ar" : "en", { month: "long", year: "numeric" });
    } catch (e) {
        return frappe.datetime.str_to_user(date_str);
    }
}

// Generic bold subtotal/total row builder. `totals_map` is a plain
// {fieldname: numeric_value} object - any column whose fieldname appears
// in it gets that value rendered (bold, right-aligned); columns not in the
// map render as an empty cell. Used for both the monthly subtotal rows
// (QTY + Fresh Water Consumption + Daily Off-Spec + every chemical column)
// and reused logic-wise by the grand total row further down.
function build_subtotal_row(columns, label, totals_map, is_arabic) {
    const qty_idx = columns.findIndex((c) => c.fieldname === "waste_water_treated_volume");
    const label_span = Math.max(qty_idx, 1);

    const cells = [];
    cells.push(
        `<td colspan="${label_span}" style="text-align:${
            is_arabic ? "right" : "left"
        }"><b>${frappe.utils.escape_html(label)}</b></td>`
    );

    for (let idx = label_span; idx < columns.length; idx++) {
        const col = columns[idx];
        if (totals_map.hasOwnProperty(col.fieldname)) {
            cells.push(`<td style="text-align:right"><b>${format_total_value(totals_map[col.fieldname], col)}</b></td>`);
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

// Renders daily rows in order, inserting a bold subtotal row every time
// the Project + Unit + Month key changes. Sums QTY (waste_water_treated_volume),
// Fresh Water Consumption (fresh_water_consumption), Daily Off-Spec, and
// every chemical qty column (col.group === "chemical") - nothing else is
// subtotalled. Columns that aren't present (e.g. Daily Off-Spec when
// hide_calculation_and_amount is on) are simply skipped.
function build_body_rows_with_monthly_subtotals(columns, data, is_arabic) {
    const subtotal_fieldnames = columns
        .filter(
            (c) =>
                c.fieldname === "waste_water_treated_volume" ||
                c.fieldname === "fresh_water_consumption" ||
                c.fieldname === "daily_off_spec" ||
                c.group === "chemical"
        )
        .map((c) => c.fieldname);

    let html = "";
    let group_key = null;
    let month_label = "";
    let sums = {};
    let row_idx = 0;

    const reset_sums = () => {
        sums = {};
        subtotal_fieldnames.forEach((f) => (sums[f] = 0));
    };
    reset_sums();

    const flush_group = () => {
        if (group_key === null) return;
        const label = is_arabic ? `إجمالي - ${month_label}` : `Total - ${month_label}`;
        html += build_subtotal_row(columns, label, sums, is_arabic);
    };

    data.forEach((row) => {
        const month_key = (row.date || "").slice(0, 7); // "YYYY-MM"
        const key = `${row.project || ""}|${row.unit || ""}|${month_key}`;

        if (group_key !== null && key !== group_key) {
            flush_group();
            reset_sums();
        }

        group_key = key;
        month_label = get_month_label(row.date, is_arabic);
        subtotal_fieldnames.forEach((f) => {
            sums[f] += flt(row[f]);
        });

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

function render_print_window(columns, data, totals, filters, company, is_arabic, add_monthly_subtotals, ctx) {
    const logo_url = company.company_logo ? frappe.urllib.get_full_url(company.company_logo) : "";
    const company_name = company.company_name || "";
    const is_monthly = !!filters.group_by_month;

    const title = is_arabic
        ? is_monthly
            ? "سجل معالجة المياه (ملخص شهري)"
            : add_monthly_subtotals
            ? "سجل معالجة المياه التفصيلي مع إجمالي شهري"
            : "سجل معالجة المياه"
        : is_monthly
        ? "Water Treatment Register (Monthly Summary)"
        : add_monthly_subtotals
        ? "Water Treatment Register (Detailed, with Monthly Totals)"
        : "Water Treatment Register";
    const date_range_label = is_arabic ? "الفترة" : "Period";
    const date_range = `${frappe.datetime.str_to_user(filters.from_date)} - ${frappe.datetime.str_to_user(filters.to_date)}`;
    const generated_label = is_arabic ? "تاريخ الطباعة" : "Generated on";
    const generated_on = frappe.datetime.now_datetime();

    const group_header_row = build_group_header_row(columns, is_arabic);

    const header_cells = columns
        .map((col) => `<th>${frappe.utils.escape_html(__(col.label))}</th>`)
        .join("");

    // Data comes straight from the server's get_print_data - authoritative,
    // no client-side de-duplication/grouping/re-summing - EXCEPT the monthly
    // subtotal rows below, which only sum QTY / Fresh Water Consumption /
    // Daily Off-Spec / chemical columns for display.
    const body_rows =
        add_monthly_subtotals && !is_monthly
            ? build_body_rows_with_monthly_subtotals(columns, data, is_arabic)
            : build_body_rows(columns, data, is_arabic);

    const totals_label_colspan = columns.findIndex(
        (c) => ((c.fieldtype === "Float" || c.fieldtype === "Currency") && (c.fieldname === "waste_water_treated_volume" || c.fieldname === "total_off_spec_count"))
    );
    const totals_row = columns
        .map((col, idx) => {
            const is_summable =
                totals &&
                totals.hasOwnProperty(col.fieldname) &&
                (col.fieldname === "waste_water_treated_volume" ||
                    col.fieldname === "fresh_water_consumption" ||
                    col.fieldname === "daily_off_spec" ||
                    col.group === "chemical");
            if (is_summable) {
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

        /* Repeats the header block (logo + title + group row + column row)
           on every printed page. Grand total lives in tbody as the LAST
           row, so it prints once at the true end, never per-page. */
        thead.report-header { display: table-header-group; }

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

        tr.group-header-row th {
            background: #dfe2f7;
            color: ${HM_BLUE};
            border: 1px solid #ccc;
            padding: 4px 8px;
            font-size: 10.5px;
            font-weight: 700;
            text-align: center;
        }
        tr.group-header-row th.group-header-inlet {
            background: #dce6ff;
        }
        tr.group-header-row th.group-header-outlet {
            background: #ffe0e0;
        }
        tr.group-header-row th.group-header-chemical {
            background: #e6f7e6;
        }
        tr.group-header-row th.group-header-none {
            background: #f1f2fb;
            border-color: #f1f2fb;
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

        /* Grand total row - a normal tbody row, printed once at the end */
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
            ${group_header_row}
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