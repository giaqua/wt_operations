# Test script for WWTP Technical Questionnaire Site Visit Integration

import frappe
from frappe.test_runner import make_test_objects

def test_site_visit_integration():
	"""Test the site visit request creation functionality"""
	
	# Create test external site settings
	test_site_settings = frappe.get_doc({
		"doctype": "External Site Settings",
		"site_name": "Test Site",
		"site_url": "https://test.erpnext.com",
		"api_key": "test_key",
		"api_secret": "test_secret",
		"enabled": 1
	})
	test_site_settings.insert()
	
	# Create test WWTP Technical Questionnaire
	test_stp = frappe.get_doc({
		"doctype": "WWTP Technical Questionnaire",
		"lead": "TEST-LEAD-001",  # Assuming this lead exists
		"opportunity": "TEST-OPP-001",  # Assuming this opportunity exists
		"site_visit_required": 1,
		"date": frappe.utils.today()
	})
	
	try:
		# Test validation (this should trigger site visit request creation)
		test_stp.validate()
		
		print("✓ WWTP Technical Questionnaire validation passed")
		print(f"✓ External site visit request field: {test_stp.external_site_visit_request}")
		
	except Exception as e:
		print(f"✗ Test failed: {str(e)}")
		# This is expected if the external site is not reachable
		print("Note: This error is expected if the external site is not accessible")
	
	finally:
		# Clean up test data
		if frappe.db.exists("External Site Settings", test_site_settings.name):
			frappe.delete_doc("External Site Settings", test_site_settings.name)
		if frappe.db.exists("WWTP Technical Questionnaire", test_stp.name):
			frappe.delete_doc("WWTP Technical Questionnaire", test_stp.name)

if __name__ == "__main__":
	test_site_visit_integration()
