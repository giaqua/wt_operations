import frappe
from frappe.model.document import Document
from frappe import _

class WWTPTechnicalProposal(Document):
	def validate(self):
		"""Validate the technical proposal"""
		self.validate_required_fields()
		self.validate_dates()
		self.calculate_totals()
		self.validate_capacity()
		
	# def before_save(self):
	# 	"""Actions before saving the document"""
	# 	self.calculate_totals()

	def validate_required_fields(self):
		"""Validate required fields"""
		if not self.lead:
			frappe.throw(_("Lead is required"))
		
		if not self.wwtp_technical_questionnaire:
			frappe.throw(_("WWTP Technical Questionnaire is required"))
		
		if not self.project_title:
			frappe.throw(_("Project Title is required"))
		
		if not self.design_capacity or self.design_capacity <= 0:
			frappe.throw(_("Design Capacity must be greater than 0"))
		
		if not self.treatment_technology:
			frappe.throw(_("Treatment Technology is required"))
		
		if not self.process_description:
			frappe.throw(_("Process Description is required"))
		
		if not self.technical_recommendations:
			frappe.throw(_("Technical Recommendations are required"))
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.valid_until and self.proposal_date:
			if self.valid_until <= self.proposal_date:
				frappe.throw(_("Valid Until date must be after Proposal Date"))
	
	def calculate_totals(self):
		"""Calculate total costs and implementation time"""
		# Calculate total project cost
		total_cost = 0
		if self.equipment_cost:
			total_cost += self.equipment_cost
		if self.civil_works_cost:
			total_cost += self.civil_works_cost
		if self.electrical_cost:
			total_cost += self.electrical_cost
		
		self.total_project_cost = total_cost
		
		# Calculate total implementation time
		total_time = 0
		if self.design_period:
			total_time += self.design_period
		if self.procurement_period:
			total_time += self.procurement_period
		if self.construction_period:
			total_time += self.construction_period
		if self.commissioning_period:
			total_time += self.commissioning_period
		
		self.total_implementation_time = total_time
	
	def validate_capacity(self):
		"""Validate capacity fields"""
		if self.current_capacity and self.design_capacity:
			if self.current_capacity > self.design_capacity:
				frappe.msgprint(_("Current capacity is higher than design capacity. Please verify."), alert=True)
	
	def on_submit(self):
		"""Actions when document is submitted"""
		self.update_related_documents()
		self.create_follow_up_tasks()
	
	def update_related_documents(self):
		"""Update related documents"""
		if self.wwtp_technical_questionnaire:
			frappe.msgprint(
				_("Technical Proposal submitted for WWTP Technical Questionnaire: {0}").format(
					self.wwtp_technical_questionnaire
				),
				alert=True
			)
	
	def create_follow_up_tasks(self):
		"""Create follow-up tasks if required"""
		if self.follow_up_required:
			frappe.msgprint(
				_("Follow-up required for this technical proposal"),
				alert=True
			)
	
	@frappe.whitelist()
	def auto_fill_from_tq(self):
		"""Auto-fill fields from WWTP Technical Questionnaire"""
		if not self.wwtp_technical_questionnaire:
			frappe.throw(_("Please select a WWTP Technical Questionnaire first"))
		
		try:
			tq_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
			
			# Auto-populate basic fields
			self.lead = tq_doc.lead
			self.opportunity = tq_doc.opportunity
			self.wastewater_generator_type = tq_doc.wastewater_generator_type
			self.current_capacity = tq_doc.capacity
			
			# Set default design capacity if not set
			if not self.design_capacity:
				self.design_capacity = tq_doc.capacity
			
			# Auto-populate project title if not set
			if not self.project_title:
				self.project_title = f"WWTP Technical Proposal - {tq_doc.wastewater_generator_type or 'Wastewater Treatment'}"
			
			# Auto-populate roles and responsibilities from TQ
			self.populate_roles_and_responsibilities_from_tq(tq_doc)
			
			return {
				"message": "Fields populated from WWTP Technical Questionnaire",
				"populated_fields": [
					"lead", "opportunity", "wastewater_generator_type", 
					"current_capacity", "design_capacity", "project_title",
					"roles_and_responsibilities_table"
				]
			}
			
		except Exception as e:
			frappe.throw(_("Error auto-filling from Technical Questionnaire: {0}").format(str(e)))
	
	@frappe.whitelist()
	def populate_roles_and_responsibilities_from_tq(self, tq_doc=None):
		"""Populate roles and responsibilities table from TQ"""
		if not tq_doc:
			if not self.wwtp_technical_questionnaire:
				frappe.throw(_("Please select a WWTP Technical Questionnaire first"))
			tq_doc = frappe.get_doc("WWTP Technical Questionnaire", self.wwtp_technical_questionnaire)
		
		try:
			# Clear existing roles and responsibilities
			self.roles_and_responsibilities_table = []
			
			# Get all scope of work options
			scope_of_work_options = frappe.get_all("Scope Of Work", 
				fields=["name", "scope_of_work", "scope_of_work_details"],
				order_by="scope_of_work"
			)
			
			# Get selected roles from TQ
			selected_roles = []
			if hasattr(tq_doc, 'tq_roles_and_responsibilities') and tq_doc.tq_roles_and_responsibilities:
				for role in tq_doc.tq_roles_and_responsibilities:
					if role.scope_of_work and role.not_required != 1:
						selected_roles.append(role.scope_of_work)
			
			# Populate roles and responsibilities table
			for scope_option in scope_of_work_options:
				# Only add roles that were selected in TQ
				if scope_option.name in selected_roles:
					self.append("roles_and_responsibilities_table", {
						"scope_of_work": scope_option.name,
						"scope_of_work_details": scope_option.scope_of_work_details,
						"not_required": 0
					})
			
			return {
				"message": f"Roles and responsibilities populated from TQ ({len(selected_roles)} roles selected)",
				"roles_count": len(selected_roles)
			}
			
		except Exception as e:
			frappe.throw(_("Error populating roles and responsibilities: {0}").format(str(e)))
	
	@frappe.whitelist()
	def auto_fill_from_site_visit(self):
		"""Auto-fill fields from Site Visit"""
		if not self.site_visit:
			frappe.throw(_("Please select a Site Visit first"))
		
		try:
			sv_doc = frappe.get_doc("Site Visit", self.site_visit)
			
			# Auto-populate site conditions
			self.site_conditions_summary = sv_doc.site_observations
			self.site_accessibility_rating = sv_doc.site_accessibility
			self.power_availability_rating = sv_doc.power_availability
			self.ground_conditions_rating = sv_doc.ground_conditions
			self.environmental_impact_assessment = sv_doc.environmental_impact
			
			# Auto-populate existing facility assessment
			if sv_doc.existing_treatment:
				self.existing_facility_assessment = f"Existing treatment facility: {sv_doc.treatment_capacity or 'Capacity not specified'}"
			
			return {
				"message": "Fields populated from Site Visit",
				"populated_fields": [
					"site_conditions_summary", "site_accessibility_rating",
					"power_availability_rating", "ground_conditions_rating",
					"environmental_impact_assessment", "existing_facility_assessment"
				]
			}
			
		except Exception as e:
			frappe.throw(_("Error auto-filling from Site Visit: {0}").format(str(e)))
	
	@frappe.whitelist()
	def auto_fill_from_water_sample(self):
		"""Auto-fill fields from Water Sample"""
		if not self.water_sample:
			frappe.throw(_("Please select a Water Sample first"))
		
		try:
			ws_doc = frappe.get_doc("Water Sample", self.water_sample)
			
			# Auto-populate water quality analysis
			self.influent_characteristics = f"Sample Type: {ws_doc.sample_type}\nLocation: {ws_doc.sample_location}\nCollected: {ws_doc.date_collected}"
			
			if ws_doc.results_available:
				self.compliance_status = "Under Review"  # Default status
			
			return {
				"message": "Fields populated from Water Sample",
				"populated_fields": [
					"influent_characteristics", "compliance_status"
				]
			}
			
		except Exception as e:
			frappe.throw(_("Error auto-filling from Water Sample: {0}").format(str(e)))
	
	@frappe.whitelist()
	def sync_to_external_site(self):
		"""Sync this proposal to external site (Site 1)"""
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
				frappe.throw(_("No external site settings configured. Proposal will not be synced."))
			
			# Create external proposal
			external_name = external_settings.create_technical_proposal_from_local(self)
			
			# Update local proposal with external details
			self.external_proposal_name = external_name
			self.external_proposal_url = f"{external_settings.site_url}/app/wwtp-technical-proposal/{external_name}"
			self.external_sync_status = "Synced"
			self.external_sync_error = ""
			self.external_site_settings = external_settings.name
			
			# Save without triggering hooks
			self.flags.ignore_validate = True
			self.save()
			
			frappe.msgprint(
				_("Technical Proposal synced to external site: {0}").format(external_name),
				alert=True
			)
			
			return {
				"status": self.external_sync_status,
				"external_proposal_name": self.external_proposal_name,
				"external_proposal_url": self.external_proposal_url
			}
			
		except Exception as e:
			# Update sync status to failed
			self.external_sync_status = "Failed"
			self.external_sync_error = str(e)
			self.flags.ignore_validate = True
			self.save()
			
			frappe.throw(_("Failed to sync Technical Proposal to external site: {0}").format(str(e)))
	
	@frappe.whitelist()
	def generate_proposal_summary(self):
		"""Generate a summary of the technical proposal"""
		summary = {
			"project_title": self.project_title,
			"lead": self.lead,
			"design_capacity": f"{self.design_capacity} m³/day",
			"treatment_technology": self.treatment_technology,
			"total_cost": f"${self.total_project_cost:,.2f}" if self.total_project_cost else "Not specified",
			"implementation_time": f"{self.total_implementation_time} weeks" if self.total_implementation_time else "Not specified",
			"compliance_status": self.compliance_status or "Not specified",
			"recommendations": self.technical_recommendations[:200] + "..." if len(self.technical_recommendations or "") > 200 else self.technical_recommendations
		}
		
		return summary
	
	@frappe.whitelist()
	def validate_proposal_completeness(self):
		"""Validate if proposal is complete for submission"""
		missing_fields = []
		
		required_fields = [
			("project_title", "Project Title"),
			("design_capacity", "Design Capacity"),
			("treatment_technology", "Treatment Technology"),
			("process_description", "Process Description"),
			("technical_recommendations", "Technical Recommendations")
		]
		
		for field, label in required_fields:
			if not getattr(self, field):
				missing_fields.append(label)
		
		if missing_fields:
			return {
				"complete": False,
				"missing_fields": missing_fields,
				"message": f"Missing required fields: {', '.join(missing_fields)}"
			}
		else:
			return {
				"complete": True,
				"message": "Proposal is complete and ready for submission"
			}
