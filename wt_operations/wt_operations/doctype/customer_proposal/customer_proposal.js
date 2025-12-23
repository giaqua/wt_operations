// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Proposal', {
	refresh: function(frm) {
		// Add custom buttons based on workflow status
		if (frm.doc.workflow_status === 'Approved' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Send to Customer'), function() {
				send_to_customer(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.workflow_status === 'Sent to Customer') {
			frm.add_custom_button(__('Create RFP'), function() {
				create_rfp(frm);
			}, __('Actions'));
			
			frm.add_custom_button(__('Schedule Follow-up'), function() {
				schedule_follow_up(frm);
			}, __('Actions'));
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date || frm.doc.customer_response_deadline) {
			check_deadline_status(frm);
		}
		
		// Show proposal priority indicator
		if (frm.doc.proposal_priority) {
			show_priority_indicator(frm);
		}
		
		// Auto-populate from technical proposal on creation
		if (frm.doc.__islocal && frm.doc.wwtp_technical_proposal) {
			populate_from_technical_proposal(frm);
		}
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('workflow_status', 'Draft');
			frm.set_value('proposal_priority', 'Medium');
			frm.set_value('issue_date', frappe.datetime.nowdate());
			frm.set_value('prepared_by', frappe.session.user);
			
			// Set default validity period (30 days)
			const valid_until = frappe.datetime.add_days(frappe.datetime.nowdate(), 30);
			frm.set_value('valid_up_to', valid_until);
			
			// Set customer response deadline (45 days)
			const response_deadline = frappe.datetime.add_days(frappe.datetime.nowdate(), 45);
			frm.set_value('customer_response_deadline', response_deadline);
		}
	},
	
	wwtp_technical_proposal: function(frm) {
		// Auto-populate from technical proposal
		if (frm.doc.wwtp_technical_proposal) {
			populate_from_technical_proposal(frm);
		}
	},
	
	proposal_priority: function(frm) {
		// Adjust deadlines based on priority
		if (frm.doc.proposal_priority) {
			adjust_deadlines_by_priority(frm);
		}
	},
	
	workflow_status: function(frm) {
		// Update timestamps when status changes
		if (frm.doc.workflow_status === 'Sent to Customer' && !frm.doc.customer_response_deadline) {
			const response_deadline = frappe.datetime.add_days(frappe.datetime.nowdate(), 30);
			frm.set_value('customer_response_deadline', response_deadline);
		}
	}
});

