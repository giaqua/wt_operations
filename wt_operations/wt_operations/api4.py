import frappe

@frappe.whitelist()
def create_rfq_from_questionnaire(questionnaire_name, supplier, item_code):
    # Validate inputs
    if not questionnaire_name or not supplier or not item_code:
        frappe.throw("Parameters 'questionnaire_name', 'supplier', and 'item_code' are required.")

    # Load questionnaire document
    questionnaire = frappe.get_doc("STP TECHNICAL QUESTIONNAIRE", questionnaire_name)

    # Get default company from System Settings
    default_company = frappe.get_cached_value("System Settings", None, "default_company")

    # Use company from questionnaire if exists, else default company
    company = getattr(questionnaire, "company", default_company)

    # Load Item document to get stock_uom and verify existence
    item = frappe.get_doc("Item", item_code)

    # Get today's date from DB
    today_str = frappe.db.sql("SELECT CURDATE()", as_list=True)[0][0]

    # Calculate schedule_date = today + 7 days
    schedule_date = frappe.db.sql("SELECT DATE_ADD(%s, INTERVAL 7 DAY)", (today_str,), as_list=True)[0][0]

    # Create new Request for Quotation document
    rfq = frappe.new_doc("Request for Quotation")
    rfq.supplier = supplier
    rfq.company = company
    rfq.schedule_date = schedule_date

    # Set mandatory 'Message for Supplier' field; adjust text as needed
    rfq.message_supplier = "Please provide your quotation at earliest convenience."

    # Append item with required fields
    rfq.append("items", {
        "item_code": item_code,
        "qty": 1,
        "uom": item.stock_uom,
        "conversion_factor": 1,
        "description": f"Auto created RFQ from questionnaire {questionnaire_name}"
    })

    # Insert and submit RFQ
    rfq.insert()

    # Return the created RFQ name for link/display
    return rfq.name
