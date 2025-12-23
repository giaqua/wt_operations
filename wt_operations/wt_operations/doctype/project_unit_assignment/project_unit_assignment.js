
// To check duplicate assignments for the same unit within the specified date range
frappe.ui.form.on('Project Unit Assignment', {
    unit: function(frm) {
        frm.trigger('check_for_duplicates');
    },
    assignment_date: function(frm) {
        frm.trigger('check_for_duplicates');
    },
    assignment_expected_end_date: function(frm) {
        frm.trigger('check_for_duplicates');
    },
    check_for_duplicates: function(frm) {
        if (frm.doc.unit && frm.doc.assignment_date && frm.doc.assignment_expected_end_date) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Project Unit Assignment',
                    filters: [
                        ['unit', '=', frm.doc.unit],
                        ['docstatus', '<', 2],
                        ['name', '!=', frm.doc.name],
                        ['assignment_date', '<=', frm.doc.assignment_expected_end_date],
                        ['assignment_expected_end_date', '>=', frm.doc.assignment_date]
                    ],
                    fields: ['name']
                },
                callback: function(response) {
                    if (response.message.length > 0) {
                        frappe.msgprint(__('There is already an assignment for this unit during the selected timeframe.'));
                    }
                }
            });
        }
    }
});


// To validate the assignment date and expected end date
frappe.ui.form.on('Project Unit Assignment', {
    assignment_date: function(frm) {
        validate_dates(frm);
    },
    assignment_expected_end_date: function(frm) {
        validate_dates(frm);
    }
});

function validate_dates(frm) {
    if (frm.doc.assignment_date && frm.doc.assignment_expected_end_date) {
        if (frm.doc.assignment_expected_end_date <= frm.doc.assignment_date) {
            frappe.msgprint(__('Assignment Expected End Date must be after the Assignment Date'));
            frm.set_value('assignment_expected_end_date', null);
        }
    }
}

//To check for duplicate treatment parameters in the Treatment Parameters Table
frappe.ui.form.on('Project Unit Assignment', {
    refresh: function(frm) {
        frm.fields_dict['treatment_parameters_template_table'].grid.wrapper.on('change', 'input[data-fieldname="treatment_parameter"]', function() {
            check_for_duplicate_parameters(frm);
        });
    }
});

function check_for_duplicate_parameters(frm) {
    const parameters = [];
    let has_duplicate = false;

    (frm.doc.treatment_parameters_template_table || []).forEach(row => {
        if (parameters.includes(row.treatment_parameter)) {
            has_duplicate = true;
        } else if (row.treatment_parameter) {
            parameters.push(row.treatment_parameter);
        }
    });

    if (has_duplicate) {
        frappe.msgprint(__('Duplicate parameters found in Treatment Parameters Table.'));
    }
}



// To set filters for the Treatment Parameters, Influent Parameters, and Effluent Parameters fields
// This ensures that only relevant parameters are selectable in each table.

frappe.ui.form.on('Project Unit Assignment', {
    onload: function(frm) {
        set_pua_parameter_filters(frm);
    }
});

function set_pua_parameter_filters(frm) {
    // Treatment Parameters Filter
    frm.fields_dict.treatment_parameters_template_table.grid.get_field('treatment_parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Treatment'
            }
        };
    };

    // Influent Parameters Filter
    frm.fields_dict.influent_parameters_template_table.grid.get_field('parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Physical'
            }
        };
    };

    // Effluent Parameters Filter
    frm.fields_dict.effluent_parameters_template_table.grid.get_field('parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Physical'
            }
        };
    };
}