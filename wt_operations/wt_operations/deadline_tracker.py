# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, getdate, add_days, get_datetime, cint
from frappe.utils.background_jobs import enqueue
from .deadline_engine import DeadlineCalculationEngine, get_deadline_status
import json
from datetime import datetime, timedelta


class DeadlineTracker:
	"""
	Automated deadline tracking system that monitors document deadlines,
	updates status indicators, and triggers escalations.
	"""
	
	def __init__(self):
		self.engine = DeadlineCalculationEngine()
		self.tracked_doctypes = [
			"WWTP Technical Questionnaire",
			"Site Visit Request", 
			"Site Visit",
			"Water Sample",
			"Lab Test Result",
			"WWTP Technical Proposal",
			"Customer Proposal"
		]
	
	def run_deadline_monitoring(self):
		"""Main method to run deadline monitoring for all tracked documents"""
		frappe.logger().info("Starting deadline monitoring job")
		
		try:
			# Track deadlines for all document types
			for doctype in self.tracked_doctypes:
				self._track_doctype_deadlines(doctype)
			
			# Update deadline history
			self._update_deadline_history()
			
			# Generate deadline alerts
			self._generate_deadline_alerts()
			
			frappe.logger().info("Deadline monitoring job completed successfully")
			
		except Exception as e:
			frappe.log_error(f"Error in deadline monitoring: {str(e)}", "Deadline Monitoring")
			raise
	
	def _track_doctype_deadlines(self, doctype):
		"""Track deadlines for a specific document type"""
		try:
			# Get all active documents of this type
			documents = frappe.get_all(
				doctype,
				filters={"docstatus": ["!=", 2]},  # Exclude cancelled documents
				fields=["name", "deadline_date", "creation", "modified", "workflow_state"]
			)
			
			updated_count = 0
			
			for doc_info in documents:
				try:
					# Get the full document
					doc = frappe.get_doc(doctype, doc_info.name)
					
					# Skip if document is in final state
					if self._is_final_state(doc):
						continue
					
					# Update deadline status
					if self._update_document_deadline_status(doc):
						updated_count += 1
					
					# Calculate escalation level
					self._update_escalation_level(doc)
					
				except Exception as e:
					frappe.log_error(f"Error tracking deadline for {doctype} {doc_info.name}: {str(e)}")
					continue
			
			frappe.logger().info(f"Updated deadline status for {updated_count} {doctype} documents")
			
		except Exception as e:
			frappe.log_error(f"Error tracking deadlines for {doctype}: {str(e)}")
	
	def _update_document_deadline_status(self, doc):
		"""Update deadline status for a single document"""
		try:
			deadline_date = doc.get("deadline_date")
			if not deadline_date:
				# Try to calculate deadline if missing
				deadline_info = self.engine.calculate_deadline(
					document_type=doc.doctype,
					start_date=doc.creation
				)
				deadline_date = deadline_info["deadline_date"]
				
				# Update the document with calculated deadline
				if hasattr(doc, 'deadline_date'):
					doc.deadline_date = deadline_date
			
			# Get current deadline status
			status_info = get_deadline_status(deadline_date)
			
			# Update status fields if they exist
			updated = False
			
			if hasattr(doc, 'deadline_status') and doc.deadline_status != status_info['status']:
				doc.deadline_status = status_info['status']
				updated = True
			
			if hasattr(doc, 'deadline_urgency_level') and doc.deadline_urgency_level != status_info['urgency_level']:
				doc.deadline_urgency_level = status_info['urgency_level']
				updated = True
			
			if hasattr(doc, 'days_to_deadline'):
				doc.days_to_deadline = status_info['days_remaining']
				updated = True
			
			# Update last tracking timestamp
			if hasattr(doc, 'last_deadline_check'):
				doc.last_deadline_check = get_datetime()
				updated = True
			
			if updated:
				doc.save(ignore_permissions=True)
				return True
			
			return False
			
		except Exception as e:
			frappe.log_error(f"Error updating deadline status for {doc.doctype} {doc.name}: {str(e)}")
			return False
	
	def _update_escalation_level(self, doc):
		"""Update escalation level based on deadline configuration"""
		try:
			deadline_date = doc.get("deadline_date")
			if not deadline_date:
				return
			
			# Get deadline configuration for this document type
			config_name = frappe.db.get_value(
				"Deadline Configuration",
				{"document_type": doc.doctype, "is_active": 1},
				"name"
			)
			
			if not config_name:
				return
			
			config = frappe.get_doc("Deadline Configuration", config_name)
			escalation_level = config.get_escalation_level(deadline_date)
			
			# Update escalation level if field exists
			if hasattr(doc, 'escalation_level') and doc.escalation_level != escalation_level:
				doc.escalation_level = escalation_level
				doc.save(ignore_permissions=True)
				
				# Log escalation level change
				self._log_escalation_change(doc, escalation_level)
		
		except Exception as e:
			frappe.log_error(f"Error updating escalation level for {doc.doctype} {doc.name}: {str(e)}")
	
	def _log_escalation_change(self, doc, new_level):
		"""Log escalation level changes"""
		try:
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
				"content": f"Escalation level changed to {new_level} due to deadline status",
				"comment_by": "Administrator"
			}).insert(ignore_permissions=True)
		except:
			pass  # Don't fail if comment creation fails
	
	def _is_final_state(self, doc):
		"""Check if document is in a final workflow state"""
		final_states = [
			"Completed", "Approved", "Closed", "Cancelled", 
			"Synced to Operations", "Synced to Sales", "Sent to Customer"
		]
		
		workflow_state = doc.get("workflow_state")
		return workflow_state in final_states
	
	def _update_deadline_history(self):
		"""Update deadline history tracking"""
		try:
			# Create or update deadline history records
			for doctype in self.tracked_doctypes:
				self._create_deadline_history_entry(doctype)
		
		except Exception as e:
			frappe.log_error(f"Error updating deadline history: {str(e)}")
	
	def _create_deadline_history_entry(self, doctype):
		"""Create deadline history entry for a document type"""
		try:
			# Get deadline statistics
			stats = self._get_deadline_statistics(doctype)
			
			# Create history entry
			history_entry = frappe.get_doc({
				"doctype": "Deadline History",
				"document_type": doctype,
				"tracking_date": nowdate(),
				"total_documents": stats["total"],
				"on_time_count": stats["on_time"],
				"approaching_deadline_count": stats["approaching"],
				"overdue_count": stats["overdue"],
				"average_days_to_deadline": stats["avg_days"]
			})
			
			# Check if entry for today already exists
			existing = frappe.db.exists(
				"Deadline History",
				{"document_type": doctype, "tracking_date": nowdate()}
			)
			
			if existing:
				# Update existing entry
				existing_doc = frappe.get_doc("Deadline History", existing)
				for field in ["total_documents", "on_time_count", "approaching_deadline_count", 
							 "overdue_count", "average_days_to_deadline"]:
					setattr(existing_doc, field, getattr(history_entry, field))
				existing_doc.save(ignore_permissions=True)
			else:
				# Create new entry
				history_entry.insert(ignore_permissions=True)
		
		except Exception as e:
			frappe.log_error(f"Error creating deadline history for {doctype}: {str(e)}")
	
	def _get_deadline_statistics(self, doctype):
		"""Get deadline statistics for a document type"""
		try:
			# Get all active documents
			documents = frappe.get_all(
				doctype,
				filters={"docstatus": ["!=", 2]},
				fields=["name", "deadline_date", "deadline_status"]
			)
			
			stats = {
				"total": len(documents),
				"on_time": 0,
				"approaching": 0,
				"overdue": 0,
				"avg_days": 0
			}
			
			total_days = 0
			valid_deadlines = 0
			
			for doc in documents:
				if doc.deadline_date:
					status_info = get_deadline_status(doc.deadline_date)
					
					if status_info["status"] == "On Time":
						stats["on_time"] += 1
					elif status_info["status"] in ["Approaching Deadline", "Due Today"]:
						stats["approaching"] += 1
					elif status_info["status"] == "Overdue":
						stats["overdue"] += 1
					
					if status_info["days_remaining"] is not None:
						total_days += status_info["days_remaining"]
						valid_deadlines += 1
			
			if valid_deadlines > 0:
				stats["avg_days"] = total_days / valid_deadlines
			
			return stats
		
		except Exception as e:
			frappe.log_error(f"Error getting deadline statistics for {doctype}: {str(e)}")
			return {"total": 0, "on_time": 0, "approaching": 0, "overdue": 0, "avg_days": 0}
	
	def _generate_deadline_alerts(self):
		"""Generate alerts for critical deadline situations"""
		try:
			# Find overdue documents
			overdue_docs = self._find_overdue_documents()
			
			# Find approaching deadlines
			approaching_docs = self._find_approaching_deadlines()
			
			# Create system alerts
			if overdue_docs:
				self._create_system_alert("Overdue Documents", overdue_docs)
			
			if approaching_docs:
				self._create_system_alert("Approaching Deadlines", approaching_docs)
		
		except Exception as e:
			frappe.log_error(f"Error generating deadline alerts: {str(e)}")
	
	def _find_overdue_documents(self):
		"""Find all overdue documents"""
		overdue_docs = []
		
		for doctype in self.tracked_doctypes:
			try:
				docs = frappe.get_all(
					doctype,
					filters={
						"docstatus": ["!=", 2],
						"deadline_date": ["<", nowdate()],
						"deadline_status": "Overdue"
					},
					fields=["name", "deadline_date", "escalation_level"]
				)
				
				for doc in docs:
					overdue_docs.append({
						"doctype": doctype,
						"name": doc.name,
						"deadline_date": doc.deadline_date,
						"escalation_level": doc.get("escalation_level", 0)
					})
			
			except Exception as e:
				frappe.log_error(f"Error finding overdue documents for {doctype}: {str(e)}")
		
		return overdue_docs
	
	def _find_approaching_deadlines(self):
		"""Find documents with approaching deadlines (within 3 days)"""
		approaching_docs = []
		threshold_date = add_days(nowdate(), 3)
		
		for doctype in self.tracked_doctypes:
			try:
				docs = frappe.get_all(
					doctype,
					filters={
						"docstatus": ["!=", 2],
						"deadline_date": ["<=", threshold_date],
						"deadline_date": [">=", nowdate()],
						"deadline_status": ["in", ["Approaching Deadline", "Due Today"]]
					},
					fields=["name", "deadline_date", "days_to_deadline"]
				)
				
				for doc in docs:
					approaching_docs.append({
						"doctype": doctype,
						"name": doc.name,
						"deadline_date": doc.deadline_date,
						"days_remaining": doc.get("days_to_deadline", 0)
					})
			
			except Exception as e:
				frappe.log_error(f"Error finding approaching deadlines for {doctype}: {str(e)}")
		
		return approaching_docs
	
	def _create_system_alert(self, alert_type, documents):
		"""Create system alert for deadline issues"""
		try:
			alert_content = f"{alert_type}: {len(documents)} documents require attention\n\n"
			
			for doc in documents[:10]:  # Limit to first 10 for readability
				alert_content += f"- {doc['doctype']}: {doc['name']} (Deadline: {doc['deadline_date']})\n"
			
			if len(documents) > 10:
				alert_content += f"\n... and {len(documents) - 10} more documents"
			
			# Create notification log entry
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Deadline Alert: {alert_type}",
				"email_content": alert_content,
				"for_user": "Administrator",
				"type": "Alert",
				"document_type": "Deadline Tracking",
				"read": 0
			}).insert(ignore_permissions=True)
		
		except Exception as e:
			frappe.log_error(f"Error creating system alert: {str(e)}")


