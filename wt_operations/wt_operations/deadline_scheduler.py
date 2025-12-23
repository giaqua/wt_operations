# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime, add_to_date
from .deadline_tracker import run_deadline_monitoring, run_hourly_deadline_check
from .escalation_manager import run_escalation_check


def setup_deadline_scheduled_jobs():
	"""Setup scheduled jobs for deadline management"""
	
	# Daily deadline monitoring job
	if not frappe.db.exists("Scheduled Job Type", "deadline_monitoring_daily"):
		frappe.get_doc({
			"doctype": "Scheduled Job Type",
			"method": "wt_operations.wt_operations.deadline_tracker.run_deadline_monitoring",
			"frequency": "Daily",
			"cron_format": "0 6 * * *",  # Run at 6 AM daily
			"create_log": 1
		}).insert()
	
	# Hourly deadline check job
	if not frappe.db.exists("Scheduled Job Type", "deadline_check_hourly"):
		frappe.get_doc({
			"doctype": "Scheduled Job Type",
			"method": "wt_operations.wt_operations.deadline_tracker.run_hourly_deadline_check",
			"frequency": "Hourly",
			"cron_format": "0 * * * *",  # Run every hour
			"create_log": 1
		}).insert()
	
	# Escalation check job (every 4 hours)
	if not frappe.db.exists("Scheduled Job Type", "escalation_check"):
		frappe.get_doc({
			"doctype": "Scheduled Job Type",
			"method": "wt_operations.wt_operations.escalation_manager.run_escalation_check",
			"frequency": "Cron",
			"cron_format": "0 */4 * * *",  # Run every 4 hours
			"create_log": 1
		}).insert()


