// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Water Sample', {
	refresh: function(frm) {
		// Add custom buttons based on sample status
		if (frm.doc.sample_status === 'In Lab' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Create Lab Test Result'), function() {
				create_lab_test_result(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.sample_status === 'Analyzed' && frm.doc.results_available) {
			frm.add_custom_button(__('View Lab Results'), function() {
				view_lab_results(frm);
			}, __('Actions'));
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date || frm.doc.expected_results_date) {
			check_deadline_status(frm);
		}
		
		// Show compliance status indicator
		if (frm.doc.compliance_status) {
			show_compliance_indicator(frm);
		}
		
		// Auto-calculate expected results date on creation
		if (frm.doc.__islocal && !frm.doc.expected_results_date) {
			calculate_expected_results_date(frm);
		}
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('sample_status', 'Collected');
			frm.set_value('lab_priority', 'Medium');
			frm.set_value('date_collected', frappe.datetime.nowdate());
			frm.set_value('time_collected', frappe.datetime.now_time());
		}
	},
	
	sample_status: function(frm) {
		// Update related documents when status changes
		if (frm.doc.sample_status === 'Results Available') {
			frm.set_value('results_available', 1);
			frm.set_value('analysis_completed', frappe.datetime.nowdate());
		}
		
		// Auto-create lab test result when sample reaches lab
		if (frm.doc.sample_status === 'In Lab' && !frm.doc.__islocal) {
			auto_create_lab_test_result(frm);
		}
	},
	
	lab_priority: function(frm) {
		// Recalculate expected results date based on priority
		if (frm.doc.lab_priority) {
			calculate_expected_results_date(frm);
		}
	},
	
	sample_type: function(frm) {
		// Set default analysis parameters based on sample type
		set_default_analysis_parameters(frm);
	},
	
	related_visit: function(frm) {
		// Auto-populate fields from site visit
		if (frm.doc.related_visit) {
			populate_from_site_visit(frm);
		}
	},
	
	wwtp_technical_questionnaire: function(frm) {
		// Auto-populate lead and opportunity
		if (frm.doc.wwtp_technical_questionnaire) {
			populate_from_questionnaire(frm);
		}
	}
});

function create_lab_test_result(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.create_lab_test_result_from_sample',
		args: {
			water_sample: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__(`Lab Test Result ${r.message.lab_test_name} created successfully`));
				frappe.set_route('Form', 'Lab Test Result', r.message.lab_test_name);
			} else {
				frappe.msgprint(__('Failed to create Lab Test Result: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function auto_create_lab_test_result(frm) {
	// Check if lab test result already exists
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Lab Test Result',
			filters: {
				'sample_tag': frm.doc.name
			},
			limit: 1
		},
		callback: function(r) {
			if (!r.message || r.message.length === 0) {
				// No existing lab test result, create one
				create_lab_test_result(frm);
			}
		}
	});
}

function view_lab_results(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Lab Test Result',
			filters: {
				'sample_tag': frm.doc.name
			},
			fields: ['name'],
			limit: 1
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				frappe.set_route('Form', 'Lab Test Result', r.message[0].name);
			} else {
				frappe.msgprint(__('No lab test results found for this sample'));
			}
		}
	});
}

function calculate_expected_results_date(frm) {
	const priority_days = {
		'Urgent': 1,
		'High': 2,
		'Medium': 5,
		'Low': 7
	};
	
	const days = priority_days[frm.doc.lab_priority] || 5;
	const expected_date = frappe.datetime.add_days(frm.doc.date_collected, days);
	
	frm.set_value('expected_results_date', expected_date);
	frm.set_value('deadline_date', expected_date);
}

function set_default_analysis_parameters(frm) {
	const sample_type = frm.doc.sample_type;
	
	// Set default analysis based on sample type
	let default_analysis = '';
	
	switch(sample_type) {
		case 'Influent':
			default_analysis = 'pH, TSS, BOD5, COD, TDS, Oil & Grease, E.coli';
			break;
		case 'Effluent':
			default_analysis = 'pH, TSS, BOD5, COD, Turbidity, Free Chlorine, E.coli';
			break;
		case 'Process Water':
			default_analysis = 'pH, TSS, COD, TDS';
			break;
		case 'Sludge':
			default_analysis = 'Moisture Content, Volatile Solids, Heavy Metals';
			break;
		default:
			default_analysis = 'pH, TSS, BOD5, COD';
	}
	
	if (!frm.doc.analysis_requested) {
		frm.set_value('analysis_requested', default_analysis);
	}
}

function populate_from_site_visit(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Site Visit Request',
			name: frm.doc.related_visit
		},
		callback: function(r) {
			if (r.message) {
				const sv = r.message;
				
				if (sv.lead && !frm.doc.lead) {
					frm.set_value('lead', sv.lead);
				}
				if (sv.technical_questionnaire && !frm.doc.wwtp_technical_questionnaire) {
					frm.set_value('wwtp_technical_questionnaire', sv.technical_questionnaire);
				}
				if (sv.opportunity && !frm.doc.opportunity) {
					frm.set_value('opportunity', sv.opportunity);
				}
			}
		}
	});
}

function populate_from_questionnaire(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'WWTP Technical Questionnaire',
			name: frm.doc.wwtp_technical_questionnaire
		},
		callback: function(r) {
			if (r.message) {
				const tq = r.message;
				
				if (tq.lead && !frm.doc.lead) {
					frm.set_value('lead', tq.lead);
				}
				if (tq.opportunity && !frm.doc.opportunity) {
					frm.set_value('opportunity', tq.opportunity);
				}
			}
		}
	});
}

function show_compliance_indicator(frm) {
	const status = frm.doc.compliance_status;
	let alert_class = 'info';
	let message = '';
	
	switch(status) {
		case 'Compliant':
			alert_class = 'success';
			message = 'Sample results are compliant with standards';
			break;
		case 'Non-Compliant':
			alert_class = 'danger';
			message = 'Sample results are non-compliant with standards';
			break;
		case 'Pending':
			alert_class = 'warning';
			message = 'Compliance status is pending review';
			break;
	}
	
	if (message) {
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-${alert_class}">
				<strong>Compliance Status:</strong> ${message}
			</div>`
		);
	}
}

function check_deadline_status(frm) {
	const deadline = frm.doc.deadline_date || frm.doc.expected_results_date;
	if (!deadline) return;
	
	const deadline_date = frappe.datetime.str_to_obj(deadline);
	const today = frappe.datetime.now_date();
	const days_diff = frappe.datetime.get_diff(deadline_date, today);
	
	if (days_diff < 0) {
		// Overdue
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-danger">
				<strong>Overdue:</strong> Results are ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> Results are due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 2) {
		// Due within 2 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> Results are due in ${days_diff} days
			</div>`
		);
	}
}