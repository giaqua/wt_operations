# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WorkflowTracking(Document):
	def validate(self):
		"""Validate workflow tracking data"""
		self.update_completion_percentage()
		self.update_current_stage()
	
	def update_completion_percentage(self):
		"""Calculate completion percentage based on stage history"""
		if not self.stage_history:
			self.completion_percentage = 0
			return
		
		# Define workflow stages and their weights
		stage_weights = {
			"Technical Questionnaire": 10,
			"Site Visit Request": 20,
			"Site Visit": 30,
			"Water Sample": 40,
			"Lab Test Result": 60,
			"Technical Proposal": 80,
			"Customer Proposal": 100
		}
		
		completed_stages = [stage.stage_name for stage in self.stage_history if stage.status == "Completed"]
		total_weight = sum(stage_weights.get(stage, 0) for stage in completed_stages)
		self.completion_percentage = min(total_weight, 100)
	
	def update_current_stage(self):
		"""Update current stage based on latest stage history"""
		if not self.stage_history:
			self.current_stage = "Not Started"
			return
		
		# Get the latest stage that is in progress or completed
		latest_stage = None
		# Use getdate to normalize dates for comparison (handles both date objects and strings)
		default_date = frappe.utils.getdate("1900-01-01")
		for stage in sorted(self.stage_history, key=lambda x: frappe.utils.getdate(x.start_date) if x.start_date else default_date, reverse=True):
			if stage.status in ["In Progress", "Completed"]:
				latest_stage = stage
				break
		
		if latest_stage:
			self.current_stage = latest_stage.stage_name
		else:
			self.current_stage = "Not Started"
	
	def add_stage_history(self, stage_name, status, document_name=None):
		"""Add a new stage history entry"""
		stage_entry = self.append("stage_history", {})
		stage_entry.stage_name = stage_name
		stage_entry.status = status
		stage_entry.start_date = frappe.utils.nowdate()
		if document_name:
			stage_entry.document_name = document_name
		
		self.save()
	
	def add_bottleneck(self, stage_name, description, severity="Medium"):
		"""Add a bottleneck entry"""
		bottleneck = self.append("bottlenecks", {})
		bottleneck.stage_name = stage_name
		bottleneck.description = description
		bottleneck.severity = severity
		bottleneck.identified_date = frappe.utils.nowdate()
		
		self.save()