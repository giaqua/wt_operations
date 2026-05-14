// Copyright (c) 2025, WT Operations and contributors
// For license information, please see license.txt

frappe.ui.form.on('WWTP Technical Proposal', {
	refresh: function(frm) {
		// Add custom buttons based on workflow status
		if (frm.doc.workflow_status === 'Approved' && frm.doc.external_sync_status !== 'Synced') {
			frm.add_custom_button(__('Sync to Sales Site'), function() {
				sync_to_sales_site(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.workflow_status === 'Synced to Sales') {
			frm.add_custom_button(__('Create Customer Proposal'), function() {
				create_customer_proposal(frm);
			}, __('Actions'));
		}
		
		// Show deadline warning if approaching
		if (frm.doc.deadline_date) {
			check_deadline_status(frm);
		}
		
		// Show review status indicator
		if (frm.doc.review_status) {
			show_review_status_indicator(frm);
		}
		
		// Auto-populate fields from related documents
		if (frm.doc.__islocal) {
			auto_populate_from_related_docs(frm);
		}
		
		// Calculate total costs
		calculate_total_costs(frm);
		// calculate_total_implementation_time(frm);
	},
	
	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('workflow_status', 'Draft');
			frm.set_value('review_status', 'Pending');
			frm.set_value('proposal_date', frappe.datetime.nowdate());
			frm.set_value('prepared_by', frappe.session.user);
			
			// Set default validity period (60 days)
			const valid_until = frappe.datetime.add_days(frappe.datetime.nowdate(), 60);
			frm.set_value('valid_until', valid_until);
		}
	},
	
	workflow_status: function(frm) {
		// Update review status when workflow status changes
		if (frm.doc.workflow_status === 'Under Review' && frm.doc.review_status === 'Pending') {
			frm.set_value('review_status', 'Under Review');
		}
		
		if (frm.doc.workflow_status === 'Approved') {
			frm.set_value('review_status', 'Approved');
			if (!frm.doc.reviewed_by) {
				frm.set_value('reviewed_by', frappe.session.user);
			}
			if (!frm.doc.review_date) {
				frm.set_value('review_date', frappe.datetime.nowdate());
			}
		}
	},
	
	wwtp_technical_questionnaire: function(frm) {
		// Auto-populate from technical questionnaire
		if (frm.doc.wwtp_technical_questionnaire) {
			populate_from_questionnaire(frm);
		}
	},
	
	site_visit: function(frm) {
		// Auto-populate from site visit
		if (frm.doc.site_visit) {
			populate_from_site_visit(frm);
		}
	},
	
	water_sample: function(frm) {
		// Auto-populate from water sample
		if (frm.doc.water_sample) {
			populate_from_water_sample(frm);
		}
	},
	
	equipment_cost: function(frm) {
		calculate_total_costs(frm);
	},
	
	civil_works_cost: function(frm) {
		calculate_total_costs(frm);
	},
	
	electrical_cost: function(frm) {
		calculate_total_costs(frm);
	},
	
	design_period: function(frm) {
		calculate_total_implementation_time(frm);
	},
	
	procurement_period: function(frm) {
		calculate_total_implementation_time(frm);
	},
	
	construction_period: function(frm) {
		calculate_total_implementation_time(frm);
	},
	
	commissioning_period: function(frm) {
		calculate_total_implementation_time(frm);
	},
	technical_specifications_template: async function(frm) {
		if (frm.doc.technical_specifications_template) {
			let technical_specifications_template =  await frappe.db.get_doc('Technical Specifications Template', frm.doc.technical_specifications_template);
			$.each(technical_specifications_template.technical_specifications, function(index, source_row) {
                let new_row = frm.add_child('technical_specifications_table'); // 'items' is your target child table fieldname
                new_row.specification_type = source_row.specification_type;
                new_row.parameter = source_row.parameter;
                new_row.value = source_row.value;
                new_row.unit = source_row.unit;
				new_row.description = source_row.description;
                // Map other fields as needed
            });
			 frm.refresh_field('technical_specifications_table');
            
		}
	},
	equipment_details_template: async function(frm) {
		if (frm.doc.equipment_details_template) {
			let equipment_details_template =  await frappe.db.get_doc('Equipment Details Template', frm.doc.equipment_details_template);
			$.each(equipment_details_template.equipment_details, function(index, source_row) {
                let new_row = frm.add_child('equipment_details_table'); // 'items' is your target child table fieldname
                new_row.specification_type = source_row.specification_type;
                new_row.equipment_name = source_row.equipment_name;
                new_row.equipment_type = source_row.equipment_type;
                new_row.quantity = source_row.quantity;
				new_row.capacity = source_row.capacity;
				new_row.unit = source_row.unit;
				new_row.power_consumption = source_row.power_consumption;
				new_row.manufacturer = source_row.manufacturer;
				new_row.model = source_row.model;
				new_row.description = source_row.description;
                // Map other fields as needed
            });
			 frm.refresh_field('equipment_details_table');
            
		}
	},
	effluent_quality_parameters_template: async function(frm) {
		if (frm.doc.effluent_quality_parameters_template) {
			let effluent_quality_parameters_template =  await frappe.db.get_doc('Effluent Quality Parameters Template', frm.doc.effluent_quality_parameters_template);
			$.each(effluent_quality_parameters_template.effluent_quality, function(index, source_row) {
                let new_row = frm.add_child('effluent_quality_table'); // 'items' is your target child table fieldname
				new_row.parameter = source_row.parameter;
                new_row.unit = source_row.unit;
                new_row.target_value = source_row.target_value;
                new_row.guaranteed_value = source_row.guaranteed_value;
				new_row.test_method = source_row.test_method;
				new_row.frequency = source_row.frequency;
                // Map other fields as needed
            });
			 frm.refresh_field('effluent_quality_table');
            
		}
	},
	fetch_scope_of_work: async function(frm) {
		await frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: 'Scope Of Work',
				fields: ['name', 'scope_of_work_details']
			},
			callback: function(response) {
				let list = response.message;
				list.forEach(item => {
					console.log(item);
					let new_row = frm.add_child('roles_and_responsibilities_table');
					new_row.scope_of_work = item.name;
				});
				frm.refresh_field('roles_and_responsibilities_table');
			}
		});
	}
});

