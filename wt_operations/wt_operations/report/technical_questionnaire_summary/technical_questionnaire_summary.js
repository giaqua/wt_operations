// Copyright (c) 2025, Takamol and contributors
// For license information, please see license.txt

frappe.query_reports["Technical Questionnaire Summary"] = {
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
	"formatter":function (value, row, column, data, default_formatter) {
		// console.log(typeof(value??""),"aaaaaasssssssssssssssaaaa"+value);
		
		// console.log(typeof(value??""),"aaaaaaaaaa"+value);
	
		
		// console.log(column.id,"bbbbbbbbbb",column,"ccccccccccc",data,"dddddddddd",value,"eeeeeee",row);
		
		if (column.fieldname === "visit_request" && data?.visit_request) {
            let color = data.visit_request > 0 ? "white" : "#f11616ff";
            let bg = data.visit_request > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.visit_request}</span>`;
        }
		if (column.fieldname === "site_visit" && data?.site_visit) {
            let color = data.site_visit > 0 ? "white" : "#f11616ff";
            let bg = data.site_visit > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.site_visit}</span>`;
        }
		if (column.fieldname === "water_sample" && data?.water_sample) {
            let color = data.water_sample > 0 ? "white" : "#f11616ff";
            let bg = data.water_sample > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.water_sample}</span>`;
        }
		if (column.fieldname === "lab_test_result" && data?.lab_test_result) {
            let color = data.lab_test_result > 0 ? "white" : "#f11616ff";
            let bg = data.lab_test_result > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.lab_test_result}</span>`;
        }
		if (column.fieldname === "technical_proposal" && data?.technical_proposal) {
            let color = data.technical_proposal > 0 ? "white" : "#f11616ff";
            let bg = data.technical_proposal > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.technical_proposal}</span>`;
        }
		if (column.fieldname === "customer_proposal" && data?.customer_proposal) {
            let color = data.customer_proposal > 0 ? "white" : "#f11616ff";
            let bg = data.customer_proposal > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.customer_proposal}</span>`;
        }
		if (column.fieldname === "request_for_proposal" && data?.request_for_proposal) {
            let color = data.request_for_proposal > 0 ? "white" : "#f11616ff";
            let bg = data.request_for_proposal > 0 ? "green" : "#f20606ff";
            return `<span style="background: ${bg}; color: ${color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${data.request_for_proposal}</span>`;
        }
		if (column.fieldname === "achieved_operations") {
			// if(value=="100" || value==100 ||  value ==100){
			// 	$(row).css('background-color', '#ffcccc');
			// }
            return `<span style="color: green;font-weight:bold;">${value}%</span>`;
        }
		if (column.fieldname === "pending_operations") {
            return `<span style="color: red;font-weight:bold;">${value}%</span>`;
        }
		if (column.fieldname === "delay_days") {
            let color = value > 2 ? "red" : "black";
            return `<span style="color: ${color};font-weight:bold;">${value}</span>`;
        }
	
		
		if(value=="0" || value==0 ||  value ==0){
			return "<span style='color:red;font-weight:bold'>0</span>";
		}
		value = default_formatter(value, row, column, data);
		// value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
	
        	return value;
        },
	"onload": function(report) {
        // Export button
        report.page.add_inner_button(__("Export to Excel"), function() {
            frappe.query_report.export_report();
        });
		//  report.page.add_inner_button(__("Print"), function() {
        //     frappe.query_report.print_report();
        // })
		// frappe.query_report.create_charts();
	}
};

/* Force reverse order for all report tiles */
// div[data-page-route*="query-report"] .report-summary {
//     display: grid !important;
//     grid-auto-flow: row !important;
//     direction: rtl !important;
// }
function reverseReportTiles() {
	const reportSummary = document.querySelector('.report-summary');
	if (reportSummary) {
		reportSummary.style.display = 'grid';
		reportSummary.style.gridAutoFlow = 'row';
		reportSummary.style.direction = 'rtl';
	}
}

// Call the function to apply the styles
// reverseReportTiles();

// Optional: If the report tiles are loaded dynamically, you might want to use a MutationObserver to watch for changes and reapply the styles
// const observer = new MutationObserver(reverseReportTiles);
// observer.observe(document.body, { childList: true, subtree: true });

function add_charts_to_report() {
	// Your code to add charts goes here
	console.log("add_charts_to_report function called");
	// Example: You can create a chart using a library like Chart.js or D3.js
	// and append it to the report container.
	document.addEventListener("DOMContentLoaded", function() {
		// Ensure the report container is available
		const reportContainer = document.querySelector('.report-summary');
		if (1) {
			console.log("=============");
			// Create a canvas element for Chart.js
			const canvas = document.createElement('canvas');
			canvas.id = 'myChart';
			reportContainer.appendChild(canvas);

			// Example Chart.js code (make sure to include Chart.js library in your project)
			const ctx = canvas.getContext('2d');
			const myChart = new Chart(ctx, {
				type: 'bar',
				data: {
					labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
					datasets: [{
						label: '# of Votes',
						data: [12, 19, 3, 5, 2, 3],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)'
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)'
						],
						borderWidth: 1
					}]
				},
				options: {
					scales: {
						y: {
							beginAtZero: true
						}
					}
				}
			});
		}
	});	
	chartAdded = true;	
	// document.removeEventListener("DOMContentLoaded", add_charts_to_report);

}

// Call the function to add charts
add_charts_to_report()