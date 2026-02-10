# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OperationManpowerCosting(Document):
	def before_save(self):
		update_daily_operation_report_references(self)
		set_manpower_costing_values(self)
		


	pass

def set_manpower_costing_values(self):
	total_man_power_cost = 0
	for employee in self.operation_manpower_costing_details:
		if employee.salary > 0:
			total_man_power_cost += employee.salary
	self.total_man_power_cost = total_man_power_cost

	self.manpower_cost_per_day = total_man_power_cost / 30
	self.manpower_cost_per_m3 = total_man_power_cost / self.waste_water_treated_volume
	
def update_daily_operation_report_references(self):
	if self.project_unit_assignment and self.project_unit:
		# Update all Daily Operation Reports linked to this PUA
		daily_reports = frappe.get_all('Daily Operation Report', 
								 filters={'unit_assignment_record': self.project_unit_assignment,'docstatus': 1,'date': ['between', [self.start_date, self.end_date]]}, 
								 fields=['name as daily_operation_report','date','waste_water_treated_volume'])
		
		self.daily_operation_report_references = []  # Clear existing references
		print(daily_reports,"Daily reports linked to PUA:", self.project_unit_assignment)
		waste_water_treated_volume = 0
		if len(daily_reports) > 0:
			for daily_report in daily_reports:
				self.append("daily_operation_report_references", {
					'daily_operation_report': daily_report.daily_operation_report,
					'date': daily_report.date,
					'waste_water_treated_volume': daily_report.waste_water_treated_volume
				})
				waste_water_treated_volume += daily_report.waste_water_treated_volume
			self.waste_water_treated_volume = waste_water_treated_volume
			