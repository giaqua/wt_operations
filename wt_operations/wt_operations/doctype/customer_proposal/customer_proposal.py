# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class CustomerProposal(Document):
	def validate(self):
		"""Validate the customer proposal"""
		self.validate_required_fields()
		self.validate_dates()
	
	def validate_required_fields(self):
		"""Validate required fields"""
		if not self.customer:
			frappe.throw(_("Customer is required"))
		
		if not self.wwtp_technical_proposal:
			frappe.throw(_("WWTP Technical Proposal is required"))
		
		if not self.issue_date:
			frappe.throw(_("Issue Date is required"))
		
		if not self.valid_up_to:
			frappe.throw(_("Valid Up To date is required"))
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.valid_up_to and self.issue_date:
			if self.valid_up_to <= self.issue_date:
				frappe.throw(_("Valid Up To date must be after Issue Date"))
	
	def on_submit(self):
		"""Actions when document is submitted"""
		self.update_related_documents()
	
	def update_related_documents(self):
		"""Update related documents"""
		if self.wwtp_technical_proposal:
			frappe.msgprint(
				_("Customer Proposal submitted based on Technical Proposal: {0}").format(
					self.wwtp_technical_proposal
				),
				alert=True
			)
	
	@frappe.whitelist()
	def auto_fill_from_technical_proposal(self):
		"""Auto-fill fields from WWTP Technical Proposal"""
		if not self.wwtp_technical_proposal:
			frappe.throw(_("Please select a WWTP Technical Proposal first"))
		
		try:
			tp_doc = frappe.get_doc("WWTP Technical Proposal", self.wwtp_technical_proposal)
			
			# Auto-populate basic fields
			self.lead = tp_doc.lead
			self.opportunity = tp_doc.opportunity
			self.wwtp_technical_questionnaire = tp_doc.wwtp_technical_questionnaire
			self.site_visit = tp_doc.site_visit
			self.water_sample = tp_doc.water_sample
			
			# Auto-populate project summary fields
			self.project_title = tp_doc.project_title
			self.project_description = tp_doc.project_description
			self.wastewater_generator_type = tp_doc.wastewater_generator_type
			self.design_capacity = tp_doc.design_capacity
			self.current_capacity = tp_doc.current_capacity
			self.treatment_technology = tp_doc.treatment_technology
			self.process_description = tp_doc.process_description
			self.treatment_stages = tp_doc.treatment_stages
			
			# Auto-populate scope fields
			self.scope_of_work = tp_doc.scope_of_work
			self.termination_points = tp_doc.termination_points
			self.exclusions = tp_doc.exclusions
			
			# Auto-populate roles and responsibilities
			self.populate_roles_and_responsibilities_from_tp(tp_doc)
			
			# Auto-populate technical specifications
			self.daily_flow = tp_doc.daily_flow
			self.operation_hours = tp_doc.operation_hours
			self.average_hourly_flow = tp_doc.average_hourly_flow
			self.site_conditions_summary = tp_doc.site_conditions_summary
			self.site_accessibility_rating = tp_doc.site_accessibility_rating
			self.power_availability_rating = tp_doc.power_availability_rating
			self.ground_conditions_rating = tp_doc.ground_conditions_rating
			self.environmental_impact_assessment = tp_doc.environmental_impact_assessment
			self.influent_characteristics = tp_doc.influent_characteristics
			self.effluent_requirements = tp_doc.effluent_requirements
			self.treatment_challenges = tp_doc.treatment_challenges
			self.compliance_status = tp_doc.compliance_status
			
			# Auto-populate implementation requirements
			self.civil_requirements = tp_doc.civil_requirements
			self.site_preparation_needs = tp_doc.site_preparation_needs
			self.utility_connections = tp_doc.utility_connections
			self.equalization_tank_minimum_capacity = tp_doc.equalization_tank_minimum_capacity
			self.sludge_holding_tank_minimum_capacity = tp_doc.sludge_holding_tank_minimum_capacity
			self.product_tank_minimum_capacity = tp_doc.product_tank_minimum_capacity
			self.concrete_pads_for_stp = tp_doc.concrete_pads_for_stp
			self.design_period = tp_doc.design_period
			self.procurement_period = tp_doc.procurement_period
			self.construction_period = tp_doc.construction_period
			self.commissioning_period = tp_doc.commissioning_period
			self.total_implementation_time = tp_doc.total_implementation_time
			
			# Auto-populate warranty and support fields
			self.warranty_text = tp_doc.warranty_text
			self.maintenance_requirements = tp_doc.maintenance_requirements
			self.chemical_consumption = tp_doc.chemical_consumption
			self.energy_consumption = tp_doc.energy_consumption
			self.environmental_permits_required = tp_doc.environmental_permits_required
			self.discharge_permit_status = tp_doc.discharge_permit_status
			self.environmental_monitoring = tp_doc.environmental_monitoring
			self.technical_risks = tp_doc.technical_risks
			self.environmental_risks = tp_doc.environmental_risks
			self.mitigation_strategies = tp_doc.mitigation_strategies
			
			return {
				"message": "Customer Proposal populated from Technical Proposal",
				"populated_fields": [
					"lead", "opportunity", "wwtp_technical_questionnaire", "site_visit", "water_sample",
					"project_title", "project_description", "wastewater_generator_type", "design_capacity",
					"treatment_technology", "scope_of_work", "roles_and_responsibilities_table",
					"technical_specifications", "implementation_requirements", "warranty_support"
				]
			}
			
		except Exception as e:
			frappe.throw(_("Error auto-filling from Technical Proposal: {0}").format(str(e)))
	
	@frappe.whitelist()
	def populate_roles_and_responsibilities_from_tp(self, tp_doc=None):
		"""Populate roles and responsibilities table from Technical Proposal"""
		if not tp_doc:
			if not self.wwtp_technical_proposal:
				frappe.throw(_("Please select a WWTP Technical Proposal first"))
			tp_doc = frappe.get_doc("WWTP Technical Proposal", self.wwtp_technical_proposal)
		
		try:
			# Clear existing roles and responsibilities
			self.roles_and_responsibilities_table = []
			
			# Copy roles and responsibilities from technical proposal
			if hasattr(tp_doc, 'roles_and_responsibilities_table') and tp_doc.roles_and_responsibilities_table:
				for role in tp_doc.roles_and_responsibilities_table:
					self.append("roles_and_responsibilities_table", {
						"scope_of_work": role.scope_of_work,
						"responsible": role.responsible,
						"not_required": role.not_required,
						"remarks": role.remarks
					})
			
			return {
				"message": f"Roles and responsibilities populated from Technical Proposal ({len(tp_doc.roles_and_responsibilities_table or [])} roles)",
				"roles_count": len(tp_doc.roles_and_responsibilities_table or [])
			}
			
		except Exception as e:
			frappe.throw(_("Error populating roles and responsibilities: {0}").format(str(e)))
	
	@frappe.whitelist()
	def generate_proposal_summary(self):
		"""Generate a summary of the customer proposal"""
		summary = {
			"customer": self.customer,
			"project_title": self.project_title,
			"treatment_technology": self.treatment_technology,
			"design_capacity": f"{self.design_capacity} m³/day" if self.design_capacity else "Not specified",
			"validity_period": f"{self.issue_date} to {self.valid_up_to}" if self.issue_date and self.valid_up_to else "Not specified",
			"technical_proposal": self.wwtp_technical_proposal,
			"options_available": []
		}
		
		# Check which options have items
		if self.option_1_table:
			summary["options_available"].append("Option 1: Supply & Installation")
		if self.option_2_table:
			summary["options_available"].append("Option 2: Design-Build")
		if self.option_3_table:
			summary["options_available"].append("Option 3: BOOT")
		
		return summary
