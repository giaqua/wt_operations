# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, add_to_date, getdate, nowdate, get_datetime, cint
from datetime import datetime, timedelta
import json


class DeadlineCalculationEngine:
	"""
	Core engine for calculating deadlines based on document types and business rules.
	Supports configurable deadline rules, business days calculation, and dependency-based deadlines.
	"""
	
	def __init__(self):
		self.deadline_configs = self._load_deadline_configurations()
		self.dependency_map = self._get_dependency_map()
	
	def _load_deadline_configurations(self):
		"""Load all active deadline configurations"""
		configs = {}
		deadline_configs = frappe.get_all(
			"Deadline Configuration",
			filters={"is_active": 1},
			fields=["name", "document_type", "default_deadline_days", "business_days_only"]
		)
		
		for config in deadline_configs:
			configs[config.document_type] = frappe.get_doc("Deadline Configuration", config.name)
		
		return configs
	
	def _get_dependency_map(self):
		"""Define document dependencies for deadline calculation"""
		return {
			"Site Visit Request": ["WWTP Technical Questionnaire"],
			"Site Visit": ["Site Visit Request"],
			"Water Sample": ["Site Visit"],
			"Lab Test Result": ["Water Sample"],
			"WWTP Technical Proposal": ["Lab Test Result"],
			"Customer Proposal": ["WWTP Technical Proposal"]
		}
	
	def calculate_deadline(self, document_type, start_date=None, parent_document=None, manual_override=None):
		"""
		Calculate deadline for a document based on type and dependencies
		
		Args:
			document_type: Type of document
			start_date: Start date for calculation (defaults to today)
			parent_document: Parent document for dependency-based calculation
			manual_override: Manual deadline override
		
		Returns:
			dict: Contains deadline_date, calculation_method, and details
		"""
		if manual_override:
			return {
				"deadline_date": manual_override,
				"calculation_method": "Manual Override",
				"details": f"Manually set deadline: {manual_override}"
			}
		
		if not start_date:
			start_date = nowdate()
		
		# Check if we have configuration for this document type
		if document_type not in self.deadline_configs:
			frappe.log_error(f"No deadline configuration found for {document_type}")
			return {
				"deadline_date": add_days(start_date, 7),  # Default 7 days
				"calculation_method": "Default Fallback",
				"details": "No configuration found, using 7-day default"
			}
		
		config = self.deadline_configs[document_type]
		
		# Check for dependency-based calculation
		if parent_document and document_type in self.dependency_map:
			return self._calculate_dependency_based_deadline(
				document_type, parent_document, config
			)
		
		# Standard deadline calculation
		deadline_date = self._calculate_standard_deadline(start_date, config)
		
		return {
			"deadline_date": deadline_date,
			"calculation_method": "Standard Configuration",
			"details": f"Added {config.default_deadline_days} {'business' if config.business_days_only else 'calendar'} days"
		}
	
	def _calculate_standard_deadline(self, start_date, config):
		"""Calculate standard deadline based on configuration"""
		if config.business_days_only:
			return self._add_business_days(start_date, config.default_deadline_days)
		else:
			return add_days(start_date, config.default_deadline_days)
	
	def _calculate_dependency_based_deadline(self, document_type, parent_document, config):
		"""Calculate deadline based on parent document's deadline"""
		try:
			parent_doc = frappe.get_doc(parent_document["doctype"], parent_document["name"])
			parent_deadline = getdate(parent_doc.get("deadline_date"))
			
			if not parent_deadline:
				# If parent has no deadline, calculate from creation date
				parent_deadline = getdate(parent_doc.creation)
			
			# Calculate deadline from parent's deadline
			if config.business_days_only:
				deadline_date = self._add_business_days(parent_deadline, config.default_deadline_days)
			else:
				deadline_date = add_days(parent_deadline, config.default_deadline_days)
			
			return {
				"deadline_date": deadline_date,
				"calculation_method": "Dependency-Based",
				"details": f"Based on {parent_document['doctype']} deadline plus {config.default_deadline_days} days"
			}
		
		except Exception as e:
			frappe.log_error(f"Error in dependency-based deadline calculation: {str(e)}")
			# Fallback to standard calculation
			return {
				"deadline_date": self._calculate_standard_deadline(nowdate(), config),
				"calculation_method": "Fallback Standard",
				"details": f"Dependency calculation failed, using standard: {str(e)}"
			}
	
	def _add_business_days(self, start_date, days):
		"""Add business days (excluding weekends)"""
		current_date = getdate(start_date)
		days_added = 0
		
		while days_added < days:
			current_date = add_days(current_date, 1)
			# Skip weekends (Saturday=5, Sunday=6)
			if current_date.weekday() < 5:
				days_added += 1
		
		return current_date
	
	def get_deadline_status(self, deadline_date, current_date=None):
		"""
		Get deadline status indicator
		
		Returns:
			dict: Contains status, days_remaining, and urgency_level
		"""
		if not deadline_date:
			return {
				"status": "No Deadline",
				"days_remaining": None,
				"urgency_level": "none"
			}
		
		if not current_date:
			current_date = nowdate()
		
		deadline = getdate(deadline_date)
		current = getdate(current_date)
		
		days_diff = (deadline - current).days
		
		if days_diff > 3:
			status = "On Time"
			urgency_level = "low"
		elif days_diff > 0:
			status = "Approaching Deadline"
			urgency_level = "medium"
		elif days_diff == 0:
			status = "Due Today"
			urgency_level = "high"
		else:
			status = "Overdue"
			urgency_level = "critical"
		
		return {
			"status": status,
			"days_remaining": days_diff,
			"urgency_level": urgency_level
		}
	
	def bulk_calculate_deadlines(self, documents):
		"""
		Calculate deadlines for multiple documents
		
		Args:
			documents: List of dicts with doctype, name, and optional parent_document
		
		Returns:
			dict: Results keyed by document identifier
		"""
		results = {}
		
		for doc_info in documents:
			doc_key = f"{doc_info['doctype']}::{doc_info['name']}"
			
			try:
				result = self.calculate_deadline(
					document_type=doc_info['doctype'],
					start_date=doc_info.get('start_date'),
					parent_document=doc_info.get('parent_document'),
					manual_override=doc_info.get('manual_override')
				)
				results[doc_key] = result
			
			except Exception as e:
				frappe.log_error(f"Error calculating deadline for {doc_key}: {str(e)}")
				results[doc_key] = {
					"deadline_date": add_days(nowdate(), 7),
					"calculation_method": "Error Fallback",
					"details": f"Error occurred: {str(e)}"
				}
		
		return results
	
	def update_document_deadline(self, doctype, name, deadline_info=None, save=True):
		"""
		Update a document's deadline fields
		
		Args:
			doctype: Document type
			name: Document name
			deadline_info: Pre-calculated deadline info (optional)
			save: Whether to save the document
		"""
		try:
			doc = frappe.get_doc(doctype, name)
			
			if not deadline_info:
				deadline_info = self.calculate_deadline(
					document_type=doctype,
					start_date=doc.get('creation') or nowdate()
				)
			
			# Update deadline fields if they exist
			if hasattr(doc, 'deadline_date'):
				doc.deadline_date = deadline_info['deadline_date']
			
			if hasattr(doc, 'deadline_calculation_method'):
				doc.deadline_calculation_method = deadline_info['calculation_method']
			
			if hasattr(doc, 'deadline_calculation_details'):
				doc.deadline_calculation_details = deadline_info['details']
			
			# Update deadline status
			status_info = self.get_deadline_status(deadline_info['deadline_date'])
			if hasattr(doc, 'deadline_status'):
				doc.deadline_status = status_info['status']
			
			if hasattr(doc, 'deadline_urgency_level'):
				doc.deadline_urgency_level = status_info['urgency_level']
			
			if save:
				doc.save(ignore_permissions=True)
			
			return True
		
		except Exception as e:
			frappe.log_error(f"Error updating deadline for {doctype} {name}: {str(e)}")
			return False


