# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import nowdate, add_days, getdate
from .deadline_engine import DeadlineCalculationEngine, get_deadline_status
from .deadline_tracker import DeadlineTracker
from .escalation_manager import EscalationManager


class TestDeadlineManagement(unittest.TestCase):
	"""Test cases for deadline management system"""
	
	def setUp(self):
		"""Set up test data"""
		self.engine = DeadlineCalculationEngine()
		self.tracker = DeadlineTracker()
		self.escalation_manager = EscalationManager()
		
		# Create test deadline configuration
		self.create_test_deadline_config()
	
	def create_test_deadline_config(self):
		"""Create test deadline configuration"""
		if not frappe.db.exists("Deadline Configuration", {"document_type": "Site Visit Request"}):
			config = frappe.get_doc({
				"doctype": "Deadline Configuration",
				"document_type": "Site Visit Request",
				"default_deadline_days": 3,
				"business_days_only": 1,
				"is_active": 1,
				"escalation_rules": [
					{
						"days_overdue": 1,
						"escalation_level": 1,
						"escalation_action": "Email Notification",
						"notify_roles": "Site Manager"
					},
					{
						"days_overdue": 3,
						"escalation_level": 2,
						"escalation_action": "Manager Notification",
						"notify_roles": "Operations Manager"
					}
				],
				"notification_schedule": [
					{
						"days_before_deadline": 1,
						"notification_type": "Email",
						"recipients": "Site Manager",
						"is_active": 1
					}
				]
			})
			config.insert(ignore_permissions=True)
	
	def test_deadline_calculation_engine(self):
		"""Test deadline calculation engine"""
		
		# Test standard deadline calculation
		result = self.engine.calculate_deadline(
			document_type="Site Visit Request",
			start_date=nowdate()
		)
		
		self.assertIsNotNone(result["deadline_date"])
		self.assertEqual(result["calculation_method"], "Standard Configuration")
		
		# Test manual override
		override_date = add_days(nowdate(), 5)
		result = self.engine.calculate_deadline(
			document_type="Site Visit Request",
			manual_override=override_date
		)
		
		self.assertEqual(result["deadline_date"], override_date)
		self.assertEqual(result["calculation_method"], "Manual Override")
	
	def test_deadline_status_calculation(self):
		"""Test deadline status calculation"""
		
		# Test on-time status
		future_date = add_days(nowdate(), 5)
		status = get_deadline_status(future_date)
		self.assertEqual(status["status"], "On Time")
		self.assertEqual(status["urgency_level"], "low")
		
		# Test approaching deadline
		approaching_date = add_days(nowdate(), 1)
		status = get_deadline_status(approaching_date)
		self.assertEqual(status["status"], "Approaching Deadline")
		self.assertEqual(status["urgency_level"], "medium")
		
		# Test overdue status
		past_date = add_days(nowdate(), -2)
		status = get_deadline_status(past_date)
		self.assertEqual(status["status"], "Overdue")
		self.assertEqual(status["urgency_level"], "critical")
	
	def test_business_days_calculation(self):
		"""Test business days calculation"""
		
		# Test business days calculation
		start_date = "2025-10-27"  # Monday
		result = self.engine._add_business_days(start_date, 3)
		
		# Should be Thursday (3 business days later)
		expected_date = getdate("2025-10-30")
		self.assertEqual(result, expected_date)
	
	def test_escalation_level_calculation(self):
		"""Test escalation level calculation"""
		
		config = frappe.get_doc("Deadline Configuration", {"document_type": "Site Visit Request"})
		
		# Test no escalation (not overdue)
		level = config.get_escalation_level(add_days(nowdate(), 1))
		self.assertEqual(level, 0)
		
		# Test level 1 escalation (1 day overdue)
		level = config.get_escalation_level(add_days(nowdate(), -1))
		self.assertEqual(level, 1)
		
		# Test level 2 escalation (3 days overdue)
		level = config.get_escalation_level(add_days(nowdate(), -3))
		self.assertEqual(level, 2)
	
	def test_bulk_deadline_calculation(self):
		"""Test bulk deadline calculation"""
		
		documents = [
			{"doctype": "Site Visit Request", "name": "test-1"},
			{"doctype": "Site Visit Request", "name": "test-2", "start_date": add_days(nowdate(), -1)}
		]
		
		results = self.engine.bulk_calculate_deadlines(documents)
		
		self.assertEqual(len(results), 2)
		self.assertIn("Site Visit Request::test-1", results)
		self.assertIn("Site Visit Request::test-2", results)
	
	def test_deadline_history_creation(self):
		"""Test deadline history creation"""
		
		# This would require actual documents to test properly
		# For now, just test that the method doesn't crash
		try:
			stats = self.tracker._get_deadline_statistics("Site Visit Request")
			self.assertIsInstance(stats, dict)
			self.assertIn("total", stats)
			self.assertIn("on_time", stats)
			self.assertIn("approaching", stats)
			self.assertIn("overdue", stats)
		except Exception as e:
			self.fail(f"Deadline statistics calculation failed: {str(e)}")
	
	def test_escalation_manager_initialization(self):
		"""Test escalation manager initialization"""
		
		self.assertIsInstance(self.escalation_manager.tracked_doctypes, list)
		self.assertIn("Site Visit Request", self.escalation_manager.tracked_doctypes)
	
	def test_deadline_configuration_validation(self):
		"""Test deadline configuration validation"""
		
		# Test valid configuration
		config = frappe.get_doc("Deadline Configuration", {"document_type": "Site Visit Request"})
		config.validate()  # Should not raise an exception
		
		# Test invalid configuration (negative deadline days)
		config.default_deadline_days = -1
		with self.assertRaises(frappe.ValidationError):
			config.validate()
	
	def tearDown(self):
		"""Clean up test data"""
		# Clean up test deadline configuration
		if frappe.db.exists("Deadline Configuration", {"document_type": "Site Visit Request"}):
			frappe.delete_doc("Deadline Configuration", 
				frappe.db.get_value("Deadline Configuration", {"document_type": "Site Visit Request"}, "name"),
				ignore_permissions=True)


