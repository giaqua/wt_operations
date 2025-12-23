# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DeadlineHistory(Document):
	def validate(self):
		"""Validate deadline history entry"""
		self.calculate_performance_score()
	
	def calculate_performance_score(self):
		"""Calculate performance score based on deadline adherence"""
		if self.total_documents > 0:
			# Performance score = (on_time + 0.5 * approaching) / total * 100
			score = (self.on_time_count + (0.5 * self.approaching_deadline_count)) / self.total_documents * 100
			self.performance_score = min(100, max(0, score))  # Ensure between 0-100
		else:
			self.performance_score = 0