# Utility functions for easy access
def calculate_document_deadline(doctype, name, start_date=None, parent_document=None, manual_override=None):
	"""Utility function to calculate deadline for a single document"""
	engine = DeadlineCalculationEngine()
	return engine.calculate_deadline(doctype, start_date, parent_document, manual_override)


def update_document_deadline(doctype, name, save=True):
	"""Utility function to update a document's deadline"""
	engine = DeadlineCalculationEngine()
	return engine.update_document_deadline(doctype, name, save=save)


def get_deadline_status(deadline_date, current_date=None):
	"""Utility function to get deadline status"""
	engine = DeadlineCalculationEngine()
	return engine.get_deadline_status(deadline_date, current_date)


@frappe.whitelist()
def calculate_deadline_api(doctype, start_date=None, parent_doctype=None, parent_name=None, manual_override=None):
	"""API endpoint for calculating deadlines"""
	parent_document = None
	if parent_doctype and parent_name:
		parent_document = {"doctype": parent_doctype, "name": parent_name}
	
	engine = DeadlineCalculationEngine()
	result = engine.calculate_deadline(
		document_type=doctype,
		start_date=start_date,
		parent_document=parent_document,
		manual_override=manual_override
	)
	
	return result


@frappe.whitelist()
def get_deadline_status_api(deadline_date, current_date=None):
	"""API endpoint for getting deadline status"""
	return get_deadline_status(deadline_date, current_date)