def run_deadline_management_tests():
	"""Run all deadline management tests"""
	try:
		# Create test suite
		suite = unittest.TestLoader().loadTestsFromTestCase(TestDeadlineManagement)
		
		# Run tests
		runner = unittest.TextTestRunner(verbosity=2)
		result = runner.run(suite)
		
		# Return results
		return {
			"tests_run": result.testsRun,
			"failures": len(result.failures),
			"errors": len(result.errors),
			"success": result.wasSuccessful()
		}
	
	except Exception as e:
		frappe.log_error(f"Error running deadline management tests: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def test_deadline_system():
	"""API endpoint to test the deadline management system"""
	return run_deadline_management_tests()


def validate_deadline_system_setup():
	"""Validate that the deadline management system is properly set up"""
	
	validation_results = {
		"deadline_configurations": False,
		"scheduled_jobs": False,
		"doctype_fields": False,
		"dashboard_access": False,
		"api_endpoints": False
	}
	
	try:
		# Check deadline configurations
		configs = frappe.get_all("Deadline Configuration", filters={"is_active": 1})
		validation_results["deadline_configurations"] = len(configs) > 0
		
		# Check scheduled jobs
		jobs = frappe.get_all("Scheduled Job Type", 
			filters={"method": ["like", "%deadline%"]})
		validation_results["scheduled_jobs"] = len(jobs) > 0
		
		# Check if deadline fields exist on doctypes
		sample_doctype = frappe.get_meta("Site Visit Request")
		has_deadline_fields = any(field.fieldname == "deadline_date" for field in sample_doctype.fields)
		validation_results["doctype_fields"] = has_deadline_fields
		
		# Check dashboard access
		try:
			from .www.deadline_dashboard import get_dashboard_data
			dashboard_data = get_dashboard_data()
			validation_results["dashboard_access"] = "error" not in dashboard_data
		except:
			validation_results["dashboard_access"] = False
		
		# Check API endpoints
		try:
			from .deadline_engine import calculate_deadline_api
			validation_results["api_endpoints"] = True
		except:
			validation_results["api_endpoints"] = False
		
		return validation_results
	
	except Exception as e:
		frappe.log_error(f"Error validating deadline system setup: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def validate_system_setup():
	"""API endpoint to validate system setup"""
	return validate_deadline_system_setup()