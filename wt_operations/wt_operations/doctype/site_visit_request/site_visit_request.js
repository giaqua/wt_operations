// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Site Visit Request', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.status === 'Scheduled' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Create Site Visit'), function() {
				create_site_visit(frm);
			}, __('Actions'));
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date) {
			check_deadline_status(frm);
		}
		
		// Show escalation level if > 0
		if (frm.doc.escalation_level > 0) {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-danger">
					<strong>Escalated:</strong> This request is at escalation level ${frm.doc.escalation_level}
				</div>`
			);
		}
		
		// Auto-calculate deadline on creation
		if (frm.doc.__islocal && !frm.doc.deadline_date) {
			calculate_deadline(frm);
		}
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('status', 'Open');
			frm.set_value('priority', 'Medium');
			frm.set_value('visit_type', 'Initial Assessment');
		}
	},
	
	status: function(frm) {
		// Update workflow stage when status changes
		frm.set_value('workflow_stage', frm.doc.status);
		
		// Auto-assign deadline when scheduled
		if (frm.doc.status === 'Scheduled' && !frm.doc.deadline_date) {
			calculate_deadline(frm);
		}
	},
	
	priority: function(frm) {
		// Recalculate deadline based on priority
		if (frm.doc.priority) {
			calculate_deadline(frm);
		}
	},
	
	technical_questionnaire: function(frm) {
		// Auto-populate fields from technical questionnaire
		if (frm.doc.technical_questionnaire) {
			populate_from_questionnaire(frm);
		}
	},
	
	assigned_to: function(frm) {
		// Send notification to assigned user
		if (frm.doc.assigned_to && !frm.doc.__islocal) {
			send_assignment_notification(frm);
		}
	}
});

function create_site_visit(frm) {
	frappe.new_doc('Site Visit', {
		'site_visit_request': frm.doc.name,
		'lead': frm.doc.lead,
		'opportunity': frm.doc.opportunity,
		'technical_questionnaire': frm.doc.technical_questionnaire,
		'visit_date': frm.doc.site_visit_date,
		'assigned_to': frm.doc.assigned_to,
		'visit_type': frm.doc.visit_type,
		'priority': frm.doc.priority
	});
}

function calculate_deadline(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.calculate_site_visit_deadline',
		args: {
			priority: frm.doc.priority,
			visit_type: frm.doc.visit_type
		},
		callback: function(r) {
			if (r.message && r.message.deadline) {
				frm.set_value('deadline_date', r.message.deadline);
			}
		}
	});
}

function populate_from_questionnaire(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'WWTP Technical Questionnaire',
			name: frm.doc.technical_questionnaire
		},
		callback: function(r) {
			if (r.message) {
				const tq = r.message;
				
				// Populate basic fields
				if (tq.lead && !frm.doc.lead) {
					frm.set_value('lead', tq.lead);
				}
				if (tq.opportunity && !frm.doc.opportunity) {
					frm.set_value('opportunity', tq.opportunity);
				}
				if (tq.assigned_site_manager && !frm.doc.assigned_to) {
					frm.set_value('assigned_to', tq.assigned_site_manager);
				}
				
				// Set visit purpose based on questionnaire
				if (!frm.doc.visit_purpose) {
					let purpose = `Site assessment for ${tq.wastewater_generator_type} wastewater treatment plant`;
					if (tq.capacity) {
						purpose += ` with capacity of ${tq.capacity} m3/day`;
					}
					frm.set_value('visit_purpose', purpose);
				}
				
				// Set parent reference
				frm.set_value('parent_technical_questionnaire', tq.name);
			}
		}
	});
}

function send_assignment_notification(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.send_site_visit_assignment_notification',
		args: {
			site_visit_request: frm.doc.name,
			assigned_user: frm.doc.assigned_to
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert(__('Assignment notification sent'));
			}
		}
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
				<strong>Overdue:</strong> This site visit request is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> This site visit request is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 3) {
		// Due within 3 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> This site visit request is due in ${days_diff} days
			</div>`
		);
	}
}