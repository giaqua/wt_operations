# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_to_date, getdate, nowdate


class DeadlineConfiguration(Document):
	def validate(self):
		"""Validate deadline configuration"""
		self.validate_deadline_days()
		self.validate_escalation_rules()
	
	def validate_deadline_days(self):
		"""Validate that deadline days is positive"""
		if self.default_deadline_days <= 0:
			frappe.throw("Default deadline days must be greater than 0")
	
	def validate_escalation_rules(self):
		"""Validate escalation rules"""
		if self.escalation_rules:
			for rule in self.escalation_rules:
				if rule.days_overdue <= 0:
					frappe.throw("Days overdue must be greater than 0 for escalation rules")
	
	def calculate_deadline(self, start_date=None):
		"""Calculate deadline based on configuration"""
		if not start_date:
			start_date = nowdate()
		
		if self.business_days_only:
			# Add business days only
			deadline = add_to_date(start_date, days=self.default_deadline_days, as_string=True)
		else:
			# Add calendar days
			deadline = add_days(start_date, self.default_deadline_days)
		
		return deadline
	
	def get_escalation_level(self, deadline_date, current_date=None):
		"""Get escalation level based on how overdue the document is"""
		if not current_date:
			current_date = nowdate()
		
		deadline = getdate(deadline_date)
		current = getdate(current_date)
		
		if current <= deadline:
			return 0  # Not overdue
		
		days_overdue = (current - deadline).days
		
		escalation_level = 0
		if self.escalation_rules:
			for rule in sorted(self.escalation_rules, key=lambda x: x.days_overdue):
				if days_overdue >= rule.days_overdue:
					escalation_level = rule.escalation_level
		
		return escalation_level
	
	def get_notification_schedule(self):
		"""Get notification schedule for this document type"""
		schedule = []
		if self.notification_schedule:
			for notification in self.notification_schedule:
				schedule.append({
					'days_before': notification.days_before_deadline,
					'notification_type': notification.notification_type,
					'recipients': notification.recipients
				})
		return schedule