# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeProjectAllocation(Document):
	def before_save(self):
		calculate_total_percentage(self)



def calculate_total_percentage(self):
	total_percentage = 0
	for row in self.employee_project_allocation_details:
		total_percentage += row.percentage

	if total_percentage > 100:
		frappe.throw("Total percentage cannot exceed 100%")
	self.total_percentage = total_percentage