# Scheduled job functions
def run_deadline_monitoring():
	"""Scheduled job to run deadline monitoring"""
	tracker = DeadlineTracker()
	tracker.run_deadline_monitoring()


def run_hourly_deadline_check():
	"""Hourly check for critical deadlines"""
	try:
		tracker = DeadlineTracker()
		
		# Quick check for documents due today or overdue
		critical_docs = []
		
		for doctype in tracker.tracked_doctypes:
			docs = frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],
					"deadline_date": ["<=", nowdate()],
					"deadline_status": ["in", ["Due Today", "Overdue"]]
				},
				fields=["name", "deadline_date"]
			)
			
			critical_docs.extend([{"doctype": doctype, **doc} for doc in docs])
		
		if critical_docs:
			tracker._create_system_alert("Critical Deadlines", critical_docs)
	
	except Exception as e:
		frappe.log_error(f"Error in hourly deadline check: {str(e)}")


# API endpoints
@frappe.whitelist()
def get_deadline_dashboard_data():
	"""API endpoint to get deadline dashboard data"""
	try:
		tracker = DeadlineTracker()
		dashboard_data = {}
		
		for doctype in tracker.tracked_doctypes:
			stats = tracker._get_deadline_statistics(doctype)
			dashboard_data[doctype] = stats
		
		return dashboard_data
	
	except Exception as e:
		frappe.log_error(f"Error getting deadline dashboard data: {str(e)}")
		return {}


@frappe.whitelist()
def force_deadline_update(doctype, name):
	"""API endpoint to force deadline update for a specific document"""
	try:
		tracker = DeadlineTracker()
		doc = frappe.get_doc(doctype, name)
		
		success = tracker._update_document_deadline_status(doc)
		tracker._update_escalation_level(doc)
		
		return {"success": success, "message": "Deadline updated successfully" if success else "No updates needed"}
	
	except Exception as e:
		frappe.log_error(f"Error forcing deadline update: {str(e)}")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_document_deadline_history(doctype, name):
	"""API endpoint to get deadline history for a specific document"""
	try:
		# Get comment history related to deadlines
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": doctype,
				"reference_name": name,
				"content": ["like", "%deadline%"]
			},
			fields=["content", "creation", "comment_by"],
			order_by="creation desc"
		)
		
		return comments
	
	except Exception as e:
		frappe.log_error(f"Error getting deadline history: {str(e)}")
		return []