def create_default_deadline_configurations():
	"""Create default deadline configurations for all document types"""
	
	default_configs = [
		{
			"document_type": "WWTP Technical Questionnaire",
			"default_deadline_days": 3,
			"business_days_only": 1,
			"description": "Technical questionnaire completion deadline",
			"escalation_rules": [
				{"days_overdue": 1, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Technical Engineer, Operations Manager"},
				{"days_overdue": 3, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"},
				{"days_overdue": 5, "escalation_level": 3, "escalation_action": "Automatic Reassignment", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 1, "notification_type": "Email", "recipients": "Technical Engineer", "is_active": 1},
				{"days_before_deadline": 0, "notification_type": "Both", "recipients": "Technical Engineer, Operations Manager", "is_active": 1}
			]
		},
		{
			"document_type": "Site Visit Request",
			"default_deadline_days": 3,
			"business_days_only": 1,
			"description": "Site visit request scheduling deadline",
			"escalation_rules": [
				{"days_overdue": 1, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Site Manager"},
				{"days_overdue": 2, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 1, "notification_type": "Email", "recipients": "Site Manager", "is_active": 1}
			]
		},
		{
			"document_type": "Site Visit",
			"default_deadline_days": 7,
			"business_days_only": 1,
			"description": "Site visit completion deadline",
			"escalation_rules": [
				{"days_overdue": 2, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Site Manager"},
				{"days_overdue": 5, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 2, "notification_type": "Email", "recipients": "Site Manager", "is_active": 1},
				{"days_before_deadline": 0, "notification_type": "Both", "recipients": "Site Manager, Operations Manager", "is_active": 1}
			]
		},
		{
			"document_type": "Water Sample",
			"default_deadline_days": 2,
			"business_days_only": 1,
			"description": "Water sample collection deadline",
			"escalation_rules": [
				{"days_overdue": 1, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Site Manager, Lab Technician"}
			],
			"notification_schedule": [
				{"days_before_deadline": 1, "notification_type": "Email", "recipients": "Site Manager", "is_active": 1}
			]
		},
		{
			"document_type": "Lab Test Result",
			"default_deadline_days": 5,
			"business_days_only": 1,
			"description": "Lab test result completion deadline",
			"escalation_rules": [
				{"days_overdue": 1, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Lab Technician"},
				{"days_overdue": 3, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"},
				{"days_overdue": 5, "escalation_level": 3, "escalation_action": "Automatic Reassignment", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 2, "notification_type": "Email", "recipients": "Lab Technician", "is_active": 1},
				{"days_before_deadline": 0, "notification_type": "Both", "recipients": "Lab Technician, Operations Manager", "is_active": 1}
			]
		},
		{
			"document_type": "WWTP Technical Proposal",
			"default_deadline_days": 10,
			"business_days_only": 1,
			"description": "Technical proposal completion deadline",
			"escalation_rules": [
				{"days_overdue": 2, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Technical Engineer"},
				{"days_overdue": 5, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"},
				{"days_overdue": 8, "escalation_level": 3, "escalation_action": "Automatic Reassignment", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 3, "notification_type": "Email", "recipients": "Technical Engineer", "is_active": 1},
				{"days_before_deadline": 1, "notification_type": "Both", "recipients": "Technical Engineer, Operations Manager", "is_active": 1}
			]
		},
		{
			"document_type": "Customer Proposal",
			"default_deadline_days": 5,
			"business_days_only": 1,
			"description": "Customer proposal completion deadline",
			"escalation_rules": [
				{"days_overdue": 1, "escalation_level": 1, "escalation_action": "Email Notification", "notify_roles": "Sales Manager"},
				{"days_overdue": 3, "escalation_level": 2, "escalation_action": "Manager Notification", "notify_roles": "Operations Manager"}
			],
			"notification_schedule": [
				{"days_before_deadline": 2, "notification_type": "Email", "recipients": "Sales Manager", "is_active": 1},
				{"days_before_deadline": 0, "notification_type": "Both", "recipients": "Sales Manager, Operations Manager", "is_active": 1}
			]
		}
	]
	
	for config_data in default_configs:
		# Check if configuration already exists
		if not frappe.db.exists("Deadline Configuration", {"document_type": config_data["document_type"]}):
			
			# Create the main configuration document
			config_doc = frappe.get_doc({
				"doctype": "Deadline Configuration",
				"document_type": config_data["document_type"],
				"default_deadline_days": config_data["default_deadline_days"],
				"business_days_only": config_data["business_days_only"],
				"description": config_data["description"],
				"is_active": 1
			})
			
			# Add escalation rules
			for rule_data in config_data["escalation_rules"]:
				config_doc.append("escalation_rules", rule_data)
			
			# Add notification schedule
			for notification_data in config_data["notification_schedule"]:
				config_doc.append("notification_schedule", notification_data)
			
			config_doc.insert(ignore_permissions=True)
			frappe.logger().info(f"Created deadline configuration for {config_data['document_type']}")


def initialize_deadline_management():
	"""Initialize the complete deadline management system"""
	try:
		frappe.logger().info("Initializing deadline management system...")
		
		# Setup scheduled jobs
		setup_deadline_scheduled_jobs()
		frappe.logger().info("Scheduled jobs created")
		
		# Create default configurations
		create_default_deadline_configurations()
		frappe.logger().info("Default deadline configurations created")
		
		# Run initial deadline monitoring
		run_deadline_monitoring()
		frappe.logger().info("Initial deadline monitoring completed")
		
		frappe.logger().info("Deadline management system initialized successfully")
		
	except Exception as e:
		frappe.log_error(f"Error initializing deadline management system: {str(e)}")
		raise


@frappe.whitelist()
def setup_deadline_system():
	"""API endpoint to setup the deadline management system"""
	try:
		initialize_deadline_management()
		return {"success": True, "message": "Deadline management system setup completed successfully"}
	
	except Exception as e:
		frappe.log_error(f"Error setting up deadline system: {str(e)}")
		return {"success": False, "message": str(e)}


def execute():
	"""Patch function to initialize deadline management system"""
	initialize_deadline_management()