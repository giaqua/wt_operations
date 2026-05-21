# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeProjectAllocationTool(Document):
	pass


@frappe.whitelist()
def get_child_table_data(parent_doctype, child_table_fieldname):
    """
    Get child table data for a parent document
    """
    try:
        # Get the parent document
        parent_doc = frappe.get_doc("Employee Project Allocation", parent_doctype)
        
        # Get child table data
        child_table_data = parent_doc.get(child_table_fieldname, [])
        
        # Return as list of dicts
        return [{
            "project": row.project,
            "activity": row.activity,
            "percentage": row.percentage
        } for row in child_table_data]
        
    except Exception as e:
        frappe.log_error(f"Error getting child table data: {str(e)}", "Employee Allocation Tool")
        return []