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
	},
    project: function(frm) {
        filter_units_based_on_project(frm);
    },
    project_unit: function(frm) {
        console.log('Unit changed, fetching PUA record...');
        auto_fetch_pua_record(frm);
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
