# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, getdate, add_days
from wt_operations.wt_operations.deadline_tracker import DeadlineTracker
from wt_operations.wt_operations.escalation_manager import EscalationManager
import json


def get_context(context):
	"""Get context for deadline dashboard page"""
	context.no_cache = 1
	
	try:
		# Get deadline statistics
		context.deadline_stats = get_deadline_statistics()
		
		# Get escalation data
		context.escalation_data = get_escalation_data()
		
		# Get recent deadline changes
		context.recent_changes = get_recent_deadline_changes()
		
		# Get overdue documents
		context.overdue_documents = get_overdue_documents()
		
		# Get approaching deadlines
		context.approaching_deadlines = get_approaching_deadlines()
		
		# Get performance metrics
		context.performance_metrics = get_performance_metrics()
		
	except Exception as e:
		frappe.log_error(f"Error getting deadline dashboard context: {str(e)}")
		context.error = str(e)


def get_deadline_statistics():
	"""Get deadline statistics for all document types"""
	try:
		tracker = DeadlineTracker()
		stats = {}
		
		for doctype in tracker.tracked_doctypes:
			doctype_stats = tracker._get_deadline_statistics(doctype)
			stats[doctype] = doctype_stats
		
		# Calculate overall statistics
		overall = {
			"total": sum(s["total"] for s in stats.values()),
			"on_time": sum(s["on_time"] for s in stats.values()),
			"approaching": sum(s["approaching"] for s in stats.values()),
			"overdue": sum(s["overdue"] for s in stats.values())
		}
		
		if overall["total"] > 0:
			overall["on_time_percentage"] = (overall["on_time"] / overall["total"]) * 100
			overall["overdue_percentage"] = (overall["overdue"] / overall["total"]) * 100
		else:
			overall["on_time_percentage"] = 0
			overall["overdue_percentage"] = 0
		
		stats["overall"] = overall
		return stats
	
	except Exception as e:
		frappe.log_error(f"Error getting deadline statistics: {str(e)}")
		return {}


def get_escalation_data():
	"""Get escalation data for dashboard"""
	try:
		manager = EscalationManager()
		escalation_data = {}
		
		for doctype in manager.tracked_doctypes:
			escalated_docs = frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],
					"escalation_level": [">", 0]
				},
				fields=["name", "escalation_level", "deadline_date", "last_escalation_date"]
			)
			
			level_counts = {}
			for doc in escalated_docs:
				level = doc.escalation_level
				if level not in level_counts:
					level_counts[level] = 0
				level_counts[level] += 1
			
			escalation_data[doctype] = {
				"total_escalated": len(escalated_docs),
				"level_breakdown": level_counts,
				"documents": escalated_docs
			}
		
		return escalation_data
	
	except Exception as e:
		frappe.log_error(f"Error getting escalation data: {str(e)}")
		return {}


def get_recent_deadline_changes():
	"""Get recent deadline-related changes"""
	try:
		# Get recent comments related to deadlines and escalations
		comments = frappe.get_all(
			"Comment",
			filters={
				"creation": [">=", add_days(nowdate(), -7)],
				"content": ["like", "%deadline%"]
			},
			fields=["reference_doctype", "reference_name", "content", "creation", "comment_by"],
			order_by="creation desc",
			limit=20
		)
		
		return comments
	
	except Exception as e:
		frappe.log_error(f"Error getting recent deadline changes: {str(e)}")
		return []


def get_overdue_documents():
	"""Get all overdue documents"""
	try:
		overdue_docs = []
		
		tracked_doctypes = [
			"WWTP Technical Questionnaire",
			"Site Visit Request", 
			"Site Visit",
			"Water Sample",
			"Lab Test Result",
			"WWTP Technical Proposal",
			"Customer Proposal"
		]
		
		for doctype in tracked_doctypes:
			docs = frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],
					"deadline_date": ["<", nowdate()],
					"deadline_status": "Overdue"
				},
				fields=["name", "deadline_date", "escalation_level", "assigned_to", "workflow_state"],
				order_by="deadline_date asc"
			)
			
			for doc in docs:
				doc["doctype"] = doctype
				doc["days_overdue"] = (getdate(nowdate()) - getdate(doc.deadline_date)).days
				overdue_docs.append(doc)
		
		# Sort by days overdue (most overdue first)
		overdue_docs.sort(key=lambda x: x["days_overdue"], reverse=True)
		
		return overdue_docs[:50]  # Limit to 50 most overdue
	
	except Exception as e:
		frappe.log_error(f"Error getting overdue documents: {str(e)}")
		return []


