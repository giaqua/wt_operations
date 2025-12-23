# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class WWTPTechnicalQuestionnaire(Document):
	pass
	
	@frappe.whitelist()
	def create_site_visit_request(self, external_site_settings=None):
		"""Create a draft Site Visit Request from this Technical Questionnaire"""
		try:
			# Check if TQ is submitted
			if self.docstatus != 1:
				frappe.throw(_("Technical Questionnaire must be submitted before creating Site Visit Request"))
			
			# Create new Site Visit Request
			svr = frappe.new_doc("Site Visit Request")
			
			# Set basic fields from TQ
			svr.lead = self.lead
			svr.opportunity = self.opportunity
			svr.site_visit_date = frappe.utils.today()
			svr.status = "Open"
			svr.source_document = self.name
			svr.source_doctype = "WWTP Technical Questionnaire"
			svr.notes = f"Auto-generated from WWTP Technical Questionnaire: {self.name}"
			
			# Set visit details based on TQ data with comprehensive analysis
			svr.visit_type = self._determine_visit_type()
			svr.priority = self._determine_priority()
			svr.visit_purpose = self._generate_visit_purpose()
			svr.special_requirements = self._generate_special_requirements()
			svr.equipment_needed = self._generate_equipment_list()
			svr.estimated_duration = self._estimate_duration()
			svr.follow_up_required = 1 if self.sample_collection_required else 0
			
			# Link to technical questionnaire
			svr.technical_questionnaire = self.name
			
			# Insert as draft (do not submit yet)
			# Note: external_site_settings will be set when user manually syncs
			svr.insert()
			
			# Update TQ with local SVR link for reference (using db.set_value for submitted docs)
			frappe.db.set_value("WWTP Technical Questionnaire", self.name, "local_site_visit_request", svr.name)
			
			return {
				"local_svr": svr.name,
				"message": "Site Visit Request created as draft. Please complete and review before submitting."
			}
			
		except Exception as e:
			frappe.throw(_("Error creating Site Visit Request: {0}").format(str(e)))
	
	def _determine_visit_type(self):
		"""Determine visit type based on TQ data"""
		if self.is_it_new_wwtp_or_an_upgrade and "upgrade" in str(self.is_it_new_wwtp_or_an_upgrade).lower():
			return "Follow-up Visit"
		elif self.wastewater_generator_type in ["Industrial", "Oil and Gas", "Slaughterhouse"]:
			return "Technical Survey"
		elif self.sample_collection_required:
			return "Initial Assessment"
		else:
			return "Technical Survey"
	
	def _determine_priority(self):
		"""Determine priority based on TQ data"""
		priority_score = 0
		
		# High capacity = higher priority
		if self.capacity and self.capacity > 1000:
			priority_score += 2
		elif self.capacity and self.capacity > 500:
			priority_score += 1
		
		# Industrial/complex types = higher priority
		if self.wastewater_generator_type in ["Industrial", "Oil and Gas", "Slaughterhouse"]:
			priority_score += 2
		elif self.wastewater_generator_type == "Special Case":
			priority_score += 3
		
		# Sample collection = higher priority
		if self.sample_collection_required:
			priority_score += 1
		
		# Site visit required = higher priority
		if self.site_visit_required:
			priority_score += 1
		
		if priority_score >= 4:
			return "Urgent"
		elif priority_score >= 2:
			return "High"
		elif priority_score >= 1:
			return "Medium"
		else:
			return "Low"
	
	def _generate_visit_purpose(self):
		"""Generate detailed visit purpose based on TQ data"""
		purpose_parts = []
		
		# Base purpose
		if self.is_it_new_wwtp_or_an_upgrade and "upgrade" in str(self.is_it_new_wwtp_or_an_upgrade).lower():
			purpose_parts.append("WWTP Upgrade Assessment")
		else:
			purpose_parts.append("WWTP Technical Assessment")
		
		# Add generator type context
		if self.wastewater_generator_type:
			purpose_parts.append(f"for {self.wastewater_generator_type} wastewater")
		
		# Add capacity context
		if self.capacity:
			purpose_parts.append(f"({self.capacity} m³/day capacity)")
		
		# Add special requirements
		if self.sample_collection_required:
			purpose_parts.append("- includes water quality sampling")
		
		if self.site_visit_required:
			purpose_parts.append("- site survey required")
		
		return " ".join(purpose_parts)
	
	def _generate_special_requirements(self):
		"""Generate comprehensive special requirements"""
		requirements = []
		
		# Capacity and footprint
		if self.capacity:
			requirements.append(f"Treatment Capacity: {self.capacity} m³/day")
		if self.the_available_footprint_dedicated_for_stp_in_sm:
			requirements.append(f"Available Footprint: {self.the_available_footprint_dedicated_for_stp_in_sm} sqm")
		
		# Location details
		if self.location_of_the_wwtp_needed:
			requirements.append(f"Location: {self.location_of_the_wwtp_needed}")
		
		# Generator type specific requirements
		if self.wastewater_generator_type == "Industrial":
			requirements.append("Industrial wastewater treatment - check for chemical contaminants")
		elif self.wastewater_generator_type == "Slaughterhouse":
			requirements.append("Slaughterhouse wastewater - high organic load expected")
		elif self.wastewater_generator_type == "Oil and Gas":
			requirements.append("Oil & Gas wastewater - hydrocarbon contamination assessment")
		elif self.wastewater_generator_type == "Special Case":
			requirements.append(f"Special Case: {self.special_case_generator_type or 'Custom requirements'}")
		
		# Existing equipment
		if self.available_equipment__tanks_pumpsect:
			requirements.append(f"Existing Equipment: {self.available_equipment__tanks_pumpsect}")
		
		# Design conditions
		if self.design_of_the_site_condition:
			requirements.append(f"Site Conditions: {self.design_of_the_site_condition}")
		
		# Flow characteristics
		if self.daily_flow:
			requirements.append(f"Daily Flow: {self.daily_flow}")
		if self.peak_factor:
			requirements.append(f"Peak Factor: {self.peak_factor}")
		
		# Number of streams
		if self.number_of_streams and self.number_of_streams > 1:
			requirements.append(f"Multiple influent streams: {int(self.number_of_streams)} streams")
		
		return "; ".join(requirements) if requirements else "Standard WWTP assessment requirements"
	
	def _generate_equipment_list(self):
		"""Generate equipment list based on requirements"""
		equipment = []
		
		# Basic equipment
		equipment.extend(["Measuring tape", "Camera", "Notebook", "Safety equipment"])
		
		# Sample collection equipment
		if self.sample_collection_required:
			equipment.extend([
				"Water sampling bottles",
				"pH meter",
				"Turbidity meter",
				"Temperature probe",
				"Sample preservation chemicals"
			])
		
		# Generator type specific equipment
		if self.wastewater_generator_type == "Industrial":
			equipment.extend(["Chemical test strips", "Conductivity meter"])
		elif self.wastewater_generator_type == "Oil and Gas":
			equipment.extend(["Oil detection kit", "Hydrocarbon analyzer"])
		elif self.wastewater_generator_type == "Slaughterhouse":
			equipment.extend(["BOD test kit", "Organic load analyzer"])
		
		# Site assessment equipment
		if self.the_available_footprint_dedicated_for_stp_in_sm:
			equipment.append("Area measurement tools")
		
		# Flow measurement
		if self.daily_flow or self.peak_factor:
			equipment.append("Flow measurement devices")
		
		# Multiple streams
		if self.number_of_streams and self.number_of_streams > 1:
			equipment.append("Multiple sampling points setup")
		
		return ", ".join(equipment)
	
	def _estimate_duration(self):
		"""Estimate visit duration based on complexity"""
		base_hours = 2
		
		# Add time for sample collection
		if self.sample_collection_required:
			base_hours += 1
		
		# Add time for complex generator types
		if self.wastewater_generator_type in ["Industrial", "Oil and Gas", "Slaughterhouse"]:
			base_hours += 1
		elif self.wastewater_generator_type == "Special Case":
			base_hours += 2
		
		# Add time for multiple streams
		if self.number_of_streams and self.number_of_streams > 1:
			base_hours += int(self.number_of_streams) * 0.5
		
		# Add time for large capacity
		if self.capacity and self.capacity > 1000:
			base_hours += 1
		
		# Add time for site survey
		if self.site_visit_required:
			base_hours += 1
		
		if base_hours <= 3:
			return f"{base_hours}-{base_hours + 1} hours"
		elif base_hours <= 5:
			return f"{base_hours}-{base_hours + 2} hours"
		else:
			return f"{base_hours}-{base_hours + 3} hours"
	
	@frappe.whitelist()
	def populate_roles_from_scope_of_work(self):
		"""Populate tq_roles_and_responsibilities table with all available Scope of Work entries"""
		try:
			# Get all Scope of Work entries
			scope_of_work_list = frappe.get_all(
				"Scope Of Work",
				fields=["name", "scope_of_work", "scope_of_work_details"],
				order_by="scope_of_work"
			)
			
			if not scope_of_work_list:
				return {
					"message": "No Scope of Work entries found. Please create Scope of Work entries first.",
					"added_count": 0,
					"total_available": 0
				}
			
			# Get existing scope_of_work entries in the table to avoid duplicates
			existing_scope_of_work = set()
			if self.tq_roles_and_responsibilities:
				for role in self.tq_roles_and_responsibilities:
					if role.scope_of_work:
						existing_scope_of_work.add(role.scope_of_work)
			
			# Add missing scope of work entries
			added_count = 0
			for sow in scope_of_work_list:
				if sow.name not in existing_scope_of_work:
					self.append("tq_roles_and_responsibilities", {
						"scope_of_work": sow.name,
						"responsible": "",  # Leave empty for user to select
						"not_required": 0,
						"remarks": ""
					})
					added_count += 1
			
			return {
				"message": f"Added {added_count} Scope of Work entries. {len(existing_scope_of_work)} entries were already present.",
				"added_count": added_count,
				"total_available": len(scope_of_work_list),
				"already_present": len(existing_scope_of_work)
			}
			
		except Exception as e:
			frappe.throw(_("Error populating roles from Scope of Work: {0}").format(str(e)))
	
	@frappe.whitelist()
	def populate_effluent_parameters(self):
		"""Auto-populate effluent quality parameters based on target type"""
		effluent_type = self.please_pick_the_target_effluent_type
		
		# Define standards dictionary based on effluent-rates.md
		standards = {
			"Irrigation (unrestricted)": {
				"ph_eff": 7.5,  # midpoint of 6.5-8.5
				"tss_eff": 10,  # monthly average
				"bod5_eff": 10,  # monthly average
				"cod_eff": 90,
				"turbidity_eff": 5,
				"oil_grease_eff": 0,
				"tds_eff": 2000,
				"free_chlorine": 0.5,
				"ecoli": 100,
				"wormies": 0
			},
			"Irrigation (restricted)": {
				"ph_eff": 7.5,  # midpoint of 6.5-8.5
				"tss_eff": 20,  # monthly average
				"bod5_eff": 20,  # monthly average
				"cod_eff": 90,
				"turbidity_eff": None,  # undefined
				"oil_grease_eff": 0,
				"tds_eff": 2000,
				"free_chlorine": 0.5,
				"ecoli": 1000,
				"wormies": 1
			},
			"unusable (safe discharge)": {
				"ph_eff": 7.5,  # midpoint of 5-10
				"tss_eff": 300,
				"bod5_eff": 500,
				"cod_eff": 1000,
				"turbidity_eff": None,
				"oil_grease_eff": 60,  # hydrocarbon-based
				"tds_eff": 2000,
				"free_chlorine": None,
				"ecoli": None,
				"wormies": None
			},
			"Industrial - Washing": {
				"ph_eff": 7.5,  # midpoint of 5-10
				"tss_eff": 300,
				"bod5_eff": 500,
				"cod_eff": 1000,
				"turbidity_eff": None,
				"oil_grease_eff": 60,  # hydrocarbon-based
				"tds_eff": 2000,
				"free_chlorine": None,
				"ecoli": None,
				"wormies": None
			},
			"Industrial - cooling": {
				"ph_eff": 7.5,  # midpoint of 5-10
				"tss_eff": 300,
				"bod5_eff": 500,
				"cod_eff": 1000,
				"turbidity_eff": None,
				"oil_grease_eff": 60,  # hydrocarbon-based
				"tds_eff": 2000,
				"free_chlorine": None,
				"ecoli": None,
				"wormies": None
			},
			"Industrial - manufacturing": {
				"ph_eff": 7.5,  # midpoint of 5-10
				"tss_eff": 300,
				"bod5_eff": 500,
				"cod_eff": 1000,
				"turbidity_eff": None,
				"oil_grease_eff": 60,  # hydrocarbon-based
				"tds_eff": 2000,
				"free_chlorine": None,
				"ecoli": None,
				"wormies": None
			},
			"Coastal Discharge - Marine": {
				"ph_eff": 7.5,  # midpoint of 6-9
				"tss_eff": 40,  # monthly average
				"bod5_eff": 40,  # monthly average
				"cod_eff": 150,
				"turbidity_eff": None,
				"oil_grease_eff": 10,
				"tds_eff": None,
				"free_chlorine": 0.3,
				"ecoli": 1000,
				"wormies": None  # <1 in standard
			},
			"Coastal Discharge - Environmentally Sensitive": {
				"ph_eff": 7.5,  # midpoint of 6-9
				"tss_eff": 20,  # monthly average
				"bod5_eff": 20,  # monthly average
				"cod_eff": 90,
				"turbidity_eff": None,
				"oil_grease_eff": 5,
				"tds_eff": None,
				"free_chlorine": 0.2,
				"ecoli": 1000,
				"wormies": None
			},
			"Coastal Discharge - Industrial": {
				"ph_eff": 7.5,  # midpoint of 6-9
				"tss_eff": 40,  # monthly average
				"bod5_eff": 40,  # monthly average
				"cod_eff": 150,
				"turbidity_eff": None,
				"oil_grease_eff": 10,
				"tds_eff": None,
				"free_chlorine": 0.3,
				"ecoli": None,  # not specified for industrial
				"wormies": None
			}
		}
		
		if effluent_type in standards:
			return standards[effluent_type]
		
		return {}