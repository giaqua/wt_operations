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
		console.log(typeof(value??""),"aaaaaasssssssssssssssaaaa"+value);
		
		console.log(typeof(value??""),"aaaaaaaaaa"+value);
	
		
		console.log(column.id,"bbbbbbbbbb",column,"ccccccccccc",data,"dddddddddd",value,"eeeeeee",row);
		
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
	
		
		if(value=="0" || value==0 ||  value ==0){
			return "<span style='color:red;font-weight:bold'>0</span>";
		}
		value = default_formatter(value, row, column, data);
		// value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
	
        	return value;
        }
};
