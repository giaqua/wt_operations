# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now
from .deadline_engine import DeadlineCalculationEngine, update_document_deadline
from .deadline_tracker import DeadlineTracker
from .escalation_manager import EscalationManager


def on_submit_technical_questionnaire(doc, method):
	"""Handle Technical Questionnaire submission for workflow"""
	# Set initial workflow status
	doc.db_set("workflow_status", "Submitted")
	doc.db_set("sync_status", "Pending")
	
	# Calculate and set deadline
	update_document_deadline(doc.doctype, doc.name, save=False)
	
	# Auto-sync if enabled
	try:
		settings = frappe.get_all("External Site Settings", 
			filters={"enabled": 1, "auto_sync_enabled": 1, "sync_technical_questionnaires": 1}, 
			limit=1)
		
		if settings:
			from wt_operations.wt_operations.sync_manager import sync_document_to_external_site
			external_name = sync_document_to_external_site("WWTP Technical Questionnaire", doc.name, settings[0].name)
			
			if external_name:
				# Only set external_document_name if the field exists
				if hasattr(doc, "external_document_name"):
					doc.db_set("external_document_name", external_name)
				
				# Create workflow tracking entry
				create_workflow_tracking(doc)
				
	except Exception as e:
		frappe.logger().error(f"Auto-sync failed for Technical Questionnaire {doc.name}: {str(e)}")
		# Don't fail the submission, just log the error
		doc.db_set("sync_status", "Failed")
		doc.db_set("sync_error_message", str(e))


def on_submit_technical_proposal(doc, method):
	"""Handle Technical Proposal submission for workflow"""
	# Set initial workflow status
	doc.db_set("workflow_status", "Under Review")
	doc.db_set("review_status", "Pending")
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Technical Proposal", "In Progress")


def on_submit_customer_proposal(doc, method):
	"""Handle Customer Proposal submission for workflow"""
	# Set initial workflow status
	doc.db_set("workflow_status", "Under Review")
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Customer Proposal", "In Progress")


def on_submit_site_visit_request(doc, method):
	"""Handle Site Visit Request submission for workflow"""
	# Calculate and set deadline
	update_document_deadline(doc.doctype, doc.name, save=False)
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Site Visit Request", "In Progress")
	
	# Auto-sync Site Visit Request to external site if enabled
	try:
		# Check for sync_site_visit_requests field, if not exists, use enabled filter only
		settings = frappe.get_all("External Site Settings", 
			filters={"enabled": 1}, 
			limit=1)
		
		if settings:
			from wt_operations.wt_operations.sync_manager import sync_document_to_external_site
			external_name = sync_document_to_external_site("Site Visit Request", doc.name, settings[0].name)
			if external_name:
				doc.db_set("external_sync_status", "Synced")
				doc.db_set("external_request_name", external_name)
				frappe.logger().info(f"Site Visit Request {doc.name} auto-synced to external site as {external_name}")
			else:
				doc.db_set("external_sync_status", "Failed")
				frappe.log_error(f"Auto-sync failed for Site Visit Request {doc.name}", "SVR Auto-Sync Error")
	except Exception as e:
		frappe.logger().error(f"Auto-sync failed for Site Visit Request {doc.name}: {str(e)}")
		# Don't fail the submission, just log the error
		doc.db_set("external_sync_status", "Failed")
		frappe.log_error(f"Auto-sync error for Site Visit Request {doc.name}: {str(e)}", "SVR Auto-Sync Error")


def on_submit_site_visit(doc, method):
	"""Handle Site Visit submission for workflow"""
	# Set completion status
	doc.db_set("completion_status", "Completed")
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Site Visit", "Completed")


def on_submit_water_sample(doc, method):
	"""Handle Water Sample submission for workflow"""
	# Set sample status
	doc.db_set("sample_status", "In Lab")
	
	# Calculate expected results date if not set
	if not doc.expected_results_date:
		deadline_config = get_deadline_configuration("Lab Test Result")
		if deadline_config:
			doc.db_set("expected_results_date", deadline_config.calculate_deadline())
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Water Sample", "In Progress")


def on_submit_lab_test_result(doc, method):
	"""Handle Lab Test Result submission for workflow"""
	# Set completion date
	doc.db_set("analysis_completion_date", now())
	
	# Update compliance status based on results
	update_compliance_status(doc)
	
	# Update workflow tracking
	update_workflow_tracking(doc, "Lab Test Result", "Completed")


def create_workflow_tracking(doc):
	"""Create workflow tracking entry for a lead"""
	if not doc.lead:
		return
	
	# Check if workflow tracking already exists
	existing = frappe.get_all("Workflow Tracking", 
		filters={"lead": doc.lead}, limit=1)
	
	if existing:
		workflow_doc = frappe.get_doc("Workflow Tracking", existing[0].name)
	else:
		workflow_doc = frappe.new_doc("Workflow Tracking")
		workflow_doc.lead = doc.lead
		workflow_doc.actual_start_date = frappe.utils.nowdate()
	
	# Add stage history
	workflow_doc.add_stage_history("Technical Questionnaire", "Completed", doc.name)
	
	# Add to site 1 documents
	workflow_doc.append("site_1_documents", {
		"document_type": "WWTP Technical Questionnaire",
		"document_name": doc.name,
		"status": "Submitted",
		"created_date": frappe.utils.nowdate(),
		"last_updated": now()
	})
	
	workflow_doc.save()


