// ============================================================
// DOR Cost Analysis - Script Report client script
// Defines filters (date range or Month/Year shortcut, project,
// group-by Month/Project, exclude-zero-volume, and the Cost /
// Cost per M3 / Both display toggle), highlights the "/ M3"
// columns, and adds a "Print" button that calls the whitelisted
// get_print_pdf() Python method to render and return a branded
// PDF (company logo/name, colored header, KPI cards).
//
// IMPORTANT: update PY_MODULE_PATH below to match where you place
// this report folder, e.g.
//   "your_app.water_treatment_operations.report.dor_cost_analysis.dor_cost_analysis"
// (app_name.module_name_snake_case.report.report_name.report_name)
// ============================================================

const PY_MODULE_PATH =
	"wt_operations.wt_operations.report.dor_cost_analysis.dor_cost_analysis";

frappe.query_reports["DOR Cost Analysis"] = {
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
// All rendering happens server-side in get_print_pdf() (Python) -
// this just validates filters, calls it, and opens the returned
// PDF (base64) in a new tab as a Blob.
// ------------------------------------------------------------
function print_dor_cost_analysis(report) {
	const filters = frappe.query_report.get_filter_values(true);

	if (!filters.filter_month && (!filters.from_date || !filters.to_date)) {
		frappe.msgprint(__("Please set a From/To Date range, or pick a Month, before printing."));
		return;
	}

	frappe.call({
		method: `${PY_MODULE_PATH}.get_print_pdf`,
		args: { filters },
		freeze: true,
		freeze_message: __("Generating PDF..."),
		callback(r) {
			if (r.exc || !r.message) {
				frappe.msgprint(__("Could not generate the PDF. Check the error log for details."));
				return;
			}

			const pdf_blob = base64_to_blob(r.message, "application/pdf");
			const blob_url = URL.createObjectURL(pdf_blob);
			window.open(blob_url, "_blank");
		},
	});
}

function base64_to_blob(base64_data, content_type) {
	const byte_chars = atob(base64_data);
	const byte_numbers = new Array(byte_chars.length);
	for (let i = 0; i < byte_chars.length; i++) {
		byte_numbers[i] = byte_chars.charCodeAt(i);
	}
	const byte_array = new Uint8Array(byte_numbers);
	return new Blob([byte_array], { type: content_type });
}

function get_year_options() {
	const current_year = new Date().getFullYear();
	const years = [""];
	for (let y = current_year - 5; y <= current_year + 1; y++) {
		years.push(String(y));
	}
	return years;
}