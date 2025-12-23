# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
import json


def add_deadline_fields_to_doctypes():
	"""Add deadline management fields to all workflow doctypes"""
	
	# Define the deadline fields to add
	deadline_fields = [
		{
			"fieldname": "deadline_management_section",
			"fieldtype": "Section Break",
			"label": "Deadline Management",
			"collapsible": 1
		},
		{
			"fieldname": "deadline_date",
			"fieldtype": "Date",
			"label": "Deadline Date",
			"description": "Target completion date for this document"
		},
		{
			"fieldname": "deadline_status",
			"fieldtype": "Select",
			"label": "Deadline Status",
			"options": "On Time\nApproaching Deadline\nDue Today\nOverdue",
			"read_only": 1
		},
		{
			"fieldname": "deadline_urgency_level",
			"fieldtype": "Select",
			"label": "Urgency Level",
			"options": "low\nmedium\nhigh\ncritical",
			"read_only": 1
		},
		{
			"fieldname": "column_break_deadline",
			"fieldtype": "Column Break"
		},
		{
			"fieldname": "days_to_deadline",
			"fieldtype": "Int",
			"label": "Days to Deadline",
			"read_only": 1
		},
		{
			"fieldname": "escalation_level",
			"fieldtype": "Int",
			"label": "Escalation Level",
			"default": "0",
			"read_only": 1
		},
		{
			"fieldname": "last_escalation_date",
			"fieldtype": "Datetime",
			"label": "Last Escalation Date",
			"read_only": 1,
			"hidden": 1
		},
		{
			"fieldname": "section_break_deadline_details",
			"fieldtype": "Section Break",
			"label": "Deadline Details",
			"collapsible": 1,
			"collapsible_depends_on": "deadline_calculation_method"
		},
		{
			"fieldname": "deadline_calculation_method",
			"fieldtype": "Data",
			"label": "Calculation Method",
			"read_only": 1
		},
		{
			"fieldname": "deadline_calculation_details",
			"fieldtype": "Small Text",
			"label": "Calculation Details",
			"read_only": 1
		},
		{
			"fieldname": "column_break_deadline_override",
			"fieldtype": "Column Break"
		},
		{
			"fieldname": "escalation_override_reason",
			"fieldtype": "Small Text",
			"label": "Escalation Override Reason",
			"read_only": 1
		},
		{
			"fieldname": "escalation_override_by",
			"fieldtype": "Link",
			"label": "Override By",
			"options": "User",
			"read_only": 1
		},
		{
			"fieldname": "escalation_override_date",
			"fieldtype": "Datetime",
			"label": "Override Date",
			"read_only": 1
		},
		{
			"fieldname": "last_deadline_check",
			"fieldtype": "Datetime",
			"label": "Last Deadline Check",
			"read_only": 1,
			"hidden": 1
		}
	]
	
	# Define doctypes that need deadline fields
	workflow_doctypes = [
		"WWTP Technical Questionnaire",
		"Site Visit Request",
		"Site Visit", 
		"Water Sample",
		"Lab Test Result",
		"WWTP Technical Proposal",
		"Customer Proposal"
	]
	
	for doctype_name in workflow_doctypes:
		try:
			add_deadline_fields_to_doctype(doctype_name, deadline_fields)
			frappe.logger().info(f"Added deadline fields to {doctype_name}")
		except Exception as e:
			frappe.log_error(f"Error adding deadline fields to {doctype_name}: {str(e)}")


def add_deadline_fields_to_doctype(doctype_name, deadline_fields):
	"""Add deadline fields to a specific doctype"""
	
	# Get the doctype document
	doctype_doc = frappe.get_doc("DocType", doctype_name)
	
	# Check if deadline fields already exist
	existing_fieldnames = [field.fieldname for field in doctype_doc.fields]
	
	# Add fields that don't exist
	fields_added = 0
	for field_def in deadline_fields:
		if field_def["fieldname"] not in existing_fieldnames:
			doctype_doc.append("fields", field_def)
			fields_added += 1
	
	if fields_added > 0:
		# Update field_order to include new fields
		new_fieldnames = [field.fieldname for field in doctype_doc.fields]
		doctype_doc.field_order = new_fieldnames
		
		# Save the doctype
		doctype_doc.save(ignore_permissions=True)
		
		frappe.logger().info(f"Added {fields_added} deadline fields to {doctype_name}")
	else:
		frappe.logger().info(f"No new deadline fields needed for {doctype_name}")


def update_existing_documents_with_deadlines():
	"""Update existing documents with calculated deadlines"""
	
	from .deadline_engine import DeadlineCalculationEngine
	
	engine = DeadlineCalculationEngine()
	workflow_doctypes = [
		"WWTP Technical Questionnaire",
		"Site Visit Request",
		"Site Visit", 
		"Water Sample",
		"Lab Test Result",
		"WWTP Technical Proposal",
		"Customer Proposal"
	]
	
	total_updated = 0
	
	for doctype_name in workflow_doctypes:
		try:
			# Get all active documents of this type without deadlines
			documents = frappe.get_all(
				doctype_name,
				filters={
					"docstatus": ["!=", 2],  # Not cancelled
					"deadline_date": ["is", "not set"]
				},
				fields=["name", "creation"]
			)
			
			updated_count = 0
			for doc_info in documents:
				try:
					success = engine.update_document_deadline(
						doctype_name, 
						doc_info.name, 
						save=True
					)
					if success:
						updated_count += 1
				except Exception as e:
					frappe.log_error(f"Error updating deadline for {doctype_name} {doc_info.name}: {str(e)}")
					continue
			
			total_updated += updated_count
			frappe.logger().info(f"Updated deadlines for {updated_count} {doctype_name} documents")
			
		except Exception as e:
			frappe.log_error(f"Error updating deadlines for {doctype_name}: {str(e)}")
	
	frappe.logger().info(f"Total documents updated with deadlines: {total_updated}")
	return total_updated


@frappe.whitelist()
def setup_deadline_fields():
	"""API endpoint to setup deadline fields on all workflow doctypes"""
	try:
		# Add fields to doctypes
		add_deadline_fields_to_doctypes()
		
		# Update existing documents
		updated_count = update_existing_documents_with_deadlines()
		
		return {
			"success": True, 
			"message": f"Deadline fields added to doctypes and {updated_count} existing documents updated"
		}
	
	except Exception as e:
		frappe.log_error(f"Error setting up deadline fields: {str(e)}")
		return {"success": False, "message": str(e)}


def execute():
	"""Patch function to add deadline fields"""
	add_deadline_fields_to_doctypes()
	update_existing_documents_with_deadlines()