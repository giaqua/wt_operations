# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, getdate, add_days, get_datetime, cint
from frappe.utils.background_jobs import enqueue
from .deadline_engine import get_deadline_status
import json
from datetime import datetime, timedelta


class EscalationManager:
	"""
	Manages escalation procedures for overdue documents based on configured rules.
	Handles automatic escalation triggers, notifications, and override mechanisms.
	"""
	
	def __init__(self):
		self.tracked_doctypes = [
			"WWTP Technical Questionnaire",
			"Site Visit Request", 
			"Site Visit",
			"Water Sample",
			"Lab Test Result",
			"WWTP Technical Proposal",
			"Customer Proposal"
		]
	
	def run_escalation_check(self):
		"""Main method to check and process escalations for all documents"""
		frappe.logger().info("Starting escalation check")
		
		try:
			escalation_count = 0
			
			for doctype in self.tracked_doctypes:
				count = self._process_doctype_escalations(doctype)
				escalation_count += count
			
			frappe.logger().info(f"Processed {escalation_count} escalations")
			
			# Log escalation summary
			self._log_escalation_summary(escalation_count)
			
		except Exception as e:
			frappe.log_error(f"Error in escalation check: {str(e)}", "Escalation Manager")
			raise
	
	def _process_doctype_escalations(self, doctype):
		"""Process escalations for a specific document type"""
		try:
			# Get deadline configuration for this doctype
			config = self._get_deadline_configuration(doctype)
			if not config or not config.escalation_rules:
				return 0
			
			# Get overdue documents
			overdue_docs = self._get_overdue_documents(doctype)
			escalation_count = 0
			
			for doc_info in overdue_docs:
				try:
					doc = frappe.get_doc(doctype, doc_info.name)
					
					# Skip if document is in final state
					if self._is_final_state(doc):
						continue
					
					# Check if escalation is needed
					if self._should_escalate(doc, config):
						self._execute_escalation(doc, config)
						escalation_count += 1
				
				except Exception as e:
					frappe.log_error(f"Error processing escalation for {doctype} {doc_info.name}: {str(e)}")
					continue
			
			return escalation_count
		
		except Exception as e:
			frappe.log_error(f"Error processing escalations for {doctype}: {str(e)}")
			return 0
	
	def _get_deadline_configuration(self, doctype):
		"""Get deadline configuration for a document type"""
		try:
			config_name = frappe.db.get_value(
				"Deadline Configuration",
				{"document_type": doctype, "is_active": 1},
				"name"
			)
			
			if config_name:
				return frappe.get_doc("Deadline Configuration", config_name)
			
			return None
		
		except Exception as e:
			frappe.log_error(f"Error getting deadline configuration for {doctype}: {str(e)}")
			return None
	
	def _get_overdue_documents(self, doctype):
		"""Get all overdue documents for a doctype"""
		try:
			return frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],  # Not cancelled
					"deadline_date": ["<", nowdate()],
					"deadline_status": "Overdue"
				},
				fields=["name", "deadline_date", "escalation_level", "last_escalation_date"]
			)
		
		except Exception as e:
			frappe.log_error(f"Error getting overdue documents for {doctype}: {str(e)}")
			return []
	
	def _should_escalate(self, doc, config):
		"""Determine if a document should be escalated"""
		try:
			deadline_date = doc.get("deadline_date")
			if not deadline_date:
				return False
			
			# Calculate days overdue
			days_overdue = (getdate(nowdate()) - getdate(deadline_date)).days
			
			if days_overdue <= 0:
				return False  # Not overdue
			
			# Get current escalation level
			current_level = doc.get("escalation_level", 0)
			
			# Check if there's a higher escalation level available
			next_level = self._get_next_escalation_level(days_overdue, current_level, config)
			
			if next_level > current_level:
				# Check if enough time has passed since last escalation
				return self._check_escalation_timing(doc, next_level, config)
			
			return False
		
		except Exception as e:
			frappe.log_error(f"Error checking escalation for {doc.doctype} {doc.name}: {str(e)}")
			return False
	
	def _get_next_escalation_level(self, days_overdue, current_level, config):
		"""Get the next escalation level based on days overdue"""
		next_level = current_level
		
		for rule in config.escalation_rules:
			if days_overdue >= rule.days_overdue and rule.escalation_level > current_level:
				next_level = max(next_level, rule.escalation_level)
		
		return next_level
	
	def _check_escalation_timing(self, doc, next_level, config):
		"""Check if enough time has passed for the next escalation"""
		last_escalation = doc.get("last_escalation_date")
		
		if not last_escalation:
			return True  # First escalation
		
		# Minimum 24 hours between escalations
		min_hours_between = 24
		hours_since_last = (get_datetime() - get_datetime(last_escalation)).total_seconds() / 3600
		
		return hours_since_last >= min_hours_between
	
	def _execute_escalation(self, doc, config):
		"""Execute escalation for a document"""
		try:
			deadline_date = doc.get("deadline_date")
			days_overdue = (getdate(nowdate()) - getdate(deadline_date)).days
			current_level = doc.get("escalation_level", 0)
			
			# Find applicable escalation rule
			escalation_rule = None
			for rule in config.escalation_rules:
				if (days_overdue >= rule.days_overdue and 
					rule.escalation_level > current_level):
					escalation_rule = rule
					break
			
			if not escalation_rule:
				return
			
			# Update document escalation level
			doc.escalation_level = escalation_rule.escalation_level
			doc.last_escalation_date = get_datetime()
			doc.save(ignore_permissions=True)
			
			# Execute escalation actions
			self._execute_escalation_actions(doc, escalation_rule, days_overdue)
			
			# Log escalation
			self._log_escalation(doc, escalation_rule, days_overdue)
			
			frappe.logger().info(f"Escalated {doc.doctype} {doc.name} to level {escalation_rule.escalation_level}")
		
		except Exception as e:
			frappe.log_error(f"Error executing escalation for {doc.doctype} {doc.name}: {str(e)}")
	
	def _execute_escalation_actions(self, doc, escalation_rule, days_overdue):
		"""Execute the specific escalation actions"""
		try:
			action = escalation_rule.escalation_action
			
			if action == "Email Notification":
				self._send_escalation_email(doc, escalation_rule, days_overdue)
			
			elif action == "System Alert":
				self._create_system_alert(doc, escalation_rule, days_overdue)
			
			elif action == "Manager Notification":
				self._notify_managers(doc, escalation_rule, days_overdue)
			
			elif action == "Automatic Reassignment":
				self._reassign_document(doc, escalation_rule)
		
		except Exception as e:
			frappe.log_error(f"Error executing escalation action {escalation_rule.escalation_action}: {str(e)}")
	
	def _send_escalation_email(self, doc, escalation_rule, days_overdue):
		"""Send escalation email notification"""
		try:
			# Get recipients
			recipients = self._get_escalation_recipients(doc, escalation_rule)
			
			if not recipients:
				return
			
			# Prepare email content
			subject = f"ESCALATION LEVEL {escalation_rule.escalation_level}: {doc.doctype} {doc.name} is {days_overdue} days overdue"
			
			message = f"""
			<h3>Document Escalation Alert</h3>
			<p><strong>Document:</strong> {doc.doctype} - {doc.name}</p>
			<p><strong>Deadline:</strong> {doc.get('deadline_date')}</p>
			<p><strong>Days Overdue:</strong> {days_overdue}</p>
			<p><strong>Escalation Level:</strong> {escalation_rule.escalation_level}</p>
			<p><strong>Current Status:</strong> {doc.get('workflow_state', 'N/A')}</p>
			
			<p>This document requires immediate attention. Please take necessary action to resolve the delay.</p>
			
			<p><a href="{frappe.utils.get_url()}/app/{doc.doctype.lower().replace(' ', '-')}/{doc.name}">View Document</a></p>
			"""
			
			# Send email
			frappe.sendmail(
				recipients=recipients,
				subject=subject,
				message=message,
				reference_doctype=doc.doctype,
				reference_name=doc.name
			)
		
		except Exception as e:
			frappe.log_error(f"Error sending escalation email: {str(e)}")
	
	def _create_system_alert(self, doc, escalation_rule, days_overdue):
		"""Create system alert for escalation"""
		try:
			alert_content = f"""
			ESCALATION ALERT - Level {escalation_rule.escalation_level}
			
			Document: {doc.doctype} - {doc.name}
			Deadline: {doc.get('deadline_date')}
			Days Overdue: {days_overdue}
			Current Status: {doc.get('workflow_state', 'N/A')}
			
			Immediate action required.
			"""
			
			# Create notification log
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Escalation Level {escalation_rule.escalation_level}: {doc.doctype} {doc.name}",
				"email_content": alert_content,
				"for_user": "Administrator",
				"type": "Alert",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"read": 0
			}).insert(ignore_permissions=True)
		
		except Exception as e:
			frappe.log_error(f"Error creating system alert: {str(e)}")
	
	def _notify_managers(self, doc, escalation_rule, days_overdue):
		"""Notify managers about escalation"""
		try:
			# Get manager roles
			manager_roles = ["Operations Manager", "System Manager"]
			
			# Get users with manager roles
			managers = frappe.get_all(
				"Has Role",
				filters={"role": ["in", manager_roles]},
				fields=["parent"],
				distinct=True
			)
			
			manager_emails = []
			for manager in managers:
				user_email = frappe.db.get_value("User", manager.parent, "email")
				if user_email:
					manager_emails.append(user_email)
			
			if manager_emails:
				subject = f"MANAGER ALERT: {doc.doctype} {doc.name} escalated to Level {escalation_rule.escalation_level}"
				
				message = f"""
				<h3>Manager Escalation Alert</h3>
				<p>A document has been escalated and requires management attention:</p>
				
				<p><strong>Document:</strong> {doc.doctype} - {doc.name}</p>
				<p><strong>Deadline:</strong> {doc.get('deadline_date')}</p>
				<p><strong>Days Overdue:</strong> {days_overdue}</p>
				<p><strong>Escalation Level:</strong> {escalation_rule.escalation_level}</p>
				<p><strong>Assigned To:</strong> {doc.get('assigned_to', 'Unassigned')}</p>
				
				<p>Please review and take appropriate management action.</p>
				
				<p><a href="{frappe.utils.get_url()}/app/{doc.doctype.lower().replace(' ', '-')}/{doc.name}">View Document</a></p>
				"""
				
				frappe.sendmail(
					recipients=manager_emails,
					subject=subject,
					message=message,
					reference_doctype=doc.doctype,
					reference_name=doc.name
				)
		
		except Exception as e:
			frappe.log_error(f"Error notifying managers: {str(e)}")
	
	def _reassign_document(self, doc, escalation_rule):
		"""Automatically reassign document to a different user"""
		try:
			# Get potential assignees based on document type
			assignees = self._get_potential_assignees(doc.doctype)
			
			if not assignees:
				return
			
			# Get current assignee
			current_assignee = doc.get("assigned_to")
			
			# Find a different assignee
			new_assignee = None
			for assignee in assignees:
				if assignee != current_assignee:
					new_assignee = assignee
					break
			
			if new_assignee:
				# Update assignment
				doc.assigned_to = new_assignee
				doc.save(ignore_permissions=True)
				
				# Create assignment comment
				frappe.get_doc({
					"doctype": "Comment",
					"comment_type": "Info",
					"reference_doctype": doc.doctype,
					"reference_name": doc.name,
					"content": f"Document automatically reassigned to {new_assignee} due to escalation level {escalation_rule.escalation_level}",
					"comment_by": "Administrator"
				}).insert(ignore_permissions=True)
				
				# Notify new assignee
				self._notify_new_assignee(doc, new_assignee, escalation_rule)
		
		except Exception as e:
			frappe.log_error(f"Error reassigning document: {str(e)}")
	
	def _get_potential_assignees(self, doctype):
		"""Get potential assignees for a document type"""
		try:
			# Map document types to roles
			role_mapping = {
				"WWTP Technical Questionnaire": ["Technical Engineer", "Operations Manager"],
				"Site Visit Request": ["Site Manager", "Operations Manager"],
				"Site Visit": ["Site Manager", "Technical Engineer"],
				"Water Sample": ["Lab Technician", "Site Manager"],
				"Lab Test Result": ["Lab Technician", "Operations Manager"],
				"WWTP Technical Proposal": ["Technical Engineer", "Operations Manager"],
				"Customer Proposal": ["Sales Manager", "Operations Manager"]
			}
			
			roles = role_mapping.get(doctype, ["Operations Manager"])
			
			# Get users with these roles
			users = frappe.get_all(
				"Has Role",
				filters={"role": ["in", roles]},
				fields=["parent"],
				distinct=True
			)
			
			# Filter active users
			assignees = []
			for user in users:
				user_doc = frappe.get_doc("User", user.parent)
				if user_doc.enabled and not user_doc.user_type == "Website User":
					assignees.append(user.parent)
			
			return assignees
		
		except Exception as e:
			frappe.log_error(f"Error getting potential assignees: {str(e)}")
			return []
	
	def _notify_new_assignee(self, doc, new_assignee, escalation_rule):
		"""Notify new assignee about document assignment"""
		try:
			user_email = frappe.db.get_value("User", new_assignee, "email")
			
			if user_email:
				subject = f"URGENT: {doc.doctype} {doc.name} assigned to you (Escalation Level {escalation_rule.escalation_level})"
				
				message = f"""
				<h3>Urgent Document Assignment</h3>
				<p>You have been assigned an overdue document that has been escalated:</p>
				
				<p><strong>Document:</strong> {doc.doctype} - {doc.name}</p>
				<p><strong>Original Deadline:</strong> {doc.get('deadline_date')}</p>
				<p><strong>Escalation Level:</strong> {escalation_rule.escalation_level}</p>
				<p><strong>Reason:</strong> Automatic reassignment due to escalation</p>
				
				<p>Please prioritize this document and take immediate action.</p>
				
				<p><a href="{frappe.utils.get_url()}/app/{doc.doctype.lower().replace(' ', '-')}/{doc.name}">View Document</a></p>
				"""
				
				frappe.sendmail(
					recipients=[user_email],
					subject=subject,
					message=message,
					reference_doctype=doc.doctype,
					reference_name=doc.name
				)
		
		except Exception as e:
			frappe.log_error(f"Error notifying new assignee: {str(e)}")
	
	def _get_escalation_recipients(self, doc, escalation_rule):
		"""Get recipients for escalation notifications"""
		try:
			recipients = []
			
			# Parse notify_roles from escalation rule
			if escalation_rule.notify_roles:
				roles = [role.strip() for role in escalation_rule.notify_roles.split(",")]
				
				for role in roles:
					users = frappe.get_all(
						"Has Role",
						filters={"role": role},
						fields=["parent"]
					)
					
					for user in users:
						user_email = frappe.db.get_value("User", user.parent, "email")
						if user_email and user_email not in recipients:
							recipients.append(user_email)
			
			# Always include assigned user if exists
			assigned_to = doc.get("assigned_to")
			if assigned_to:
				assigned_email = frappe.db.get_value("User", assigned_to, "email")
				if assigned_email and assigned_email not in recipients:
					recipients.append(assigned_email)
			
			return recipients
		
		except Exception as e:
			frappe.log_error(f"Error getting escalation recipients: {str(e)}")
			return []
	
	def _is_final_state(self, doc):
		"""Check if document is in a final workflow state"""
		final_states = [
			"Completed", "Approved", "Closed", "Cancelled", 
			"Synced to Operations", "Synced to Sales", "Sent to Customer"
		]
		
		workflow_state = doc.get("workflow_state")
		return workflow_state in final_states
	
	def _log_escalation(self, doc, escalation_rule, days_overdue):
		"""Log escalation event"""
		try:
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": f"Document escalated to Level {escalation_rule.escalation_level} ({days_overdue} days overdue). Action: {escalation_rule.escalation_action}",
				"comment_by": "Administrator"
			}).insert(ignore_permissions=True)
		
		except Exception as e:
			frappe.log_error(f"Error logging escalation: {str(e)}")
	
	def _log_escalation_summary(self, escalation_count):
		"""Log escalation summary"""
		try:
			if escalation_count > 0:
				frappe.get_doc({
					"doctype": "Error Log",
					"method": "Escalation Manager",
					"error": f"Processed {escalation_count} document escalations on {nowdate()}"
				}).insert(ignore_permissions=True)
		
		except Exception as e:
			frappe.log_error(f"Error logging escalation summary: {str(e)}")
	
	def override_escalation(self, doctype, name, reason, override_by):
		"""Override escalation for a specific document"""
		try:
			doc = frappe.get_doc(doctype, name)
			
			# Reset escalation level
			doc.escalation_level = 0
			doc.escalation_override_reason = reason
			doc.escalation_override_by = override_by
			doc.escalation_override_date = get_datetime()
			doc.save(ignore_permissions=True)
			
			# Log override
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doctype,
				"reference_name": name,
				"content": f"Escalation overridden by {override_by}. Reason: {reason}",
				"comment_by": override_by
			}).insert(ignore_permissions=True)
			
			return True
		
		except Exception as e:
			frappe.log_error(f"Error overriding escalation: {str(e)}")
			return False


