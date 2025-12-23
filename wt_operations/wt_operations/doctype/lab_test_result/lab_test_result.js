// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Lab Test Result', {
	refresh: function(frm) {
		// Add custom buttons based on compliance status
		if (frm.doc.compliance_status === 'Approved' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Update Water Sample'), function() {
				update_water_sample_results(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.compliance_status === 'Non-Compliant') {
			frm.add_custom_button(__('Create Retest'), function() {
				create_retest(frm);
			}, __('Actions'));
		}
		
		// Show compliance status indicator
		if (frm.doc.compliance_status) {
			show_compliance_indicator(frm);
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date) {
			check_deadline_status(frm);
		}
		
		// Auto-populate test template parameters
		if (frm.doc.test_template && (!frm.doc.lab_test_results_parameters || frm.doc.lab_test_results_parameters.length === 0)) {
			populate_test_parameters(frm);
		}
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('compliance_status', 'Draft');
			frm.set_value('test_priority', 'Medium');
			frm.set_value('sample_receipt_date', frappe.datetime.now_datetime());
		}
	},
	
	compliance_status: function(frm) {
		// Update timestamps based on status changes
		if (frm.doc.compliance_status === 'In Progress' && !frm.doc.analysis_start_date) {
			frm.set_value('analysis_start_date', frappe.datetime.now_datetime());
		}
		
		if (frm.doc.compliance_status === 'Approved') {
			if (!frm.doc.analysis_completion_date) {
				frm.set_value('analysis_completion_date', frappe.datetime.now_datetime());
			}
			if (!frm.doc.approval_date) {
				frm.set_value('approval_date', frappe.datetime.now_datetime());
			}
			if (!frm.doc.approved_by_user) {
				frm.set_value('approved_by_user', frappe.session.user);
			}
		}
		
		// Auto-check compliance when reviewed
		if (frm.doc.compliance_status === 'Reviewed') {
			check_regulatory_compliance(frm);
		}
	},
	
	test_template: function(frm) {
		// Populate parameters from template
		if (frm.doc.test_template) {
			populate_test_parameters(frm);
		}
	},
	
	regulatory_standard: function(frm) {
		// Recheck compliance when standard changes
		if (frm.doc.regulatory_standard && frm.doc.lab_test_results_parameters) {
			check_regulatory_compliance(frm);
		}
	},
	
	sample_tag: function(frm) {
		// Auto-populate from water sample if exists
		if (frm.doc.sample_tag) {
			populate_from_water_sample(frm);
		}
	},
	
	test_priority: function(frm) {
		// Recalculate deadline based on priority
		if (frm.doc.test_priority) {
			calculate_deadline(frm);
		}
	}
});

// Child table events for lab test parameters
frappe.ui.form.on('Lab Test Results Parameters', {
	result_value: function(frm, cdt, cdn) {
		// Check compliance when result value changes
		check_parameter_compliance(frm, cdt, cdn);
	},
	
	lab_test_results_parameters_add: function(frm, cdt, cdn) {
		// Set default values for new parameter row
		const row = locals[cdt][cdn];
		if (!row.unit) {
			row.unit = 'mg/L';
		}
	}
});

function populate_test_parameters(frm) {
	if (!frm.doc.test_template) return;
	
	frappe.call({
		method: 'wt_operations.wt_operations.api.get_test_template_parameters',
		args: {
			template_name: frm.doc.test_template
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				// Clear existing parameters
				frm.clear_table('lab_test_results_parameters');
				
				// Add parameters from template
				r.message.parameters.forEach(param => {
					const row = frm.add_child('lab_test_results_parameters');
					row.parameter_name = param.parameter_name;
					row.unit = param.unit;
					row.normal_range = param.normal_range;
					row.method = param.test_method;
				});
				
				frm.refresh_field('lab_test_results_parameters');
			}
		}
	});
}

function populate_from_water_sample(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Water Sample',
			filters: {
				'name': frm.doc.sample_tag
			},
			fields: ['*'],
			limit: 1
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				const sample = r.message[0];
				
				// Populate basic fields
				if (sample.date_collected && !frm.doc.date_sample_received) {
					frm.set_value('date_sample_received', sample.date_collected);
				}
				if (sample.lab_priority && !frm.doc.test_priority) {
					frm.set_value('test_priority', sample.lab_priority);
				}
				if (sample.expected_results_date && !frm.doc.deadline_date) {
					frm.set_value('deadline_date', sample.expected_results_date);
				}
				
				// Set lab technician if collected by someone
				if (sample.collected_by && !frm.doc.lab_technician) {
					frm.set_value('lab_technician', sample.collected_by);
				}
			}
		}
	});
}

