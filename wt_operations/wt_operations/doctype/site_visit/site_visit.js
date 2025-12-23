// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Site Visit', {
	refresh: function(frm) {
		// Add custom buttons based on completion status
		if (frm.doc.completion_status === 'Conducted' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Create Water Sample'), function() {
				create_water_sample(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.completion_status === 'Reported' && frm.doc.follow_up_required) {
			frm.add_custom_button(__('Schedule Follow-up'), function() {
				schedule_follow_up(frm);
			}, __('Actions'));
		}
		
		// Show quality score indicator
		if (frm.doc.quality_score) {
			frm.dashboard.add_progress(__('Quality Score'), frm.doc.quality_score * 20); // Convert 5-star to percentage
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date) {
			check_deadline_status(frm);
		}
		
		// Auto-calculate quality score based on completion
		if (frm.doc.completion_status === 'Conducted' && !frm.doc.quality_score) {
			calculate_quality_score(frm);
		}
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('completion_status', 'Draft');
		}
	},
	
	completion_status: function(frm) {
		// Update related site visit request status
		if (frm.doc.related_site_visit_request && frm.doc.completion_status) {
			update_site_visit_request_status(frm);
		}
		
		// Auto-calculate quality score when conducted
		if (frm.doc.completion_status === 'Conducted') {
			calculate_quality_score(frm);
		}
	},
	
	samples_collected: function(frm) {
		// Show/hide samples table
		frm.toggle_display('samples_table', frm.doc.samples_collected);
		
		// Auto-create water sample records if samples collected
		if (frm.doc.samples_collected && !frm.doc.__islocal) {
			create_water_samples_from_table(frm);
		}
	},
	
	follow_up_required: function(frm) {
		// Show/hide follow-up fields
		frm.toggle_display('follow_up_date', frm.doc.follow_up_required);
		frm.toggle_display('follow_up_required_date', frm.doc.follow_up_required);
		
		// Set default follow-up date
		if (frm.doc.follow_up_required && !frm.doc.follow_up_date) {
			const follow_up_date = frappe.datetime.add_days(frm.doc.date, 7);
			frm.set_value('follow_up_date', follow_up_date);
		}
	},
	
	related_site_visit_request: function(frm) {
		// Auto-populate fields from site visit request
		if (frm.doc.related_site_visit_request) {
			populate_from_site_visit_request(frm);
		}
	}
});

function create_water_sample(frm) {
	frappe.new_doc('Water Sample', {
		'site_visit': frm.doc.name,
		'lead': frm.doc.lead,
		'wwtp_technical_questionnaire': frm.doc.wwtp_technical_questionnaire,
		'collection_date': frm.doc.date,
		'collected_by': frm.doc.visit_by,
		'sample_location': frm.doc.site_name,
		'sample_address': frm.doc.site_address
	});
}

function schedule_follow_up(frm) {
	frappe.new_doc('Site Visit Request', {
		'lead': frm.doc.lead,
		'technical_questionnaire': frm.doc.wwtp_technical_questionnaire,
		'visit_type': 'Follow-up Visit',
		'site_visit_date': frm.doc.follow_up_date,
		'priority': 'Medium',
		'notes': `Follow-up visit for site visit ${frm.doc.name}`
	});
}

function calculate_quality_score(frm) {
	let score = 0;
	let total_criteria = 0;
	
	// Check completion criteria
	const criteria = [
		'site_observations',
		'technical_observations', 
		'recommendations',
		'photos_taken',
		'measurements_recorded'
	];
	
	criteria.forEach(field => {
		total_criteria++;
		if (frm.doc[field]) {
			score++;
		}
	});
	
	// Additional points for comprehensive data
	if (frm.doc.samples_collected) {
		score += 0.5;
		total_criteria += 0.5;
	}
	
	if (frm.doc.sketches_made) {
		score += 0.5;
		total_criteria += 0.5;
	}
	
	// Calculate quality score (1-5 scale)
	const quality_score = Math.round((score / total_criteria) * 5);
	frm.set_value('quality_score', quality_score);
}

function update_site_visit_request_status(frm) {
	if (!frm.doc.related_site_visit_request) return;
	
	frappe.call({
		method: 'wt_operations.wt_operations.api.update_site_visit_request_from_visit',
		args: {
			site_visit_request: frm.doc.related_site_visit_request,
			site_visit_status: frm.doc.completion_status
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert(__('Site Visit Request status updated'));
			}
		}
	});
}

function populate_from_site_visit_request(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Site Visit Request',
			name: frm.doc.related_site_visit_request
		},
		callback: function(r) {
			if (r.message) {
				const svr = r.message;
				
				// Populate basic fields
				if (svr.lead && !frm.doc.lead) {
					frm.set_value('lead', svr.lead);
				}
				if (svr.technical_questionnaire && !frm.doc.wwtp_technical_questionnaire) {
					frm.set_value('wwtp_technical_questionnaire', svr.technical_questionnaire);
				}
				if (svr.site_visit_date && !frm.doc.date) {
					frm.set_value('date', svr.site_visit_date);
				}
				if (svr.assigned_to && !frm.doc.visit_by) {
					frm.set_value('visit_by', svr.assigned_to);
				}
				
				// Populate contact information
				if (svr.contact_person && !frm.doc.contact_person) {
					frm.set_value('contact_person', svr.contact_person);
				}
				if (svr.contact_number && !frm.doc.contact_number) {
					frm.set_value('contact_number', svr.contact_number);
				}
				if (svr.email && !frm.doc.email) {
					frm.set_value('email', svr.email);
				}
				
				// Populate location information
				if (svr.site_address && !frm.doc.site_address) {
					frm.set_value('site_address', svr.site_address);
				}
				if (svr.city && !frm.doc.city) {
					frm.set_value('city', svr.city);
				}
				if (svr.state && !frm.doc.state) {
					frm.set_value('state', svr.state);
				}
			}
		}
	});
}

function create_water_samples_from_table(frm) {
	if (!frm.doc.samples_table || frm.doc.samples_table.length === 0) return;
	
	frm.doc.samples_table.forEach(sample_row => {
		frappe.call({
			method: 'wt_operations.wt_operations.api.create_water_sample_from_site_visit',
			args: {
				site_visit: frm.doc.name,
				sample_data: sample_row
			},
			callback: function(r) {
				if (r.message && r.message.success) {
					frappe.show_alert(__(`Water Sample ${r.message.sample_name} created`));
				}
			}
		});
	});
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
				<strong>Overdue:</strong> This site visit is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> This site visit is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 3) {
		// Due within 3 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> This site visit is due in ${days_diff} days
			</div>`
		);
	}
}