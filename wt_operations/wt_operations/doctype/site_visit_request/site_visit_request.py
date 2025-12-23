# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class SiteVisitRequest(Document):
	def validate(self):
		"""Validate the site visit request"""
		self.set_title()
		self.validate_dates()
		self.set_defaults()
	
	def set_title(self):
		"""Set the title based on lead and visit date"""
		if self.lead and self.site_visit_date:
			lead_name = frappe.get_value("Lead", self.lead, "lead_name")
			self.title = f"{lead_name} - {self.site_visit_date}"
		elif self.lead:
			lead_name = frappe.get_value("Lead", self.lead, "lead_name")
			self.title = f"{lead_name} - Site Visit"
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.follow_up_date and self.site_visit_date:
			# Convert to date objects to ensure proper comparison
			follow_up = frappe.utils.getdate(self.follow_up_date)
			visit_date = frappe.utils.getdate(self.site_visit_date)
			if follow_up < visit_date:
				frappe.throw(_("Follow-up date cannot be before site visit date"))
	
	def set_defaults(self):
		"""Set default values"""
		if not self.status:
			self.status = "Open"
		
		if not self.priority:
			self.priority = "Medium"
		
		if not self.visit_type:
			self.visit_type = "Technical Survey"
	
	def on_submit(self):
		"""Actions when document is submitted"""
		# Update status from Open to Scheduled after submission
		# Use db_set to update without triggering validation/save
		if self.status == "Open":
			self.db_set("status", "Scheduled")
		
		# Note: External sync is now manual only - user must click sync button
	
	def push_to_external_site(self):
		"""Push this SVR to external site"""
		try:
			# Get external site settings
			external_settings = None
			if self.external_site_settings:
				external_settings = frappe.get_doc("External Site Settings", self.external_site_settings)
			else:
				# Get first enabled external site settings
				external_settings_list = frappe.get_all("External Site Settings", 
					filters={"enabled": 1}, 
					limit=1)
				if external_settings_list:
					external_settings = frappe.get_doc("External Site Settings", external_settings_list[0].name)
			
			if not external_settings:
				frappe.msgprint(_("No external site settings configured. SVR will not be synced."), alert=True)
				return
			
			# Create external SVR
			external_name = external_settings.create_site_visit_request_from_svr(self)
			
			# Update local SVR with external details
			self.external_request_name = external_name
			self.external_request_url = f"{external_settings.site_url}/app/site-visit-request/{external_name}"
			self.external_sync_status = "Synced"
			self.external_sync_error = ""
			self.external_site_settings = external_settings.name
			
			# Save without triggering hooks
			self.flags.ignore_validate = True
			self.save()
			
			# Update the TQ with external SVR link
			if self.technical_questionnaire:
				tq_doc = frappe.get_doc("WWTP Technical Questionnaire", self.technical_questionnaire)
				tq_doc.external_site_visit_request = self.external_request_url
				tq_doc.save()
			
			frappe.msgprint(
				_("Site Visit Request synced to external site: {0}").format(external_name),
				alert=True
			)
			
		except Exception as e:
			# Update sync status to failed
			self.external_sync_status = "Failed"
			self.external_sync_error = str(e)
			self.flags.ignore_validate = True
			self.save()
			
			frappe.msgprint(
				_("Failed to sync Site Visit Request to external site: {0}").format(str(e)),
				alert=True
			)
	
	@frappe.whitelist()
	def retry_push(self):
		"""Retry pushing to external site"""
		self.push_to_external_site()
		return {
			"status": self.external_sync_status,
			"external_request_name": self.external_request_name,
			"external_request_url": self.external_request_url
		}
	
	@frappe.whitelist()
	def manual_push_to_external_site(self):
		"""Manual push to external site (for any SVR status)"""
		try:
			# Set external site settings if not already set
			if not self.external_site_settings:
				external_settings_list = frappe.get_all("External Site Settings", 
					filters={"enabled": 1}, 
					limit=1)
				if external_settings_list:
					self.external_site_settings = external_settings_list[0].name
			
			self.push_to_external_site()
			return {
				"status": self.external_sync_status,
				"external_request_name": self.external_request_name,
				"external_request_url": self.external_request_url
			}
		except Exception as e:
			frappe.throw(_("Error in manual sync: {0}").format(str(e)))
	
	def on_cancel(self):
		"""Actions when document is cancelled"""
		self.status = "Cancelled"
	
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
	def create_site_visit(self):
		"""Create a Site Visit from this Site Visit Request"""
		try:
			# Check if SVR exists and has required data
			if not self.lead:
				frappe.throw(_("Lead is required to create Site Visit"))
			
			# Create new Site Visit document
			sv = frappe.new_doc("Site Visit")
			
			# Auto-populate fields from SVR
			sv.lead = self.lead
			sv.related_site_visit_request = self.name
			sv.contact_person = self.contact_person
			sv.contact_number = self.contact_number
			sv.email = self.email
			sv.site_address = self.site_address
			sv.city = self.city
			sv.state = self.state
			sv.latitude_and_longitude = self.latitude_and_longitude
			sv.maps_location_link = self.maps_location_link
			
			# Map visit-specific fields
			sv.date = self.site_visit_date
			if self.visit_purpose:
				sv.site_observations = f"Visit Purpose: {self.visit_purpose}"
			if self.equipment_needed:
				sv.equipment_used = self.equipment_needed
			if self.assigned_to:
				sv.visit_by = self.assigned_to
			
			# Set default values
			sv.weather_conditions = "Sunny"
			sv.site_accessibility = "Good"
			sv.risk_level = "Medium"
			
			# Insert as draft
			sv.insert()
			
			return {
				"site_visit": sv.name,
				"message": "Site Visit created successfully. Please complete the visit details and submit."
			}
			
		except Exception as e:
			frappe.throw(_("Error creating Site Visit: {0}").format(str(e)))
	
	def update_status_from_visits(self):
		"""Update SVR status based on linked Site Visits"""
		try:
			# Check if any Site Visits are submitted
			submitted_visits = frappe.get_all("Site Visit",
				filters={
					"related_site_visit_request": self.name,
					"docstatus": 1
				},
				limit=1
			)
			
			if submitted_visits and self.status != "Completed":
				# Update SVR status to Completed
				frappe.db.set_value("Site Visit Request", self.name, "status", "Completed")
				
				# Add entry to site_visits_table if not exists
				existing_entry = frappe.get_all("Site Visit Tracking Table",
					filters={
						"parent": self.name,
						"site_visit": submitted_visits[0].name
					},
					limit=1
				)
				
				if not existing_entry:
					sv_doc = frappe.get_doc("Site Visit", submitted_visits[0].name)
					frappe.get_doc({
						"doctype": "Site Visit Tracking Table",
						"parent": self.name,
						"parenttype": "Site Visit Request",
						"parentfield": "site_visits_table",
						"site_visit": sv_doc.name,
						"visit_date": sv_doc.date,
						"visit_status": "Submitted" if sv_doc.docstatus == 1 else "Draft",
						"visit_by": sv_doc.visit_by
					}).insert()
				
		except Exception as e:
			frappe.log_error(f"Error updating SVR status from visits: {str(e)}")