# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OperationManpowerCosting(Document):
	def before_save(self):
		update_daily_operation_report_references(self)
		set_manpower_costing_values(self)
	
	def validate(self):
		check_between_dates(self)

	@frappe.whitelist()
	def update_costs_on_reports(self):
		print("Updating costs on linked Daily Operation Reports...")
		# This function can be called to update costs on linked Daily Operation Reports if needed
		update_daily_operation_report_costs(self)


	pass

@frappe.whitelist()
def update_daily_operation_report_costs(self):
	try:
		doc = frappe.get_doc("Operation Manpower Costing", self.name)

		if doc.daily_operation_report_references:
			for reference in doc.daily_operation_report_references:
				daily_report = frappe.get_doc('Daily Operation Report', reference.daily_operation_report)

				manpower_cost_per_treated_water = doc.manpower_cost_per_m3 * reference.waste_water_treated_volume

				daily_report.db_set('manpower_cost_per_m3', doc.manpower_cost_per_m3, update_modified=False)
				daily_report.db_set('manpower_cost_per_treated_water', manpower_cost_per_treated_water, update_modified=False)

		frappe.response['message'] = {
			"status": "success",
			"message": "Costs updated on linked Daily Operation Reports successfully."
		}

	except Exception as e:
		frappe.log_error(f"Error in update_daily_operation_report_costs: {str(e)}", "Backend Process")
		frappe.response['message'] = {
			"status": "error",
			"message": str(e)
		}
	# try:
	# 	if self.daily_operation_report_references:
	# 		for reference in self.daily_operation_report_references:
	# 			daily_report = frappe.get_doc('Daily Operation Report', reference.daily_operation_report)
	# 			daily_report.manpower_cost_per_m3 = self.manpower_cost_per_m3
	# 			daily_report.manpower_cost_per_treated_water = self.manpower_cost_per_m3 * reference.waste_water_treated_volume
	# 			daily_report.save()
	# 			daily_report.submit()

	# 	return {
	# 		"status": "success",
	# 		"message": "Costs updated on linked Daily Operation Reports successfully."
	# 	}

	# except Exception as e:
	# 	frappe.log_error(f"Error in process_data: {str(e)}", "Backend Process")
	# 	return {
	# 		"status": "error",
	# 		"message": str(e)
	# 	}


def check_between_dates(self):
	if self.start_date and self.end_date:
		if self.start_date > self.end_date:
			frappe.throw("Start Date cannot be greater than End Date.")

		operation_monpower_costing = frappe.get_all('Operation Manpower Costing', filters={
			'project_unit_assignment': self.project_unit_assignment,
			'start_date': ['<=', self.end_date],
			'end_date': ['>=', self.start_date],
			'name': ['!=', self.name]
		}, fields=['name'], limit=1, as_list=True)
		if operation_monpower_costing:
			frappe.throw("Operation Manpower Costing already exists for the selected date range.")

def set_manpower_costing_values(self):
	total_man_power_cost = self.total_man_power_cost if self.total_man_power_cost else 0
	if not self.edit_total_man_power_cost:	 
		if len(self.operation_manpower_costing_details) > 0:
			total_man_power_cost = 0
			for employee in self.operation_manpower_costing_details:
				if employee.salary > 0:
					total_man_power_cost += employee.salary
			self.total_man_power_cost = total_man_power_cost
	
	self.manpower_cost_per_day = total_man_power_cost / 30
	if total_man_power_cost > 0 and self.waste_water_treated_volume > 0:
		self.manpower_cost_per_m3 = total_man_power_cost / self.waste_water_treated_volume
	
def update_daily_operation_report_references(self):
	if self.project_unit_assignment and self.project_unit:
		# Update all Daily Operation Reports linked to this PUA
		# sql = """
		# 	SELECT dor.name as daily_operation_report, dor.date, dor.waste_water_treated_volume
		# 	FROM `tabDaily Operation Report` dor, `tabDaily Operation Report References` dorr, `tabOperation Manpower Costing` omc
		# 	WHERE dorr.parent = omc.name
		# 	AND dorr.daily_operation_report != dor.name -- Exclude already linked reports
		# 	AND dor.name = dorr.daily_operation_report
		# 	AND dor.unit_assignment_record = '{project_unit_assignment}'
		# 	AND dor.docstatus = 1
		# 	AND dor.date >= '{start_date}' AND dor.date <= '{end_date}'
		# """.format(project_unit_assignment=self.project_unit_assignment, start_date=self.start_date, end_date=self.end_date)
		
		# daily_reports = frappe.db.sql(sql,as_dict=True)

		daily_reports = frappe.get_all('Daily Operation Report', 
								 filters={'unit_assignment_record': self.project_unit_assignment,'docstatus': 1,'date': ['between', [self.start_date, self.end_date]]}, 
								 fields=['name as daily_operation_report','date','waste_water_treated_volume'])
		
		self.daily_operation_report_references = []  # Clear existing references
		# print(daily_reports,"Daily reports linked to PUA:", self.project_unit_assignment)
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
			