function check_regulatory_compliance(frm) {
	if (!frm.doc.regulatory_standard || !frm.doc.lab_test_results_parameters) return;
	
	frappe.call({
		method: 'wt_operations.wt_operations.api.check_lab_result_compliance',
		args: {
			lab_test_result: frm.doc.name,
			regulatory_standard: frm.doc.regulatory_standard
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frm.set_value('compliance_status', r.message.compliance_status);
				
				if (r.message.non_compliant_parameters && r.message.non_compliant_parameters.length > 0) {
					frappe.msgprint({
						title: __('Compliance Check Results'),
						message: __('Non-compliant parameters: ') + r.message.non_compliant_parameters.join(', '),
						indicator: 'red'
					});
				}
			}
		}
	});
}

function check_parameter_compliance(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	
	if (!row.result_value || !row.normal_range) return;
	
	// Simple range check (assumes format like "0-10" or "<5")
	let is_compliant = true;
	const value = parseFloat(row.result_value);
	
	if (row.normal_range.includes('-')) {
		const [min, max] = row.normal_range.split('-').map(v => parseFloat(v.trim()));
		is_compliant = value >= min && value <= max;
	} else if (row.normal_range.startsWith('<')) {
		const max_val = parseFloat(row.normal_range.substring(1));
		is_compliant = value < max_val;
	} else if (row.normal_range.startsWith('>')) {
		const min_val = parseFloat(row.normal_range.substring(1));
		is_compliant = value > min_val;
	}
	
	// Update row styling based on compliance
	if (is_compliant) {
		row.compliance_status = 'Compliant';
	} else {
		row.compliance_status = 'Non-Compliant';
	}
	
	frm.refresh_field('lab_test_results_parameters');
}

function update_water_sample_results(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.update_water_sample_from_lab_results',
		args: {
			lab_test_result: frm.doc.name,
			sample_tag: frm.doc.sample_tag
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__('Water Sample updated with lab results'));
			} else {
				frappe.msgprint(__('Failed to update Water Sample: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function create_retest(frm) {
	frappe.confirm(
		__('Create a retest for this non-compliant sample?'),
		function() {
			frappe.call({
				method: 'wt_operations.wt_operations.api.create_retest_lab_result',
				args: {
					original_test: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.msgprint(__(`Retest ${r.message.retest_name} created successfully`));
						frappe.set_route('Form', 'Lab Test Result', r.message.retest_name);
					} else {
						frappe.msgprint(__('Failed to create retest: ') + (r.message.error || 'Unknown error'));
					}
				}
			});
		}
	);
}

function calculate_deadline(frm) {
	const priority_days = {
		'Urgent': 1,
		'High': 2,
		'Medium': 3,
		'Low': 5
	};
	
	const days = priority_days[frm.doc.test_priority] || 3;
	const deadline = frappe.datetime.add_days(frm.doc.sample_receipt_date || frappe.datetime.nowdate(), days);
	
	frm.set_value('deadline_date', deadline);
}

function show_compliance_indicator(frm) {
	const status = frm.doc.compliance_status;
	let alert_class = 'info';
	let message = '';
	
	switch(status) {
		case 'Approved':
			alert_class = 'success';
			message = 'Lab test results have been approved';
			break;
		case 'Non-Compliant':
			alert_class = 'danger';
			message = 'Lab test results are non-compliant with standards';
			break;
		case 'In Progress':
			alert_class = 'warning';
			message = 'Lab test analysis is in progress';
			break;
		case 'Reviewed':
			alert_class = 'info';
			message = 'Lab test results are under review';
			break;
	}
	
	if (message) {
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-${alert_class}">
				<strong>Status:</strong> ${message}
			</div>`
		);
	}
}

function check_deadline_status(frm) {
	if (!frm.doc.deadline_date) return;
	
	const deadline = frappe.datetime.str_to_obj(frm.doc.deadline_date);
	const today = frappe.datetime.now_date();
	const days_diff = frappe.datetime.get_diff(deadline, today);
	
	if (days_diff < 0) {
		// Overdue
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-danger">
				<strong>Overdue:</strong> Lab test is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> Lab test is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 2) {
		// Due within 2 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> Lab test is due in ${days_diff} days
			</div>`
		);
	}
}