// Copyright (c) 2025, Takamol and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Daily Operation Report", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Tank Level Table', {
    end_of_shift: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        calculate_volume_end_of_shift(child, frm, cdt, cdn);
    },
    volume_m3: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        calculate_volume_end_of_shift(child, frm, cdt, cdn);
    }
});

function calculate_volume_end_of_shift(child, frm, cdt, cdn) {
    if (child.end_of_shift && child.volume_m3) {
        frappe.model.set_value(cdt, cdn, 'volume_end_of_shift', child.end_of_shift * child.volume_m3);
    } else {
        frappe.model.set_value(cdt, cdn, 'volume_end_of_shift', 0);
    }
}
// TANK LEVEL TABLE calculation (from previous answer)
frappe.ui.form.on('Tank Level Table', {
    end_of_shift: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        calculate_volume_end_of_shift(child, frm, cdt, cdn);
    },
    volume_m3: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        calculate_volume_end_of_shift(child, frm, cdt, cdn);
    }
});

function calculate_volume_end_of_shift(child, frm, cdt, cdn) {
    if (child.end_of_shift && child.volume_m3) {
        frappe.model.set_value(cdt, cdn, 'volume_end_of_shift', child.end_of_shift * child.volume_m3);
    } else {
        frappe.model.set_value(cdt, cdn, 'volume_end_of_shift', 0);
    }
}



// ================= Dilution Table =====================
frappe.ui.form.on('Chemical Dilution Table', {
    quantity_of_chemical: function (frm, cdt, cdn) {
        calculate_dilution_rate(frm, cdt, cdn);
        update_chemical_usage_table(frm);
    },
    volume_of_water: function (frm, cdt, cdn) {
        calculate_dilution_rate(frm, cdt, cdn);
        update_chemical_usage_table(frm);
    }
});

function calculate_dilution_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    let chemical_qty = parseFloat(row.quantity_of_chemical) || 0;
    let water_volume = parseFloat(row.volume_of_water) || 0;

    let dilution_rate = (chemical_qty + water_volume)
        ? (chemical_qty / (chemical_qty + water_volume))
        : 0;

    frappe.model.set_value(cdt, cdn, 'dilution_rate', dilution_rate);
}

// ================= Usage Table ========================
frappe.ui.form.on('Chemical Usage Table', {
    volume_consumed_l: function (frm, cdt, cdn) {
        calculate_chemical_quantity_used(frm, cdt, cdn);
    },
    chemical: function (frm, cdt, cdn) {
        calculate_chemical_quantity_used(frm, cdt, cdn);
    }
});

function calculate_chemical_quantity_used(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    let chemical_name = (row.chemical || "").trim().toLowerCase();
    let volume_consumed = parseFloat(row.volume_consumed_l) || 0;  // ✅ correct fieldname

    // Look for matching chemical in the dilution table
    let dilution_row = (frm.doc.chemical_dilution_table || []).find(d => {
        return (d.chemical || "").trim().toLowerCase() === chemical_name;
    });

    let dilution_rate = dilution_row ? parseFloat(dilution_row.dilution_rate) || 0 : 0;
    let chemical_used = volume_consumed * dilution_rate;

    // 🔍 Console logging for testing
    console.log(`Chemical: ${row.chemical}, Volume: ${volume_consumed}, Rate: ${dilution_rate}, Used: ${chemical_used}`);

    // ✅ Update correct field
    frappe.model.set_value(cdt, cdn, 'chemical_quantity_used_kg', chemical_used);
}

// ============== Update All Chemical Usage Rows ==============
function update_chemical_usage_table(frm) {
    (frm.doc.chemical_usage_table || []).forEach(row => {
        calculate_chemical_quantity_used(frm, row.doctype, row.name);
    });
}


// Daily Operation Report form script to handle project and unit selection,
// auto-fetching of Project Unit Assignment records, and populating relevant tables