@frappe.whitelist()
def sync_technical_proposal_to_sales(doc_name):
	"""Sync Technical Proposal to sales site"""
	try:
		# Get the document
		doc = frappe.get_doc("WWTP Technical Proposal", doc_name)
		
		# Check if already synced
		if doc.external_sync_status == "Synced":
			return {"success": False, "error": "Document already synced"}
		
		# Get external site settings
		settings = frappe.get_all("External Site Settings", 
			filters={"enabled": 1, "sync_technical_proposals": 1}, 
			limit=1)
		
		if not settings:
			return {"success": False, "error": "No external site configured for sync"}
		
		# Perform sync using sync manager
		from wt_operations.wt_operations.sync_manager import sync_document_to_external_site
		external_name = sync_document_to_external_site("WWTP Technical Proposal", doc_name, settings[0].name)
		
		if external_name:
			# Update document status
			doc.db_set("external_sync_status", "Synced")
			doc.db_set("workflow_status", "Synced to Sales")
			doc.db_set("external_proposal_name", external_name)
			
			# Update workflow tracking
			from wt_operations.wt_operations.workflow_hooks import update_workflow_tracking
			update_workflow_tracking(doc, "WWTP Technical Proposal", "Synced to Sales")
			
			return {"success": True, "external_name": external_name}
		else:
			doc.db_set("external_sync_status", "Failed")
			return {"success": False, "error": "Sync operation failed"}
			
	except Exception as e:
		frappe.log_error(f"Sync failed for {doc_name}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_customer_proposal_from_technical(technical_proposal):
	"""Create Customer Proposal from Technical Proposal"""
	try:
		# Get technical proposal document
		tech_doc = frappe.get_doc("WWTP Technical Proposal", technical_proposal)
		
		# Check if customer proposal already exists
		existing = frappe.get_all("Customer Proposal", 
			filters={"wwtp_technical_proposal": technical_proposal}, 
			limit=1)
		
		if existing:
			return {"success": False, "error": "Customer Proposal already exists", "existing_name": existing[0].name}
		
		# Create new Customer Proposal
		customer_proposal = frappe.new_doc("Customer Proposal")
		customer_proposal.wwtp_technical_proposal = technical_proposal
		
		# Copy basic information
		customer_proposal.lead = tech_doc.lead
		customer_proposal.customer = tech_doc.customer
		customer_proposal.customer_contact = tech_doc.customer_contact
		customer_proposal.opportunity = tech_doc.opportunity
		customer_proposal.wwtp_technical_questionnaire = tech_doc.wwtp_technical_questionnaire
		customer_proposal.site_visit = tech_doc.site_visit
		customer_proposal.water_sample = tech_doc.water_sample
		
		# Set proposal information
		customer_proposal.prepared_by = frappe.session.user
		customer_proposal.technical_manager = tech_doc.technical_manager
		customer_proposal.account_manager = tech_doc.account_manager
		
		# Calculate deadline (5 days from now)
		from frappe.utils import add_days, nowdate
		customer_proposal.deadline_date = add_days(nowdate(), 5)
		
		# Save the document
		customer_proposal.insert()
		
		# Populate from technical proposal
		populate_customer_proposal_from_technical_proposal(customer_proposal.name, technical_proposal)
		
		return {"success": True, "customer_proposal": customer_proposal.name}
		
	except Exception as e:
		frappe.log_error(f"Failed to create customer proposal from technical: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def populate_customer_proposal_from_technical(customer_proposal, technical_proposal):
	"""Populate Customer Proposal fields from Technical Proposal"""
	try:
		# Get documents
		cp_doc = frappe.get_doc("Customer Proposal", customer_proposal)
		tp_doc = frappe.get_doc("WWTP Technical Proposal", technical_proposal)
		
		# Copy all relevant fields
		field_mappings = [
			"project_title", "project_description", "wastewater_generator_type",
			"design_capacity", "current_capacity", "treatment_technology",
			"process_description", "treatment_stages", "daily_flow",
			"operation_hours", "average_hourly_flow", "site_conditions_summary",
			"site_accessibility_rating", "power_availability_rating",
			"ground_conditions_rating", "environmental_impact_assessment",
			"influent_characteristics", "effluent_requirements", "treatment_challenges",
			"compliance_status", "civil_requirements", "site_preparation_needs",
			"utility_connections", "equalization_tank_minimum_capacity",
			"sludge_holding_tank_minimum_capacity", "product_tank_minimum_capacity",
			"concrete_pads_for_stp", "design_period", "procurement_period",
			"construction_period", "commissioning_period", "total_implementation_time",
			"warranty_text", "maintenance_requirements", "chemical_consumption",
			"energy_consumption", "environmental_permits_required",
			"discharge_permit_status", "environmental_monitoring",
			"technical_risks", "environmental_risks", "mitigation_strategies"
		]
		
		for field in field_mappings:
			if hasattr(tp_doc, field) and getattr(tp_doc, field):
				cp_doc.db_set(field, getattr(tp_doc, field))
		
		# Copy child tables
		if tp_doc.roles_and_responsibilities_table:
			cp_doc.set("roles_and_responsibilities_table", [])
			for row in tp_doc.roles_and_responsibilities_table:
				cp_doc.append("roles_and_responsibilities_table", {
					"role": row.role,
					"responsibility": row.responsibility,
					"party": row.party
				})
		
		# Save the document
		cp_doc.save()
		
		return {"success": True}
		
	except Exception as e:
		frappe.log_error(f"Failed to populate customer proposal: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_customer_proposal_email(customer_proposal, email_subject, email_message, include_attachments=True):
	"""Send Customer Proposal via email"""
	try:
		# Get document
		doc = frappe.get_doc("Customer Proposal", customer_proposal)
		
		# Get customer email
		customer_email = None
		if doc.customer_contact:
			customer_email = frappe.get_value("Contact", doc.customer_contact, "email_id")
		elif doc.customer:
			customer_email = frappe.get_value("Customer", doc.customer, "email_id")
		
		if not customer_email:
			return {"success": False, "error": "No email address found for customer"}
		
		# Prepare email
		attachments = []
		if include_attachments:
			# Generate PDF of the proposal
			pdf_content = frappe.get_print("Customer Proposal", customer_proposal, "Standard", as_pdf=True)
			attachments.append({
				"fname": f"Customer_Proposal_{customer_proposal}.pdf",
				"fcontent": pdf_content
			})
		
		# Send email
		frappe.sendmail(
			recipients=[customer_email],
			subject=email_subject,
			message=email_message,
			attachments=attachments,
			reference_doctype="Customer Proposal",
			reference_name=customer_proposal
		)
		
		# Update document status
		doc.db_set("workflow_status", "Sent to Customer")
		
		# Add to communication log
		frappe.get_doc({
			"doctype": "Communication",
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Sent",
			"reference_doctype": "Customer Proposal",
			"reference_name": customer_proposal,
			"subject": email_subject,
			"content": email_message,
			"recipients": customer_email
		}).insert()
		
		return {"success": True}
		
	except Exception as e:
		frappe.log_error(f"Failed to send customer proposal email: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_rfp_from_customer_proposal(customer_proposal):
	"""Create Request for Proposal from Customer Proposal"""
	try:
		# Get customer proposal document
		cp_doc = frappe.get_doc("Customer Proposal", customer_proposal)
		
		# Check if RFP already exists
		existing = frappe.get_all("Request for Proposal", 
			filters={"customer_proposal": customer_proposal}, 
			limit=1)
		
		if existing:
			return {"success": False, "error": "Request for Proposal already exists", "existing_name": existing[0].name}
		
		# Create new RFP
		rfp = frappe.new_doc("Request for Proposal")
		rfp.customer_proposal = customer_proposal
		rfp.customer = cp_doc.customer
		rfp.lead = cp_doc.lead
		rfp.opportunity = cp_doc.opportunity
		rfp.project_title = cp_doc.project_title
		rfp.project_description = cp_doc.project_description
		
		# Set RFP specific fields
		rfp.rfp_type = "Technical and Commercial"
		rfp.submission_deadline = frappe.utils.add_days(frappe.utils.nowdate(), 30)
		rfp.evaluation_criteria = "Technical compliance, commercial competitiveness, implementation timeline"
		
		# Copy scope of work
		if cp_doc.scope_of_work:
			rfp.scope_of_work = cp_doc.scope_of_work
		
		# Save the document
		rfp.insert()
		
		return {"success": True, "rfp_name": rfp.name}
		
	except Exception as e:
		frappe.log_error(f"Failed to create RFP from customer proposal: {str(e)}")
		return {"success": False, "error": str(e)}


def populate_customer_proposal_from_technical_proposal(customer_proposal_name, technical_proposal_name):
	"""Helper function to populate customer proposal from technical proposal"""
	try:
		return populate_customer_proposal_from_technical(customer_proposal_name, technical_proposal_name)
	except Exception as e:
		frappe.log_error(f"Error in populate_customer_proposal_from_technical_proposal: {str(e)}")
		return {"success": False, "error": str(e)}