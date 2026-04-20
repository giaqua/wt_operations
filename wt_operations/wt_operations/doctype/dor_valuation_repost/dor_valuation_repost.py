# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue


class DORValuationRepost(Document):
	def before_save(self):
		daily_operation_reports = get_daily_operation_report_references(self)
		# update_daily_operation_report_costs(self)
		
		# enqueue(
		# 	'wt_operations.wt_operations.doctype.dor_valuation_repost.dor_valuation_repost.update_dor_valuation_rates',
		# 	queue='long',
		# 	timeout=3000,
		# 	dors=dors
   		#  )
		update_dor_valuation_rates(daily_operation_reports)
		self.remarks = set_remarks(daily_operation_reports)
		pass
	pass

def set_remarks(daily_reports):
	html_links = []
	for dor in daily_reports:
		# Create link with additional info
		link = f'<a href="/app/daily-operation-report/{dor.name}" target="_blank">{dor.name}</a>'
		info = f"<span style='color: #666; font-size: 0.9em;'> - Date: {dor.date} | Unit: {dor.unit}</span>"
		html_links.append(f"<div>{link}{info}</div>")

	# Join all links
	if html_links:
		formatted_links = "<div class='dor-list'>" + "".join(html_links) + "</div>"
		# return {
		# 	"success": True,
		# 	"count": len(daily_reports),
		# 	"links_html": formatted_links,
		# 	"dors": daily_reports
		# }
		return formatted_links
	else:
		return {
			"success": True,
			"count": 0,
			"links_html": "<p>No DORs found that need valuation rate updates.</p>"
		}
	if not daily_reports:
		return "No Daily Operation Reports found for the specified criteria."
	else:
		report_names = [report.name for report in daily_reports]
		return f"Updated valuation rates for Daily Operation Reports: {', '.join(report_names)}"



def get_daily_operation_report_references(self):
	if self.project and self.project_unit:
		daily_reports = frappe.get_all('Daily Operation Report', filters={
			'project': self.project,
			'docstatus': 1,
			'date': ['between', [self.from_date, self.to_date]]
		}, fields=['name', 'date', 'unit', 'waste_water_treated_volume'])
		return daily_reports
	

# def update_daily_operation_report_costs(self):
# 	daily_reports = get_daily_operation_report_references(self)
# 	for report in daily_reports:
# 		dor_doc = frappe.get_doc('Daily Operation Report', report.name)
# 		dor_doc.calculate_costs()
# 		dor_doc.save()


def update_dor_valuation_rates(dors):
    """Process batch update"""
    for dor_name in dors:
        try:
            dor = frappe.get_doc("Daily Operation Report", dor_name.name)
            dor.update_chemical_valuation_rates()
            dor.submit()
            # frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error updating {dor_name}: {str(e)}", "Valuation Rate Update")
            frappe.db.rollback()