def get_approaching_deadlines():
	"""Get documents with approaching deadlines"""
	try:
		approaching_docs = []
		threshold_date = add_days(nowdate(), 3)
		
		tracked_doctypes = [
			"WWTP Technical Questionnaire",
			"Site Visit Request", 
			"Site Visit",
			"Water Sample",
			"Lab Test Result",
			"WWTP Technical Proposal",
			"Customer Proposal"
		]
		
		for doctype in tracked_doctypes:
			docs = frappe.get_all(
				doctype,
				filters={
					"docstatus": ["!=", 2],
					"deadline_date": ["<=", threshold_date],
					"deadline_date": [">=", nowdate()],
					"deadline_status": ["in", ["Approaching Deadline", "Due Today"]]
				},
				fields=["name", "deadline_date", "assigned_to", "workflow_state"],
				order_by="deadline_date asc"
			)
			
			for doc in docs:
				doc["doctype"] = doctype
				doc["days_remaining"] = (getdate(doc.deadline_date) - getdate(nowdate())).days
				approaching_docs.append(doc)
		
		return approaching_docs[:30]  # Limit to 30 most urgent
	
	except Exception as e:
		frappe.log_error(f"Error getting approaching deadlines: {str(e)}")
		return []


def get_performance_metrics():
	"""Get performance metrics for the dashboard"""
	try:
		# Get deadline history for the last 30 days
		history = frappe.get_all(
			"Deadline History",
			filters={
				"tracking_date": [">=", add_days(nowdate(), -30)]
			},
			fields=["document_type", "tracking_date", "performance_score", "total_documents", 
					"on_time_count", "overdue_count"],
			order_by="tracking_date desc"
		)
		
		# Calculate average performance by document type
		performance_by_type = {}
		for record in history:
			doctype = record.document_type
			if doctype not in performance_by_type:
				performance_by_type[doctype] = {
					"scores": [],
					"total_docs": 0,
					"on_time_total": 0,
					"overdue_total": 0
				}
			
			performance_by_type[doctype]["scores"].append(record.performance_score or 0)
			performance_by_type[doctype]["total_docs"] += record.total_documents or 0
			performance_by_type[doctype]["on_time_total"] += record.on_time_count or 0
			performance_by_type[doctype]["overdue_total"] += record.overdue_count or 0
		
		# Calculate averages
		for doctype, data in performance_by_type.items():
			if data["scores"]:
				data["avg_performance"] = sum(data["scores"]) / len(data["scores"])
			else:
				data["avg_performance"] = 0
			
			if data["total_docs"] > 0:
				data["on_time_rate"] = (data["on_time_total"] / data["total_docs"]) * 100
				data["overdue_rate"] = (data["overdue_total"] / data["total_docs"]) * 100
			else:
				data["on_time_rate"] = 0
				data["overdue_rate"] = 0
		
		return performance_by_type
	
	except Exception as e:
		frappe.log_error(f"Error getting performance metrics: {str(e)}")
		return {}


@frappe.whitelist()
def get_dashboard_data():
	"""API endpoint to get dashboard data"""
	try:
		return {
			"deadline_stats": get_deadline_statistics(),
			"escalation_data": get_escalation_data(),
			"overdue_documents": get_overdue_documents(),
			"approaching_deadlines": get_approaching_deadlines(),
			"performance_metrics": get_performance_metrics()
		}
	
	except Exception as e:
		frappe.log_error(f"Error getting dashboard data: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def refresh_deadline_data():
	"""API endpoint to refresh deadline data"""
	try:
		# Run deadline monitoring
		tracker = DeadlineTracker()
		tracker.run_deadline_monitoring()
		
		return {"success": True, "message": "Deadline data refreshed successfully"}
	
	except Exception as e:
		frappe.log_error(f"Error refreshing deadline data: {str(e)}")
		return {"success": False, "message": str(e)}