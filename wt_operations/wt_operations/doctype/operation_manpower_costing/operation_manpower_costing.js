// Copyright (c) 2026, Takamol and contributors
// For license information, please see license.txt

frappe.ui.form.on("Operation Manpower Costing", {
	refresh(frm) {
        frm.set_query('project_unit_assignment', function() {
            return {
                filters: {
                    project: frm.doc.project,
                    unit: ['like', `%${frm.doc.project_unit}%`],
                }
            };
        });

        if (frm.doc.docstatus !== 0) return;
        frm.add_custom_button(__("Spare Parts & Maintenance"), () => {
            fetch_cost_items(frm, "spare_parts_and_maintenance_cost_details");
        }, __("Fetch Costs"));

        frm.add_custom_button(__("(Other Costs)"), () => {
            fetch_cost_items(frm, "housing_and_transportation_cost_details");
        }, __("Fetch Costs"));

	},
    project: function(frm) {
        filter_units_based_on_project(frm);
    },
    project_unit: function(frm) {
        console.log('Unit changed, fetching PUA record...');
        auto_fetch_pua_record(frm);
    },
    update_costs_on_reports: function(frm) {
        console.log("ddddddddddddddd");
        if (frm.doc.docstatus === 1 && frm.doc.daily_operation_report_references.length > 0) {
            console.log("sssssssss");
            update_costs_on_reports(frm);
            // show_progress_dialog(frm);
        }
    }
});

function filter_units_based_on_project(frm) {
    if (frm.doc.project) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Project Unit Assignment',
                filters: {
                    project: frm.doc.project
                },
                fields: ['unit'],
                limit_page_length: 0
            },
            callback: function(response) {
                let units = $.map(response.message || [], d => d.unit);
                frm.set_query('unit', function() {
                    return {
                        filters: {
                            name: ['in', units]
                        }
                    };
                });
            }
        });
    }
}

function auto_fetch_pua_record(frm) {
    console.log('Auto-fetching PUA record for project:', frm.doc.project, 'and unit:', frm.doc.project_unit);
    if (frm.doc.project && frm.doc.unit) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Project Unit Assignment',
                filters: [
                    ['project', '=', frm.doc.project],
                    ['unit', '=', frm.doc.project_unit],
                    // ['assignment_date', '<=', frm.doc.date],
                    // ['assignment_expected_end_date', '>=', frm.doc.date]
                ],
                fields: ['name'],
                order_by: 'assignment_date desc', // Order by date to ensure correct fetching
                limit_page_length: 1 // Limit to the most relevant record
            },
            callback: function(response) {
                if (response.message && response.message.length > 0) {
                    console.log("Found PUA record:", response.message[0].name);
                    
                    frm.set_value('project_unit_assignment', response.message[0].name);
                } else {
                    console.log("No active PUA record found for the selected unit and date.");
                    frm.set_value('project_unit_assignment', null);
                    frappe.msgprint(__('No active assignment found for the selected unit and date.'));
                }
            }
        });
    }
}


function update_costs_on_reports(frm) {
    frappe.call({
        method: "update_costs_on_reports", // Update this path
        doc: frm.doc, 
        callback: function(response) {
            console.log("Backend process completed with response:", response);
            if (response.message) {
                if (response.message.status === "success") {
                    update_progress_bar(100, response.message.message);
                    dialog.$wrapper.find('#status-message').html(`
                        <div class="alert alert-success" style="margin-top: 10px;">
                            ${response.message.message}
                        </div>
                    `);
                } else {
                    dialog.$wrapper.find('#status-message').html(`
                        <div class="alert alert-danger" style="margin-top: 10px;">
                            Error: ${response.message.message}
                        </div>
                    `);
                }
            }
            
            // Refresh the form to show updated data
            frm.refresh();
            
            // Clean up realtime listener
            frappe.realtime.off("progress_update");
        },
        error: function(error) {
            dialog.$wrapper.find('#status-message').html(`
                <div class="alert alert-danger" style="margin-top: 10px;">
                    Error: ${error.message || 'An error occurred'}
                </div>
            `);
            
            // Clean up realtime listener
            frappe.realtime.off("progress_update");
        }
    });
}

