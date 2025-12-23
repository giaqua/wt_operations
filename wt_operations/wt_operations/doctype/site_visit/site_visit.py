# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class SiteVisit(Document):
	def validate(self):
		"""Validate the site visit document"""
		self.set_title()
		self.validate_dates()
		self.set_defaults()
		self.validate_site_data()
	
	def set_title(self):
		"""Set the title based on site name and date"""
		if self.site_name and self.date:
			self.title = f"{self.site_name} - {self.date}"
		elif self.site_name:
			self.title = f"{self.site_name} - Site Visit"
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.follow_up_date and self.date:
			if self.follow_up_date < self.date:
				frappe.throw(_("Follow-up date cannot be before visit date"))
	
	def set_defaults(self):
		"""Set default values"""
		if not self.weather_conditions:
			self.weather_conditions = "Sunny"
		
		if not self.site_accessibility:
			self.site_accessibility = "Good"
		
		if not self.risk_level:
			self.risk_level = "Medium"
	
	def validate_site_data(self):
		"""Validate site-specific data"""
		if self.existing_treatment and not self.treatment_capacity:
			frappe.msgprint(_("Please specify treatment capacity for existing facility"), alert=True)
		
		if self.available_area and self.available_area < 50:
			frappe.msgprint(_("Available area seems very small for STP installation"), alert=True)
	
	def on_submit(self):
		"""Actions when document is submitted"""
		self.update_related_documents()
		self.create_follow_up_tasks()
	
	def update_related_documents(self):
		"""Update related WWTP Technical Questionnaire and Site Visit Request"""
		if self.wwtp_technical_questionnaire:
			stp_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
			frappe.msgprint(
				_("Site visit completed for WWTP Technical Questionnaire: {0}").format(
					self.wwtp_technical_questionnaire
				),
				alert=True
			)
		
		if self.related_site_visit_request:
			# Update SVR status to Completed using db.set_value for submitted docs
			frappe.db.set_value("Site Visit Request", self.related_site_visit_request, "status", "Completed")
			
			# Add entry to SVR's site_visits_table if not exists
			existing_entry = frappe.get_all("Site Visit Tracking Table",
				filters={
					"parent": self.related_site_visit_request,
					"site_visit": self.name
				},
				limit=1
			)
			
			if not existing_entry:
				frappe.get_doc({
					"doctype": "Site Visit Tracking Table",
					"parent": self.related_site_visit_request,
					"parenttype": "Site Visit Request",
					"parentfield": "site_visits_table",
					"site_visit": self.name,
					"visit_date": self.date,
					"visit_status": "Submitted",
					"visit_by": self.visit_by
				}).insert()
			
			frappe.msgprint(
				_("Site Visit Request {0} status updated to Completed").format(
					self.related_site_visit_request
				),
				alert=True
			)
	
	def create_follow_up_tasks(self):
		"""Create follow-up tasks if required"""
		if self.follow_up_required and self.follow_up_date:
			frappe.msgprint(
				_("Follow-up visit scheduled for {0}").format(self.follow_up_date),
				alert=True
			)
	
	@frappe.whitelist()
	def get_stp_details(self):
		"""Get WWTP Technical Questionnaire details"""
		if self.wwtp_technical_questionnaire:
			stp_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
			return {
				"lead": stp_doc.lead,
				"wastewater_generator_type": stp_doc.wastewater_generator_type,
				"capacity": stp_doc.capacity,
				"location": stp_doc.location_of_the_wwtp_needed,
				"daily_flow": stp_doc.daily_flow,
				"site_visit_required": stp_doc.site_visit_required,
				"sample_collection_required": stp_doc.sample_collection_required
			}
		return {}
	
	@frappe.whitelist()
	def auto_fill_from_stp(self):
		"""Auto-fill fields from WWTP Technical Questionnaire"""
		stp_details = self.get_stp_details()
		if stp_details:
			self.site_name = f"STP Site - {stp_details.get('wastewater_generator_type', 'Wastewater Treatment')}"
			self.site_address = stp_details.get("location")
			self.wastewater_source = stp_details.get("wastewater_generator_type")
			
			# Set facility type based on generator type
			generator_type = stp_details.get("wastewater_generator_type", "")
			if "Industrial" in generator_type:
				self.facility_type = "Industrial"
			elif "Domestic" in generator_type:
				self.facility_type = "Residential"
			else:
				self.facility_type = "Mixed Use"
	
	@frappe.whitelist()
	def get_lead_details(self):
		"""Get lead contact details (excluding site location)"""
		if self.lead:
			lead_doc = frappe.get_doc("Lead", self.lead)
			return {
				"contact_person": lead_doc.lead_name,
				"contact_number": lead_doc.mobile_no or lead_doc.phone,
				"email": lead_doc.email_id
				# Note: Site address, city, state, pincode are not returned from lead
			}
		return {}
	
	@frappe.whitelist()
	def auto_fill_contact_details(self):
		"""Auto-fill contact details from lead (excluding site location)"""
		lead_details = self.get_lead_details()
		if lead_details:
			self.contact_person = lead_details.get("contact_person")
			self.contact_number = lead_details.get("contact_number")
			self.email = lead_details.get("email")
			# Note: Site address, city, state, pincode are not auto-filled from lead
	
	@frappe.whitelist()
	def calculate_risk_level(self):
		"""Calculate risk level based on site conditions"""
		risk_factors = []
		
		if self.site_accessibility in ["Poor", "Very Poor"]:
			risk_factors.append("Poor accessibility")
		
		if self.power_availability in ["Not Available", "Needs Assessment"]:
			risk_factors.append("Power issues")
		
		if self.ground_conditions in ["Soft", "Mixed"]:
			risk_factors.append("Ground conditions")
		
		if self.environmental_impact and "high" in self.environmental_impact.lower():
			risk_factors.append("Environmental concerns")
		
		if len(risk_factors) >= 3:
			self.risk_level = "High"
		elif len(risk_factors) >= 2:
			self.risk_level = "Medium"
		else:
			self.risk_level = "Low"
		
		if risk_factors:
			self.identified_risks = "; ".join(risk_factors)
	
	@frappe.whitelist()
	def generate_visit_summary(self):
		"""Generate a comprehensive visit summary"""
		summary = {
			"visit_id": self.name,
			"site_name": self.site_name,
			"visit_date": self.date,
			"visit_by": self.visit_by,
			"facility_type": self.facility_type,
			"existing_treatment": self.existing_treatment,
			"site_accessibility": self.site_accessibility,
			"available_area": self.available_area,
			"risk_level": self.risk_level,
			"samples_collected": self.samples_collected,
			"follow_up_required": self.follow_up_required
		}
		
		if self.site_observations:
			summary["key_observations"] = self.site_observations[:200] + "..." if len(self.site_observations) > 200 else self.site_observations
		
		if self.recommendations:
			summary["recommendations"] = self.recommendations[:200] + "..." if len(self.recommendations) > 200 else self.recommendations
		
		return summary
	
	def get_visit_checklist(self):
		"""Get a checklist for site visit completion"""
		checklist = [
			"Site measurements recorded",
			"Photos taken",
			"Sketches made",
			"Contact details collected",
			"Site conditions assessed",
			"Environmental factors noted",
			"Utility connections checked",
			"Regulatory requirements identified",
			"Risk assessment completed",
			"Recommendations provided"
		]
		
		completed = []
		if self.measurements_recorded:
			completed.append("Site measurements recorded")
		if self.photos_taken:
			completed.append("Photos taken")
		if self.sketches_made:
			completed.append("Sketches made")
		if self.contact_person:
			completed.append("Contact details collected")
		if self.site_observations:
			completed.append("Site conditions assessed")
		if self.environmental_impact:
			completed.append("Environmental factors noted")
		if self.sewer_connection:
			completed.append("Utility connections checked")
		if self.regulatory_requirements:
			completed.append("Regulatory requirements identified")
		if self.risk_level:
			completed.append("Risk assessment completed")
		if self.recommendations:
			completed.append("Recommendations provided")
		
		return {
			"total_items": len(checklist),
			"completed_items": len(completed),
			"completion_percentage": (len(completed) / len(checklist)) * 100,
			"checklist": checklist,
			"completed": completed
		}
	
	@frappe.whitelist()
	def auto_fill_from_svr(self):
		"""Auto-fill Site Visit fields from related Site Visit Request"""
		if not self.related_site_visit_request:
			frappe.throw(_("Please select a Site Visit Request first"))
		
		try:
			# Get SVR data
			svr_doc = frappe.get_doc("Site Visit Request", self.related_site_visit_request)
			
			# Auto-populate matching fields
			self.lead = svr_doc.lead
			self.contact_person = svr_doc.contact_person
			self.contact_number = svr_doc.contact_number
			self.email = svr_doc.email
			self.site_address = svr_doc.site_address
			self.city = svr_doc.city
			self.state = svr_doc.state
			self.latitude_and_longitude = svr_doc.latitude_and_longitude
			self.maps_location_link = svr_doc.maps_location_link
			
			# Map visit-specific fields
			self.date = svr_doc.site_visit_date
			if svr_doc.visit_purpose:
				self.site_observations = f"Visit Purpose: {svr_doc.visit_purpose}"
			if svr_doc.equipment_needed:
				self.equipment_used = svr_doc.equipment_needed
			if svr_doc.assigned_to:
				self.visit_by = svr_doc.assigned_to
			
			# Set default values
			self.weather_conditions = "Sunny"
			self.site_accessibility = "Good"
			self.risk_level = "Medium"
			
			return {
				"message": "Site Visit fields populated from Site Visit Request",
				"populated_fields": [
					"lead", "contact_person", "contact_number", "email",
					"site_address", "city", "state", "latitude_and_longitude",
					"maps_location_link", "date", "site_observations",
					"equipment_used", "visit_by"
				]
			}
			
		except Exception as e:
			frappe.throw(_("Error auto-filling from Site Visit Request: {0}").format(str(e)))
