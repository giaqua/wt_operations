// Copyright (c) 2026, Takamol and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Operation Water Sample", {
	refresh(frm) {

	},
    fetch_required_parameters(frm) {
        console.log("fetch_required_parameters");
        if (frm.doc.parameters_required.length > 0) {
            let parameters_required = frm.doc.parameters_required
            frm.clear_table("sample_collection_details");
            parameters_required.forEach(parameter => {
                 let child = frm.add_child("sample_collection_details");
                child.parameter = parameter.parameter;
            });
             frm.refresh_field("sample_collection_details");
            
        }
        

    }
        
});