function sync_to_sales_site(frm) {
	frappe.confirm(
		__('Are you sure you want to sync this Technical Proposal to the sales site?'),
		function() {
			frappe.call({
				method: 'wt_operations.wt_operations.api.sync_technical_proposal_to_sales',
				args: {
					doc_name: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.msgprint(__('Technical Proposal synced successfully'));
						frm.reload_doc();
					} else {
						frappe.msgprint(__('Sync failed: ') + (r.message.error || 'Unknown error'));
					}
				}
			});
		}
	);
}

function create_customer_proposal(frm) {
	frappe.call({
		method: 'wt_operations.wt_operations.api.create_customer_proposal_from_technical',
		args: {
			technical_proposal: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__(`Customer Proposal ${r.message.customer_proposal} created successfully`));
				frappe.set_route('Form', 'Customer Proposal', r.message.customer_proposal);
			} else {
				frappe.msgprint(__('Failed to create Customer Proposal: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function auto_populate_from_related_docs(frm) {
	// Auto-populate from questionnaire if available
	if (frm.doc.wwtp_technical_questionnaire) {
		populate_from_questionnaire(frm);
	}
	
	// Auto-populate from site visit if available
	if (frm.doc.site_visit) {
		populate_from_site_visit(frm);
	}
	
	// Auto-populate from water sample if available
	if (frm.doc.water_sample) {
		populate_from_water_sample(frm);
	}
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
				
				// Populate basic fields
				if (tq.lead && !frm.doc.lead) {
					frm.set_value('lead', tq.lead);
				}
				if (tq.opportunity && !frm.doc.opportunity) {
					frm.set_value('opportunity', tq.opportunity);
				}
				if (tq.wastewater_generator_type && !frm.doc.wastewater_generator_type) {
					frm.set_value('wastewater_generator_type', tq.wastewater_generator_type);
				}
				if (tq.capacity && !frm.doc.design_capacity) {
					frm.set_value('design_capacity', tq.capacity);
				}
				if (tq.daily_flow && !frm.doc.daily_flow) {
					frm.set_value('daily_flow', tq.daily_flow);
				}
				if (tq.operation_hours && !frm.doc.operation_hours) {
					frm.set_value('operation_hours', tq.operation_hours);
				}
				if (tq.average_hourly_flow && !frm.doc.average_hourly_flow) {
					frm.set_value('average_hourly_flow', tq.average_hourly_flow);
				}
				
				// Set project title if not set
				if (!frm.doc.project_title) {
					const title = `${tq.wastewater_generator_type} WWTP - ${tq.capacity} m³/day`;
					frm.set_value('project_title', title);
				}
			}
		}
	});
}