function show_progress_dialog(frm) {
    // Create dialog with progress bar
    let dialog = new frappe.ui.Dialog({
        title: __('Processing Data'),
        fields: [
            {
                fieldname: 'progress_html',
                fieldtype: 'HTML',
                label: __('Progress'),
                options: `
                    <div style="padding: 10px;">
                        <div style="margin-bottom: 10px;">
                            <div class="progress" style="margin-bottom: 0;">
                                <div class="progress-bar progress-bar-striped active" 
                                     role="progressbar" 
                                     style="width: 0%;">
                                    0%
                                </div>
                            </div>
                        </div>
                        <div id="progress-message" style="color: #666; text-align: center;">
                            Initializing...
                        </div>
                    </div>
                `
            },
            {
                fieldname: 'status',
                fieldtype: 'HTML',
                options: '<div id="status-message" style="padding: 10px;"></div>'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
    
    // Start the backend process
    start_backend_process(frm, dialog);
}

function start_backend_process(frm, dialog) {
    // Listen for progress updates from backend
    frappe.realtime.on("progress_update", (data) => {
        update_progress_bar(data.progress, data.message);
    });
    
    // Function to update progress bar
    function update_progress_bar(percentage, message) {
        const progressBar = dialog.$wrapper.find('.progress-bar');
        const progressValue = Math.round(percentage);
        
        progressBar.css('width', percentage + '%');
        progressBar.text(progressValue + '%');
        dialog.$wrapper.find('#progress-message').html(message);
        
        // Add active animation while processing
        if (percentage < 100) {
            progressBar.addClass('active progress-bar-striped');
        } else {
            progressBar.removeClass('active progress-bar-striped');
        }
    }
    
    // Call the backend function
    frappe.call({
        method: "update_costs_on_reports", // Update this path
        doc: frm.doc, 
        callback: function(response) {
            console.log("Backend process completed with response:", response);
            if (response.message) {
                if (response.message.status === "success") {
                    update_progress_bar(100, response.message.message);
                    dialog.$wrapper.find('#status-message').html(`
                        <div class="alert alert-success" style="margin-top: 10px;">
                            ${response.message.message}
                        </div>
                    `);
                } else {
                    dialog.$wrapper.find('#status-message').html(`
                        <div class="alert alert-danger" style="margin-top: 10px;">
                            Error: ${response.message.message}
                        </div>
                    `);
                }
            }
            
            // Refresh the form to show updated data
            frm.refresh();
            
            // Clean up realtime listener
            frappe.realtime.off("progress_update");
        },
        error: function(error) {
            dialog.$wrapper.find('#status-message').html(`
                <div class="alert alert-danger" style="margin-top: 10px;">
                    Error: ${error.message || 'An error occurred'}
                </div>
            `);
            
            // Clean up realtime listener
            frappe.realtime.off("progress_update");
        }
    });
}

// Add to Operation Manpower Costing client script (or the doctype's .js file)

// Map each child table to its Operation Cost Type.
// Add more tables here (e.g. housing) using the exact Operation Cost Type name.
const COST_TABLES = {
    spare_parts_and_maintenance_cost_details: "Spare parts & maintenance Costs",
    housing_and_transportation_cost_details: "Other Costs",
};


function fetch_cost_items(frm, table_field) {
    if (!frm.doc.project || !frm.doc.start_date || !frm.doc.end_date) {
        frappe.msgprint(__("Please set Project, Start Date and End Date first."));
        return;
    }

    frappe.call({
        method: "wt_operations.wt_operations.doctype.operation_manpower_costing.operation_manpower_costing.fetch_cost_items",
        args: {
            operation_cost_type: COST_TABLES[table_field],
            project: frm.doc.project,
            start_date: frm.doc.start_date,
            end_date: frm.doc.end_date,
            company: frm.doc.company || null, // remove if the doctype has no company field
        },
        freeze: true,
        freeze_message: __("Fetching amounts from GL..."),
        callback(r) {
            if (!r.message) return;
            const { rows, skipped } = r.message;

            frm.clear_table(table_field);
            rows.forEach((row) => {
                const child = frm.add_child(table_field);
                child.cost_item = row.cost_item;
                child.amount = row.amount;
            });
            frm.refresh_field(table_field);

            update_totals(frm, table_field);

            let msg = __("{0} item(s) loaded.", [rows.length]);
            if (skipped.length) {
                msg += "<br><br><b>" + __("Skipped:") + "</b><ul>" +
                    skipped.map((s) => `<li>${s.item} — ${s.reason}</li>`).join("") + "</ul>";
            }
            frappe.msgprint({ title: __("Fetch Costs"), message: msg, indicator: skipped.length ? "orange" : "green" });
        },
    });
}

function update_totals(frm, table_field) {
    const total = (frm.doc[table_field] || []).reduce((s, d) => s + flt(d.amount), 0);
    const volume = flt(frm.doc.waste_water_treated_volume);
    const per_m3 = volume ? total / volume : 0;

    if (table_field === "spare_parts_and_maintenance_cost_details") {
        frm.set_value("spare_parts_and_maintenance_total", total);
        frm.set_value("spare_parts_and_maintenance_cost_per_m3", per_m3);
    } else if (table_field === "housing_and_transportation_cost_details") {
        frm.set_value("housing_and_transportation_cost", total);
        frm.set_value("housing_and_transportation_cost_per_m3", per_m3);
    }
}