def update_workflow_tracking(doc, stage_name, status):
	"""Update workflow tracking for a document"""
	if not hasattr(doc, 'lead') or not doc.lead:
		return
	
	# Find workflow tracking for this lead
	tracking_docs = frappe.get_all("Workflow Tracking", 
		filters={"lead": doc.lead}, limit=1)
	
	if not tracking_docs:
		return
	
	workflow_doc = frappe.get_doc("Workflow Tracking", tracking_docs[0].name)
	
	# Add or update stage history
	workflow_doc.add_stage_history(stage_name, status, doc.name)
	
	# Add to appropriate site documents table
	site_table = "site_1_documents" if doc.doctype in ["WWTP Technical Questionnaire", "Customer Proposal"] else "site_2_documents"
	
	# Check if document already exists in table
	existing_doc = None
	for row in getattr(workflow_doc, site_table):
		if row.document_name == doc.name:
			existing_doc = row
			break
	
	if existing_doc:
		existing_doc.status = status
		existing_doc.last_updated = now()
	else:
		workflow_doc.append(site_table, {
			"document_type": doc.doctype,
			"document_name": doc.name,
			"status": status,
			"created_date": frappe.utils.nowdate(),
			"last_updated": now()
		})
	
	workflow_doc.save()


def get_deadline_configuration(doctype):
	"""Get deadline configuration for a doctype"""
	configs = frappe.get_all("Deadline Configuration", 
		filters={"document_type": doctype, "is_active": 1}, limit=1)
	
	if configs:
		return frappe.get_doc("Deadline Configuration", configs[0].name)
	
	return None


def update_compliance_status(lab_result_doc):
	"""Update compliance status based on lab test results"""
	# This is a placeholder - implement actual compliance checking logic
	# based on regulatory standards and parameter values
	
	if lab_result_doc.regulatory_standard:
		# Compare results against regulatory standard
		# For now, set as compliant by default
		lab_result_doc.db_set("compliance_status", "Compliant")
	else:
		lab_result_doc.db_set("compliance_status", "Pending Review")


def calculate_deadline_for_document(doc, doctype_name=None):
	"""Calculate deadline for a document based on configuration"""
	if not doctype_name:
		doctype_name = doc.doctype
	
	deadline_config = get_deadline_configuration(doctype_name)
	if deadline_config:
		deadline = deadline_config.calculate_deadline()
		doc.db_set("deadline_date", deadline)
		return deadline
	
	return None


def check_overdue_documents():
	"""Scheduled function to check for overdue documents and trigger escalations"""
	try:
		# Use the new deadline tracker and escalation manager
		tracker = DeadlineTracker()
		tracker.run_deadline_monitoring()
		
		escalation_manager = EscalationManager()
		escalation_manager.run_escalation_check()
		
	except Exception as e:
		frappe.log_error(f"Error in scheduled deadline check: {str(e)}")


def handle_overdue_document(doc):
	"""Handle an overdue document by updating escalation level and triggering notifications"""
	try:
		# Use the new escalation manager
		escalation_manager = EscalationManager()
		escalation_manager._execute_escalation(doc, None)
		
	except Exception as e:
		frappe.log_error(f"Error handling overdue document {doc.doctype} {doc.name}: {str(e)}")


def trigger_escalation_notification(doc, escalation_level):
	"""Trigger escalation notification for overdue document"""
	try:
		# Use the new escalation manager
		escalation_manager = EscalationManager()
		
		# Get deadline configuration
		config = escalation_manager._get_deadline_configuration(doc.doctype)
		if config and config.escalation_rules:
			# Find the appropriate escalation rule
			for rule in config.escalation_rules:
				if rule.escalation_level == escalation_level:
					escalation_manager._execute_escalation_actions(doc, rule, 0)
					break
		
	except Exception as e:
		frappe.log_error(f"Error triggering escalation notification: {str(e)}")


# Document event hooks for deadline management
def on_document_insert(doc, method):
	"""Handle document insertion for deadline calculation"""
	if doc.doctype in ["WWTP Technical Questionnaire", "Site Visit Request", "Site Visit", 
					   "Water Sample", "Lab Test Result", "WWTP Technical Proposal", "Customer Proposal"]:
		try:
			update_document_deadline(doc.doctype, doc.name, save=False)
		except Exception as e:
			frappe.log_error(f"Error calculating deadline on insert for {doc.doctype} {doc.name}: {str(e)}")


def on_document_update(doc, method):
	"""Handle document updates for deadline tracking"""
	if doc.doctype in ["WWTP Technical Questionnaire", "Site Visit Request", "Site Visit", 
					   "Water Sample", "Lab Test Result", "WWTP Technical Proposal", "Customer Proposal"]:
		try:
			# Update deadline status if deadline exists
			if hasattr(doc, 'deadline_date') and doc.deadline_date:
				from .deadline_engine import get_deadline_status
				status_info = get_deadline_status(doc.deadline_date)
				
				if hasattr(doc, 'deadline_status'):
					doc.db_set("deadline_status", status_info['status'], update_modified=False)
				
				if hasattr(doc, 'deadline_urgency_level'):
					doc.db_set("deadline_urgency_level", status_info['urgency_level'], update_modified=False)
				
				if hasattr(doc, 'days_to_deadline'):
					doc.db_set("days_to_deadline", status_info['days_remaining'], update_modified=False)
		
		except Exception as e:
			frappe.log_error(f"Error updating deadline status for {doc.doctype} {doc.name}: {str(e)}")