function populate_from_site_visit(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Site Visit',
			name: frm.doc.site_visit
		},
		callback: function(r) {
			if (r.message) {
				const sv = r.message;
				
				// Populate site conditions
				if (sv.site_observations && !frm.doc.site_conditions_summary) {
					frm.set_value('site_conditions_summary', sv.site_observations);
				}
				if (sv.site_accessibility && !frm.doc.site_accessibility_rating) {
					frm.set_value('site_accessibility_rating', sv.site_accessibility);
				}
				if (sv.power_availability && !frm.doc.power_availability_rating) {
					frm.set_value('power_availability_rating', sv.power_availability);
				}
				if (sv.ground_conditions && !frm.doc.ground_conditions_rating) {
					frm.set_value('ground_conditions_rating', sv.ground_conditions);
				}
				if (sv.environmental_impact && !frm.doc.environmental_impact_assessment) {
					frm.set_value('environmental_impact_assessment', sv.environmental_impact);
				}
			}
		}
	});
}

function populate_from_water_sample(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Water Sample',
			name: frm.doc.water_sample
		},
		callback: function(r) {
			if (r.message) {
				const ws = r.message;
				
				// Build influent characteristics from sample data
				let influent_chars = 'Based on water sample analysis:\n';
				if (ws.ph) influent_chars += `- pH: ${ws.ph}\n`;
				if (ws.tss) influent_chars += `- TSS: ${ws.tss} mg/L\n`;
				if (ws.cod) influent_chars += `- COD: ${ws.cod} mg/L\n`;
				if (ws.bod5) influent_chars += `- BOD5: ${ws.bod5} mg/L\n`;
				
				if (!frm.doc.influent_characteristics) {
					frm.set_value('influent_characteristics', influent_chars);
				}
				
				// Set compliance status
				if (ws.compliance_status && !frm.doc.compliance_status) {
					frm.set_value('compliance_status', ws.compliance_status);
				}
			}
		}
	});
}

function calculate_total_costs(frm) {
	const equipment_cost = frm.doc.equipment_cost || 0;
	const civil_works_cost = frm.doc.civil_works_cost || 0;
	const electrical_cost = frm.doc.electrical_cost || 0;
	
	const total = equipment_cost + civil_works_cost + electrical_cost;
	frm.set_value('total_project_cost', total);
}

function calculate_total_implementation_time(frm) {
	const design_period = frm.doc.design_period || 0;
	const procurement_period = frm.doc.procurement_period || 0;
	const construction_period = frm.doc.construction_period || 0;
	const commissioning_period = frm.doc.commissioning_period || 0;
	
	// Assuming some overlap between phases
	const total = Math.max(design_period + procurement_period + construction_period + commissioning_period - 4, 0);
	frm.set_value('total_implementation_time', total);
}

function show_review_status_indicator(frm) {
	const status = frm.doc.review_status;
	let alert_class = 'info';
	let message = '';
	
	switch(status) {
		case 'Approved':
			alert_class = 'success';
			message = 'Technical proposal has been approved';
			break;
		case 'Rejected':
			alert_class = 'danger';
			message = 'Technical proposal has been rejected';
			break;
		case 'Under Review':
			alert_class = 'warning';
			message = 'Technical proposal is under review';
			break;
		case 'Pending':
			alert_class = 'info';
			message = 'Technical proposal is pending review';
			break;
	}
	
	if (message) {
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-${alert_class}">
				<strong>Review Status:</strong> ${message}
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
				<strong>Overdue:</strong> Technical proposal is ${Math.abs(days_diff)} days overdue
			</div>`
		);
	} else if (days_diff <= 1) {
		// Due today or tomorrow
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-warning">
				<strong>Due Soon:</strong> Technical proposal is due in ${days_diff} day(s)
			</div>`
		);
	} else if (days_diff <= 3) {
		// Due within 3 days
		frm.dashboard.set_headline_alert(
			`<div class="alert alert-info">
				<strong>Upcoming Deadline:</strong> Technical proposal is due in ${days_diff} days
			</div>`
		);
	}
}