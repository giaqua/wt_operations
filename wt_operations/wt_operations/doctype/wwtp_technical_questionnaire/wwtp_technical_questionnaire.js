// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('WWTP Technical Questionnaire', {
	onload: function(frm) {
		// Set flag to track if we've already auto-populated
		frm._auto_populated_scope = false;
	},
	
	refresh: function(frm) {
		// Make form read-only if synced from sales
		if (frm.doc.is_synced_from_sales) {
			frm.set_read_only(true);
			// Show banner indicating synced from sales
			let synced_from = frm.doc.synced_from_site || 'Sales Site';
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-info" style="margin-bottom: 10px;">
					<strong><i class="fa fa-info-circle"></i> Synced from Sales:</strong> 
					This document was synced from ${synced_from} and is read-only. 
					${frm.doc.synced_from_site ? `<br><small>Source Site: ${frm.doc.synced_from_site}</small>` : ''}
				</div>`
			);
		}
		
		// Auto-populate scope of work when creating new TQ (first time only)
		if (frm.is_new() && !frm._auto_populated_scope && (!frm.doc.tq_roles_and_responsibilities || frm.doc.tq_roles_and_responsibilities.length === 0)) {
			frm._auto_populated_scope = true;
			// Use setTimeout to ensure form is fully loaded before populating
			setTimeout(function() {
				populate_roles_from_scope_of_work(frm, true); // true = silent mode for auto-population
			}, 500);
		}
		
		// Add custom buttons based on workflow status (only if not synced from sales)
		if (!frm.doc.is_synced_from_sales) {
			if (frm.doc.workflow_status === 'Submitted' && frm.doc.sync_status !== 'Synced') {
				frm.add_custom_button(__('Sync to Operations Site'), function() {
					sync_to_operations_site(frm);
				}, __('Actions'));
			}
			
			if (frm.doc.workflow_status === 'Synced to Operations' && frm.doc.site_visit_required) {
				frm.add_custom_button(__('Create Site Visit Request'), function() {
					create_site_visit_request(frm);
				}, __('Actions'));
			}
		}
		
		// Add workflow progress indicator
		if (frm.doc.workflow_progress) {
			frm.dashboard.add_progress(__('Workflow Progress'), frm.doc.workflow_progress);
		}
		
		// Show workflow status indicator (if not already showing synced from sales banner)
		if (frm.doc.workflow_status && !frm.doc.is_synced_from_sales) {
			frm.dashboard.set_headline_alert(
				`<div class="row">
					<div class="col-xs-12">
						<span class="indicator ${get_status_color(frm.doc.workflow_status)}">
							${frm.doc.workflow_status}
						</span>
					</div>
				</div>`
			);
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date) {
			check_deadline_status(frm);
		}
		if (frm.doc.local_site_visit_request) {
			frm.add_custom_button(__('Open Local SVR'), function() {
				frappe.set_route('Form', 'Site Visit Request', frm.doc.local_site_visit_request);
			});
		}
		
		// Add button to populate roles from Scope of Work (only if not already populated and not synced from sales)
		if (!frm.doc.is_synced_from_sales && (!frm.doc.tq_roles_and_responsibilities || frm.doc.tq_roles_and_responsibilities.length === 0)) {
			frm.add_custom_button(__('Populate All Scope of Work'), function() {
				populate_roles_from_scope_of_work(frm);
			}, __('Actions'));
		}
	},
	
	workflow_status: function(frm) {
		// Update workflow progress when status changes
		update_workflow_progress(frm);
	},
	
	site_visit_required: function(frm) {
		// Show/hide site visit related fields
		frm.toggle_display('assigned_site_manager', frm.doc.site_visit_required);
		
		// Auto-create Site Visit Request if checked and TQ is submitted
		if (frm.doc.site_visit_required && frm.doc.docstatus === 1 && !frm.doc.local_site_visit_request) {
			frappe.confirm(
				__('Do you want to create a Site Visit Request for this Technical Questionnaire?'),
				function() {
					// Yes - Create SVR
					create_site_visit_request(frm);
				},
				function() {
					// No - Just uncheck if user cancels
					frm.set_value('site_visit_required', 0);
				}
			);
		} else if (frm.doc.site_visit_required && frm.doc.docstatus === 0 && !frm.doc.local_site_visit_request) {
			// If not submitted yet, show a message but don't uncheck
			// User can keep it checked and submit later
			frappe.show_alert({
				message: __('Please submit the Technical Questionnaire first to create a Site Visit Request. You can keep this checked and submit later.'),
				indicator: 'orange'
			}, 5);
		}
	},
	
	sample_collection_required: function(frm) {
		// Future: Add sample collection related logic
	}
});

function sync_to_operations_site(frm) {
	frappe.confirm(
		__('Are you sure you want to sync this Technical Questionnaire to the operations site?'),
		function() {
			frappe.call({
				method: 'wt_operations.wt_operations.api.sync_technical_questionnaire_to_operations',
				args: {
					doc_name: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.msgprint(__('Technical Questionnaire synced successfully'));
						frm.reload_doc();
					} else {
						frappe.msgprint(__('Sync failed: ') + (r.message.error || 'Unknown error'));
					}
				}
			});
		}
	);
}

function create_site_visit_request(frm) {
	frappe.call({
		method: 'create_site_visit_request',
		doc: frm.doc,
		args: {
			external_site_settings: null
		},
		freeze: true,
		freeze_message: __('Creating Site Visit Request...'),
		callback: function(r) {
			if (r.message) {
				frappe.show_alert({
					message: __('Site Visit Request created: {0}', [r.message.local_svr]),
					indicator: 'green'
				});
				frappe.set_route('Form', 'Site Visit Request', r.message.local_svr);
				frm.reload_doc();
			}
		}
	});
}

function populate_roles_from_scope_of_work(frm, silent_mode = false) {
	frappe.call({
		method: 'populate_roles_from_scope_of_work',
		doc: frm.doc,
		freeze: !silent_mode, // Don't show freeze indicator in silent mode
		freeze_message: __('Populating roles from Scope of Work...'),
		callback: function(r) {
			if (r.message) {
				if (!silent_mode) {
					frappe.msgprint({
						title: __('Scope of Work Populated'),
						message: __(r.message.message),
						indicator: 'blue'
					});
				} else {
					// In silent mode, just show a subtle alert
					frappe.show_alert({
						message: __('{0} Scope of Work entries loaded', [r.message.added_count || 0]),
						indicator: 'blue'
					}, 3);
				}
				frm.refresh_field('tq_roles_and_responsibilities');
			}
		},
		error: function(r) {
			if (!silent_mode) {
				frappe.msgprint({
					title: __('Error'),
					message: r.message || __('Failed to populate roles from Scope of Work'),
					indicator: 'red'
				});
			}
		}
	});
}

function get_status_color(status) {
	const status_colors = {
		'Draft': 'blue',
		'Submitted': 'orange', 
		'Synced to Operations': 'green'
	};
	return status_colors[status] || 'grey';
}

function update_workflow_progress(frm) {
	const progress_map = {
		'Draft': 0,
		'Submitted': 50,
		'Synced to Operations': 100
	};
	
	const progress = progress_map[frm.doc.workflow_status] || 0;
	frm.set_value('workflow_progress', progress);
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
				<strong>Overdue:</strong> This document is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> This document is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 3) {
		// Due within 3 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> This document is due in ${days_diff} days
			</div>`
		);
	}
}


