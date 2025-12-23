# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LabTestTemplate(Document):
	def validate(self):
		"""Validate lab test template data"""
		self.validate_parameters()
		self.validate_equipment()
	
	def validate_parameters(self):
		"""Validate that required parameters are defined"""
		if not self.standard_parameters:
			frappe.throw("At least one test parameter must be defined")
	
	def validate_equipment(self):
		"""Validate equipment requirements"""
		if self.required_equipment:
			for equipment in self.required_equipment:
				if not equipment.equipment_name:
					frappe.throw("Equipment name is required for all equipment entries")
	
	def get_template_parameters(self):
		"""Get list of parameters for this template"""
		return [param.parameter_name for param in self.standard_parameters]
	
	def estimate_completion_time(self):
		"""Estimate completion time based on parameters and equipment"""
		base_time = self.analysis_duration_hours or 24
		
		# Add time based on number of parameters
		parameter_time = len(self.standard_parameters) * 0.5
		
		return base_time + parameter_time