// Child table events for commercial options
frappe.ui.form.on('Quotation Item', {
	qty: function(frm, cdt, cdn) {
		calculate_option_totals(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_option_totals(frm, cdt, cdn);
	}
});

function populate_from_technical_proposal(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.populate_customer_proposal_from_technical',
		args: {
			customer_proposal: frm.doc.name,
			technical_proposal: frm.doc.wwtp_technical_proposal
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frm.reload_doc();
				frappe.show_alert(__('Customer proposal populated from technical proposal'));
			} else {
				frappe.msgprint(__('Failed to populate from technical proposal: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function send_to_customer(frm) {
	frappe.prompt([
		{
			label: 'Email Subject',
			fieldname: 'email_subject',
			fieldtype: 'Data',
			default: `WWTP Proposal - ${frm.doc.project_title}`,
			reqd: 1
		},
		{
			label: 'Email Message',
			fieldname: 'email_message',
			fieldtype: 'Text Editor',
			default: `Dear ${frm.doc.customer},\n\nPlease find attached our technical and commercial proposal for your wastewater treatment project.\n\nWe look forward to your feedback.\n\nBest regards,\nWT Operations Team`,
			reqd: 1
		},
		{
			label: 'Include Attachments',
			fieldname: 'include_attachments',
			fieldtype: 'Check',
			default: 1
		}
	], function(values) {
		frappe.call({
			method: 'wt_operations.wt_operations.api.send_customer_proposal_email',
			args: {
				customer_proposal: frm.doc.name,
				email_subject: values.email_subject,
				email_message: values.email_message,
				include_attachments: values.include_attachments
			},
			callback: function(r) {
				if (r.message && r.message.success) {
					frappe.msgprint(__('Proposal sent to customer successfully'));
					frm.set_value('workflow_status', 'Sent to Customer');
					frm.save();
				} else {
					frappe.msgprint(__('Failed to send proposal: ') + (r.message.error || 'Unknown error'));
				}
			}
		});
	}, __('Send Proposal to Customer'), __('Send'));
}

function create_rfp(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.create_rfp_from_customer_proposal',
		args: {
			customer_proposal: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__(`Request for Proposal ${r.message.rfp_name} created successfully`));
				frappe.set_route('Form', 'Request for Proposal', r.message.rfp_name);
			} else {
				frappe.msgprint(__('Failed to create RFP: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function schedule_follow_up(frm) {
	frappe.prompt([
		{
			label: 'Follow-up Date',
			fieldname: 'follow_up_date',
			fieldtype: 'Date',
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), 7),
			reqd: 1
		},
		{
			label: 'Follow-up Type',
			fieldname: 'follow_up_type',
			fieldtype: 'Select',
			options: 'Phone Call\nEmail\nMeeting\nSite Visit',
			default: 'Phone Call',
			reqd: 1
		},
		{
			label: 'Notes',
			fieldname: 'notes',
			fieldtype: 'Small Text'
		}
	], function(values) {
		// Add to follow-up schedule table
		const row = frm.add_child('follow_up_schedule');
		row.follow_up_date = values.follow_up_date;
		row.follow_up_type = values.follow_up_type;
		row.notes = values.notes;
		row.status = 'Scheduled';
		
		frm.refresh_field('follow_up_schedule');
		frm.save();
		
		frappe.show_alert(__('Follow-up scheduled successfully'));
	}, __('Schedule Follow-up'), __('Schedule'));
}

function adjust_deadlines_by_priority(frm) {
	const priority_adjustments = {
		'Urgent': -7,    // 7 days earlier
		'High': -3,      // 3 days earlier
		'Medium': 0,     // No change
		'Low': 7         // 7 days later
	};
	
	const adjustment = priority_adjustments[frm.doc.proposal_priority] || 0;
	
	if (frm.doc.customer_response_deadline) {
		const new_deadline = frappe.datetime.add_days(frm.doc.customer_response_deadline, adjustment);
		frm.set_value('customer_response_deadline', new_deadline);
	}
}

function calculate_option_totals(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	
	if (row.qty && row.rate) {
		row.amount = row.qty * row.rate;
		frm.refresh_field(row.parentfield);
		
		// Calculate table totals
		calculate_table_total(frm, row.parentfield);
	}
}

function calculate_table_total(frm, table_field) {
	let total = 0;
	
	if (frm.doc[table_field]) {
		frm.doc[table_field].forEach(row => {
			if (row.amount) {
				total += row.amount;
			}
		});
	}
	
	// Update total field if it exists
	const total_field = table_field.replace('_table', '_total');
	if (frm.fields_dict[total_field]) {
		frm.set_value(total_field, total);
	}
}

function show_priority_indicator(frm) {
	const priority = frm.doc.proposal_priority;
	let alert_class = 'info';
	let message = '';
	
	switch(priority) {
		case 'Urgent':
			alert_class = 'danger';
			message = 'This is an urgent proposal requiring immediate attention';
			break;
		case 'High':
			alert_class = 'warning';
			message = 'This is a high priority proposal';
			break;
		case 'Medium':
			alert_class = 'info';
			message = 'This is a medium priority proposal';
			break;
		case 'Low':
			alert_class = 'secondary';
			message = 'This is a low priority proposal';
			break;
	}
	
	if (message) {
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-${alert_class}">
				<strong>Priority:</strong> ${message}
			</div>`
		);
	}
}

function check_deadline_status(frm) {
	const deadline = frm.doc.deadline_date || frm.doc.customer_response_deadline;
	if (!deadline) return;
	
	const deadline_date = frappe.datetime.str_to_obj(deadline);
	const today = frappe.datetime.now_date();
	const days_diff = frappe.datetime.get_diff(deadline_date, today);
	
	if (days_diff < 0) {
		// Overdue
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-danger">
				<strong>Overdue:</strong> Customer response is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 3) {
		// Due soon
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> Customer response is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 7) {
		// Due within a week
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> Customer response is due in ${days_diff} days
			</div>`
		);
	}
}