frappe.ui.form.on('Daily Operation Report', {
    // Triggered when project selection is changed
    project: function(frm) {
        filter_units_based_on_project(frm);
    },
    // Triggered when unit selection is changed
    unit: function(frm) {
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
    if (frm.doc.project && frm.doc.unit) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Project Unit Assignment',
                filters: [
                    ['project', '=', frm.doc.project],
                    ['unit', '=', frm.doc.unit],
                    ['assignment_date', '<=', frm.doc.date],
                    ['assignment_expected_end_date', '>=', frm.doc.date]
                ],
                fields: ['name'],
                order_by: 'assignment_date desc', // Order by date to ensure correct fetching
                limit_page_length: 1 // Limit to the most relevant record
            },
            callback: function(response) {
                if (response.message && response.message.length > 0) {
                    frm.set_value('unit_assignment_record', response.message[0].name);
                } else {
                    frm.set_value('unit_assignment_record', null);
                    frappe.msgprint(__('No active assignment found for the selected unit and date.'));
                }
            }
        });
    }
}




// Triggered when the unit assignment record is selected or changed
// This will fetch the PUA data and populate the relevant tables

frappe.ui.form.on('Daily Operation Report', {
    unit_assignment_record: function(frm) { 
        fetch_and_populate_pua_data(frm);
    },
    clear_all_tables: function(frm) {
        if (frm.doc.is_operational == 0) {
            frm.clear_table('tank_level_table');
            frm.clear_table('treatment_parameters_table');
            frm.clear_table('chemical_dilution_table');
            frm.clear_table('chemical_usage_table');
            frm.clear_table('influent_parameters_table');
            frm.clear_table('effluent_parameters_table');
            frm.refresh_field('tank_level_table');
            frm.refresh_field('treatment_parameters_table');
            frm.refresh_field('chemical_dilution_table');
            frm.refresh_field('chemical_usage_table');
            frm.refresh_field('influent_parameters_table');
            frm.refresh_field('effluent_parameters_table');
        }
    }
});

function fetch_and_populate_pua_data(frm) {
    if (frm.doc.unit_assignment_record) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Project Unit Assignment',
                name: frm.doc.unit_assignment_record
            },
            callback: function(response) {
                if (response.message) {
                    const pua = response.message;

                    // Function to check duplicates by field value
                    function isRowExists(table, field, value) {
                        return (table || []).some(r => r[field] === value);
                    }

                    // TANK LEVEL TABLE
                    (pua.tank_level_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.tank_level_table.some(row =>
                            row.tank_type === pua_row.tank_type
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('tank_level_table');
                            dor_row.tank_type = pua_row.tank_type;
                            dor_row.uom = pua_row.uom;
                            dor_row.volume_m3 = pua_row.volume_m3;
                        }
                    });
                    frm.refresh_field('tank_level_table');

                    // TREATMENT PARAMETERS TABLE
                    (pua.treatment_parameters_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.treatment_parameters_table.some(row =>
                            row.treatment_parameter === pua_row.treatment_parameter
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('treatment_parameters_table');
                            dor_row.treatment_parameter = pua_row.treatment_parameter;
                            dor_row.uom = pua_row.uom;
                            dor_row.target = pua_row.target;
                        }
                    });
                    frm.refresh_field('treatment_parameters_table');

                    // CHEMICAL DILUTION TABLE
                    (pua.chemical_dilution_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.chemical_dilution_table.some(row =>
                            row.chemical === pua_row.chemical
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('chemical_dilution_table');
                            dor_row.chemical = pua_row.chemical;
                            dor_row.uom = pua_row.uom;
                        }
                    });
                    frm.refresh_field('chemical_dilution_table');

                    // CHEMICAL USAGE TABLE
                    (pua.chemical_usage_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.chemical_usage_table.some(row =>
                            row.chemical === pua_row.chemical
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('chemical_usage_table');
                            dor_row.chemical = pua_row.chemical;
                            dor_row.uom = pua_row.uom;
                        }
                    });
                    frm.refresh_field('chemical_usage_table');

                    // INFLUENT PARAMETERS TABLE
                    (pua.influent_parameters_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.influent_parameters_table.some(row =>
                            row.parameter === pua_row.parameter
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('influent_parameters_table');
                            dor_row.parameter = pua_row.parameter;
                            dor_row.limit = pua_row.limit;
                        }
                    });
                    frm.refresh_field('influent_parameters_table');

                    // EFFLUENT PARAMETERS TABLE
                    (pua.effluent_parameters_template_table || []).forEach(pua_row => {
                        const exists = frm.doc.effluent_parameters_table.some(row =>
                            row.parameter === pua_row.parameter
                        );
                        if (!exists) {
                            let dor_row = frm.add_child('effluent_parameters_table');
                            dor_row.parameter = pua_row.parameter;
                            dor_row.limit = pua_row.limit;
                        }
                    });
                    frm.refresh_field('effluent_parameters_table');
                }
            }
        });
    }
}











