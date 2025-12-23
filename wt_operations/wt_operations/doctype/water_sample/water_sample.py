# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class WaterSample(Document):
	def validate(self):
		"""Validate the water sample document"""
		self.set_title()
		self.validate_dates()
		self.set_defaults()
		self.validate_sample_data()
	
	def set_title(self):
		"""Set the title based on sample type and date"""
		if self.sample_type and self.date_collected:
			self.title = f"{self.sample_type} Sample - {self.date_collected}"
		elif self.sample_type:
			self.title = f"{self.sample_type} Sample"
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.analysis_completed and self.date_collected:
			if self.analysis_completed < self.date_collected:
				frappe.throw(_("Analysis completed date cannot be before collection date"))
	
	def set_defaults(self):
		"""Set default values"""
		if not self.compliance_status:
			self.compliance_status = "Pending"
		
		if not self.chain_of_custody:
			self.chain_of_custody = 0
	
	def validate_sample_data(self):
		"""Validate sample collection data"""
		if self.sample_type == "Effluent" and not self.ph:
			frappe.msgprint(_("pH is typically required for effluent samples"), alert=True)
		
		if self.preservation_method == "Chemical Preservation" and not self.preservation_chemicals:
			frappe.msgprint(_("Please specify preservation chemicals"), alert=True)
	
	def on_submit(self):
		"""Actions when document is submitted"""
		self.update_stp_questionnaire()
	
	def update_stp_questionnaire(self):
		"""Update the related WWTP Technical Questionnaire"""
		if self.wwtp_technical_questionnaire:
			stp_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
			if stp_doc.sample_collection_required:
				frappe.msgprint(
					_("Sample collection completed for WWTP Technical Questionnaire: {0}").format(
						self.wwtp_technical_questionnaire
					),
					alert=True
				)
	
	@frappe.whitelist()
	def get_stp_details(self):
		"""Get WWTP Technical Questionnaire details"""
		if self.wwtp_technical_questionnaire:
			stp_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
			return {
				"lead": stp_doc.lead,
				"opportunity": stp_doc.opportunity,
				"wastewater_generator_type": stp_doc.wastewater_generator_type,
				"capacity": stp_doc.capacity,
				"location": stp_doc.location_of_the_wwtp_needed
			}
		return {}
	
	@frappe.whitelist()
	def auto_fill_from_stp(self):
		"""Auto-fill fields from WWTP Technical Questionnaire"""
		stp_details = self.get_stp_details()
		if stp_details:
			self.lead = stp_details.get("lead")
			self.opportunity = stp_details.get("opportunity")
			self.sample_location = stp_details.get("location")
			
			# Set sample type based on STP requirements
			if stp_details.get("wastewater_generator_type"):
				generator_type = stp_details.get("wastewater_generator_type")
				if "Industrial" in generator_type:
					self.sample_type = "Effluent"
				else:
					self.sample_type = "Influent"
	
	@frappe.whitelist()
	def calculate_compliance(self):
		"""Calculate compliance status based on results"""
		if not self.results_available:
			return
		
		# Basic compliance check for effluent samples
		if self.sample_type == "Effluent":
			non_compliant = []
			
			if self.ph and (self.ph < 6.0 or self.ph > 9.0):
				non_compliant.append("pH")
			
			if self.tss and self.tss > 100:
				non_compliant.append("TSS")
			
			if self.bod5 and self.bod5 > 30:
				non_compliant.append("BOD5")
			
			if non_compliant:
				self.compliance_status = "Non-Compliant"
				frappe.msgprint(
					_("Non-compliant parameters: {0}").format(", ".join(non_compliant)),
					alert=True
				)
			else:
				self.compliance_status = "Compliant"
	
	@frappe.whitelist()
	def get_sample_summary(self):
		"""Get a summary of the sample"""
		summary = {
			"sample_id": self.name,
			"type": self.sample_type,
			"location": self.sample_location,
			"date": self.date_collected,
			"compliance": self.compliance_status
		}
		
		if self.results_available:
			summary["key_results"] = {
				"pH": self.ph,
				"TSS": self.tss,
				"BOD5": self.bod5,
				"COD": self.cod
			}
		
		return summary