frappe.ui.form.on("WWTP Technical Questionnaire", {
	refresh(frm) {
		// Ensure the table has the correct number of rows when form loads
		if (frm.doc.number_of_streams && frm.doc.number_of_streams > 0) {
			update_influent_stream_table(frm);
		}
	},

	number_of_streams(frm) {
		// Update the influent stream table when number_of_streams changes
		if (frm.doc.number_of_streams && frm.doc.number_of_streams > 0) {
			update_influent_stream_table(frm);
		} else {
			// Clear the table if number_of_streams is 0 or empty
			frm.clear_table("tq_influent_stream");
			frm.refresh_field("tq_influent_stream");
		}
	},

	before_save(frm) {
		// Ensure the table has the correct number of rows before saving
		if (frm.doc.number_of_streams && frm.doc.number_of_streams > 0) {
			update_influent_stream_table(frm);
		}
	}
});

function update_influent_stream_table(frm) {
	let current_rows = frm.doc.tq_influent_stream ? frm.doc.tq_influent_stream.length : 0;
	let required_rows = frm.doc.number_of_streams;
	
	// If we need more rows, add them
	if (required_rows > current_rows) {
		for (let i = current_rows; i < required_rows; i++) {
			let new_row = frm.add_child("tq_influent_stream");
			new_row.parameter = `Stream ${i + 1}`;
		}
	}
	// If we have too many rows, remove the excess
	else if (required_rows < current_rows) {
		// Remove rows from the end
		for (let i = current_rows - 1; i >= required_rows; i--) {
			frm.get_field("tq_influent_stream").grid.grid_rows[i].remove();
		}
	}
	
	// Update parameter names for all rows
	if (frm.doc.tq_influent_stream) {
		frm.doc.tq_influent_stream.forEach((row, index) => {
			row.parameter = `Stream ${index + 1}`;
		});
	}
	
	frm.refresh_field("tq_influent_stream");
}

// --- Effluent Type Auto-population Event Handler & Refresh Button ---
frappe.ui.form.on('WWTP Technical Questionnaire', {
    please_pick_the_target_effluent_type(frm) {
        if (frm.doc.please_pick_the_target_effluent_type) {
            frm.call('populate_effluent_parameters').then((r) => {
                if (r.message && Object.keys(r.message).length > 0) {
                    frm.set_value('ph_eff', r.message.ph_eff);
                    frm.set_value('tss_eff', r.message.tss_eff);
                    frm.set_value('bod5_eff', r.message.bod5_eff);
                    frm.set_value('cod_eff', r.message.cod_eff);
                    frm.set_value('turbidity_eff', r.message.turbidity_eff);
                    frm.set_value('oil_grease_eff', r.message.oil_grease_eff);
                    frm.set_value('tds_eff', r.message.tds_eff);
                    frm.set_value('free_chlorine', r.message.free_chlorine);
                    frm.set_value('ecoli', r.message.ecoli);
                    frm.set_value('wormies', r.message.wormies);
                    frappe.msgprint({
                        message: __('Effluent parameters populated based on {0}', [frm.doc.please_pick_the_target_effluent_type]),
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    refresh(frm) {
        // Add refresh button if effluent type exists and doc is not new
        if (frm.doc.please_pick_the_target_effluent_type && !frm.is_new()) {
            frm.add_custom_button(__('Refresh Effluent Parameters'), function() {
                frm.trigger('please_pick_the_target_effluent_type');
            }).addClass('btn-primary');
        }
    }
});