// Daily Operation Report form script to handle calculations in Treatment Parameters Table
// This script will calculate average flow rate and energy consumption based on the values in the table


frappe.ui.form.on('Daily Operation Report', {
    // Trigger recalculation on table change or form load
    treatment_parameters_table_on_form_rendered: function(frm) {
        set_calculations(frm);
    },
    treatment_parameters_table_add: function(frm) {
        set_calculations(frm);
    },
    treatment_parameters_table_remove: function(frm) {
        set_calculations(frm);
    },
    // refresh: function(frm) {
    //     set_calculations(frm);
    // }
});

// Helper function that does the calculations
function set_calculations(frm) {
    let treated_volume = null;
    let running_hours = null;
    let energy_consumed = null;

    // Loop through the child table rows
    (frm.doc.treatment_parameters_table || []).forEach(function(row) {
        let param = (row['treatment_parameter'] || '').trim().toLowerCase();
        if(param === 'waste water treated volume') {
            treated_volume = parseFloat(row['actual']) || 0;
        }
        if(param === 'running hours') {
            running_hours = parseFloat(row['actual']) || 0;
        }
        if(param === 'energy consumed') {
            energy_consumed = parseFloat(row['actual']) || 0;
        }
    });

    // Calculate average flow rate
    let average_flow_rate = (treated_volume !== null && running_hours) ? (treated_volume / running_hours) : 0;
    frm.set_value('average_flow_rate', average_flow_rate);

    // Calculate energy consumption
    let energy_consumption = (treated_volume !== null) ? (energy_consumed / treated_volume) : 0;
    frm.set_value('energy_consumtion', energy_consumption);
}

frappe.ui.form.on('Treatment parameters table', {
    actual: function(frm, cdt, cdn) {
        set_calculations(frm);
    },
    treatment_parameter: function(frm, cdt, cdn) {
        set_calculations(frm);
    }
});





// Filter Project Unit Assignment based on selected project and unit
// This will ensure that only relevant assignments are shown in the dropdown
frappe.ui.form.on('Daily Operation Report', {
    onload: function(frm) {
        set_pua_filter(frm);
    },
    project: function(frm) {
        set_pua_filter(frm);
    },
    unit: function(frm) {
        set_pua_filter(frm);
    }
});

function set_pua_filter(frm) {
    if (frm.doc.project && frm.doc.unit) {
        frm.set_query('unit_assignment_record', function() {
            return {
                filters: {
                    project: frm.doc.project,
                    unit: frm.doc.unit
                }
            };
        });
    }
}



// // Validate comments in Treatment Parameters Table when submitting the form
// // // This will ensure that comments are provided when Actual does not match Target



frappe.ui.form.on('Daily Operation Report', {
    on_submit: function(frm) {
        validate_comments(frm);
    },
    refresh: function(frm) {
        update_comment_field_styles(frm);
    }
});

// Triggered when fields are changed in child table
frappe.ui.form.on('Treatment parameters table', {
    actual: function(frm, cdt, cdn) {
        update_comment_style(frm, cdt, cdn);
    },
    target: function(frm, cdt, cdn) {
        update_comment_style(frm, cdt, cdn);
    },
    comments: function(frm, cdt, cdn) {
        update_comment_style(frm, cdt, cdn);
    }
});

