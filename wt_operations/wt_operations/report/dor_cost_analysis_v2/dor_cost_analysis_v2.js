// ============================================================
// DOR Cost Analysis - Script Report client script
// Defines filters (date range or Month/Year shortcut, project,
// group-by Month/Project, exclude-zero-volume, and the Cost /
// Cost per M3 / Both display toggle), highlights the "/ M3"
// columns, and adds a "Print" button that calls the whitelisted
// get_print_html() Python method, which returns a fully-rendered
// HTML page (company logo/name, colored header, KPI cards). That
// HTML opens in a new tab and triggers the browser's print dialog -
// a normal print preview the user can review before printing or
// saving as PDF, rather than a PDF being generated up front.
//
// IMPORTANT: update PY_MODULE_PATH below to match where you place
// this report folder, e.g.
//   "your_app.water_treatment_operations.report.dor_cost_analysis.dor_cost_analysis"
// (app_name.module_name_snake_case.report.report_name.report_name)
// ============================================================

const PY_MODULE_PATH =
	"wt_operations.wt_operations.report.dor_cost_analysis_v2.dor_cost_analysis_v2";

frappe.query_reports["DOR Cost Analysis v2"] = {
	onload(report) {
		report.page.add_inner_button(__("Print"), () => {
			print_dor_cost_analysis(report);
		});
	},

	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "filter_month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				"",
				"January",
				"February",
				"March",
				"April",
				"May",
				"June",
				"July",
				"August",
				"September",
				"October",
				"November",
				"December",
			],
			description: __("Optional - overrides From/To Date with the full selected month"),
		},
		{
			fieldname: "filter_year",
			label: __("Year"),
			fieldtype: "Select",
			options: get_year_options(),
			default: String(new Date().getFullYear()),
			depends_on: "eval:doc.filter_month",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["None", "Month", "Project", "Month + Project"],
			default: "None",
			reqd: 1,
		},
		{
			fieldname: "exclude_zero_volume",
			label: __("Exclude Zero Treated Water"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "display",
			label: __("Show"),
			fieldtype: "Select",
			options: ["Both", "Cost Only", "Cost per M3 Only"],
			default: "Both",
			reqd: 1,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.is_total_row) {
			value = `<b>${value}</b>`;
		}

		if (column.fieldname && column.fieldname.endsWith("_per_m3")) {
			value = `<span style="color:#1976a8; font-weight:600;">${value}</span>`;
		}

		return value;
	},
};

// ------------------------------------------------------------
// Print button handler
// All data fetching, grouping, and totals math happen server-side
// in get_print_html() (Python) - this just calls it and opens the
// returned HTML in a new tab. The tab triggers the browser's native
// print dialog on load, which is itself a preview the user can
// review, adjust, or cancel before actually printing/saving as PDF.
// No PDF is generated or downloaded up front.
// ------------------------------------------------------------
function print_dor_cost_analysis(report) {
	const filters = frappe.query_report.get_filter_values(true);

	if (!filters.filter_month && (!filters.from_date || !filters.to_date)) {
		frappe.msgprint(__("Please set a From/To Date range, or pick a Month, before printing."));
		return;
	}

	frappe.call({
		method: `${PY_MODULE_PATH}.get_print_html`,
		args: { filters },
		freeze: true,
		freeze_message: __("Preparing print preview..."),
		callback(r) {
			if (r.exc || !r.message) {
				frappe.msgprint(__("Could not build the print preview. Check the error log for details."));
				return;
			}

			const preview_window = window.open("", "_blank");
			preview_window.document.write(r.message);
			preview_window.document.close();
		},
	});
}

function get_year_options() {
	const current_year = new Date().getFullYear();
	const years = [""];
	for (let y = current_year - 5; y <= current_year + 1; y++) {
		years.push(String(y));
	}
	return years;
}