# Scheduled job functions
def run_escalation_check():
	"""Scheduled job to run escalation checks"""
	manager = EscalationManager()
	manager.run_escalation_check()


# API endpoints
@frappe.whitelist()
def override_document_escalation(doctype, name, reason):
	"""API endpoint to override escalation for a document"""
	try:
		manager = EscalationManager()
		success = manager.override_escalation(doctype, name, reason, frappe.session.user)
		
		return {
			"success": success,
			"message": "Escalation overridden successfully" if success else "Failed to override escalation"
		}
	
	except Exception as e:
		frappe.log_error(f"Error in escalation override API: {str(e)}")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_escalation_history(doctype, name):
	"""API endpoint to get escalation history for a document"""
	try:
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": doctype,
				"reference_name": name,
				"content": ["like", "%escalat%"]
			},
			fields=["content", "creation", "comment_by"],
			order_by="creation desc"
		)
		
		return comments
	
	except Exception as e:
		frappe.log_error(f"Error getting escalation history: {str(e)}")
		return []


@frappe.whitelist()
def get_escalation_dashboard_data():
	"""API endpoint to get escalation dashboard data"""
	try:
		manager = EscalationManager()
		dashboard_data = {}
		
		for doctype in manager.tracked_doctypes:
			# Get escalation statistics
			escalated_docs = frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],
					"escalation_level": [">", 0]
				},
				fields=["name", "escalation_level", "deadline_date"]
			)
			
			level_counts = {}
			for doc in escalated_docs:
				level = doc.escalation_level
				if level not in level_counts:
					level_counts[level] = 0
				level_counts[level] += 1
			
			dashboard_data[doctype] = {
				"total_escalated": len(escalated_docs),
				"level_breakdown": level_counts
			}
		
		return dashboard_data
	
	except Exception as e:
		frappe.log_error(f"Error getting escalation dashboard data: {str(e)}")
		return {}