// Validation on submit
function validate_comments(frm) {
    (frm.doc.treatment_parameters_table || []).forEach(row => {
        if ((row.actual < row.target) && !row.comments) {
            console.log(row.actual, row.target);
            
            // if(row.actual <= row.target){
                frappe.throw(__('Comments are required when Actual value does not match Target for treatment parameter: {0}', [row.treatment_parameter]));
            // }
        }
    });
}

// Updates all rows on form refresh
function update_comment_field_styles(frm) {
    (frm.doc.treatment_parameters_table || []).forEach(row => {
        update_comment_style(frm, row.doctype, row.name);
    });
}

// Style update per row + instant message
function update_comment_style(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let grid = frm.fields_dict["treatment_parameters_table"].grid;
    let grid_row = grid.grid_rows_by_docname[cdn];

    if (!grid_row) return;

    let $cell = $(grid_row.columns["comments"]);
    let $input = $cell.find("textarea");
    const requiredText = "⚠ Required when Actual ≠ Target";

    if (row.actual <row.target && !row.comments) {
        // Red background and placeholder
        $cell.css("background-color", "#ffe6e6");
        if ($input.length && !$input.attr("placeholder")) {
            $input.attr("placeholder", requiredText);
        }

        // Show warning only once
        if (!row._notified) {
            frappe.msgprint({
                message: __("Actual value does not match Target. Comment is required."),
                indicator: 'orange'
            });
            row._notified = true; // prevent repeat messages
        }

    } else {
        $cell.css("background-color", "");
        if ($input.length && $input.attr("placeholder") === requiredText) {
            $input.attr("placeholder", "");
        }

        row._notified = false; // reset flag so it can notify again later if condition changes
    }
}



















// Daily Operation Report form script to apply filters on Treatment Parameters, Influent Parameters, and Effluent Parameters tables
// This script will ensure that only relevant parameters are shown in the dropdowns based on their type

frappe.ui.form.on('Daily Operation Report', {
    onload: function(frm) {
        apply_parameter_filters(frm);
    }
});

function apply_parameter_filters(frm) {
    // Filter for Treatment Parameters Table
    frm.fields_dict.treatment_parameters_table.grid.get_field('treatment_parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Treatment'
            }
        };
    };

    // Filter for Influent Parameters Table
    frm.fields_dict.influent_parameters_table.grid.get_field('parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Physical'
            }
        };
    };

    // Filter for Effluent Parameters Table
    frm.fields_dict.effluent_parameters_table.grid.get_field('parameter').get_query = function(doc, cdt, cdn) {
        return {
            filters: {
                parameter_type: 'Physical'
            }
        };
    };
}


// Daily Operation Report form script to handle warnings when Actual Value exceeds Limit in Influent and Effluent Parameters tables
// This script will show a warning message if the actual value exceeds the limit for any parameter
// It will also prompt the user to add a comment for clarity

frappe.ui.form.on('Daily Operation Report', {
    refresh: function(frm) {
        
    }
});

function check_parameter_warning(frm, cdt, cdn, table_field) {
    let row = locals[cdt][cdn];
    if (row.actual_value && row.limit && row.actual_value > row.limit) {
        frappe.msgprint({
            title: __('Warning'),
            message: __('Actual Value ({0}) exceeds Limit ({1}) for parameter: {2}. Please add a comment.', [row.actual_value, row.limit, row.parameter]),
            indicator: 'orange'
        });
    }
}

frappe.ui.form.on('Influent Parameters Table', {
    actual_value: function(frm, cdt, cdn) {
        check_parameter_warning(frm, cdt, cdn, 'influent_parameters_table');
    }
});

frappe.ui.form.on('Effluent Parameters Table', {
    actual_value: function(frm, cdt, cdn) {
        check_parameter_warning(frm, cdt, cdn, 'effluent_parameters_table');
    }
});


