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
def sync_technical_questionnaire_to_operations(doc_name):
	"""Sync Technical Questionnaire to operations site"""
	try:
		# Get the document
		doc = frappe.get_doc("WWTP Technical Questionnaire", doc_name)
		
		# Check if already synced
		if doc.sync_status == "Synced":
			return {"success": False, "error": "Document already synced"}
		
		# Get external site settings
		settings = frappe.get_all("External Site Settings", 
			filters={"enabled": 1, "sync_technical_questionnaires": 1}, 
			limit=1)
		
		if not settings:
			return {"success": False, "error": "No external site configured for sync"}
		
		# Perform sync using sync manager
		from wt_operations.wt_operations.sync_manager import sync_document_to_external_site
		external_name = sync_document_to_external_site("WWTP Technical Questionnaire", doc_name, settings[0].name)
		
		if external_name:
			# Update document status
			doc.db_set("sync_status", "Synced")
			doc.db_set("workflow_status", "Synced to Operations")
			# Only set external_document_name if the field exists
			if hasattr(doc, "external_document_name"):
				doc.db_set("external_document_name", external_name)
			
			# Create workflow tracking if not exists
			from wt_operations.wt_operations.workflow_hooks import create_workflow_tracking
			create_workflow_tracking(doc)
			
			return {"success": True, "external_name": external_name}
		else:
			doc.db_set("sync_status", "Failed")
			return {"success": False, "error": "Sync operation failed"}
			
	except Exception as e:
		frappe.log_error(f"Sync failed for {doc_name}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_site_visit_request_from_questionnaire(questionnaire_name):
	"""Create Site Visit Request from Technical Questionnaire"""
	try:
		# Get the questionnaire document
		questionnaire = frappe.get_doc("WWTP Technical Questionnaire", questionnaire_name)
		
		# Check if site visit is required
		if not questionnaire.site_visit_required:
			return {"success": False, "error": "Site visit not required for this questionnaire"}
		
		# Check if site visit request already exists
		existing = frappe.get_all("Site Visit Request", 
			filters={"technical_questionnaire": questionnaire_name}, 
			limit=1)
		
		if existing:
			return {"success": False, "error": "Site Visit Request already exists", "existing_name": existing[0].name}
		
		# Create new Site Visit Request
		site_visit_request = frappe.new_doc("Site Visit Request")
		site_visit_request.technical_questionnaire = questionnaire_name
		site_visit_request.lead = questionnaire.lead
		site_visit_request.opportunity = questionnaire.opportunity
		site_visit_request.assigned_site_manager = questionnaire.assigned_site_manager
		site_visit_request.priority = "Medium"  # Default priority
		
		# Calculate deadline
		from wt_operations.wt_operations.workflow_hooks import calculate_deadline_for_document
		calculate_deadline_for_document(site_visit_request, "Site Visit Request")
		
		# Save the document
		site_visit_request.insert()
		
		# Update questionnaire with local site visit request link
		questionnaire.db_set("local_site_visit_request", site_visit_request.name)
		
		return {"success": True, "site_visit_request": site_visit_request.name}
		
	except Exception as e:
		frappe.log_error(f"Failed to create Site Visit Request from {questionnaire_name}: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_workflow_progress(doctype, doc_name):
	"""Get workflow progress for a document"""
	try:
		doc = frappe.get_doc(doctype, doc_name)
		
		# Define workflow stages and their completion percentages
		workflow_stages = {
			"WWTP Technical Questionnaire": {
				"Draft": 0,
				"Submitted": 50,
				"Synced to Operations": 100
			},
			"Site Visit Request": {
				"Open": 0,
				"Scheduled": 25,
				"In Progress": 75,
				"Completed": 100
			},
			"Site Visit": {
				"Draft": 0,
				"Scheduled": 33,
				"Conducted": 66,
				"Reported": 100
			},
			"Water Sample": {
				"Collected": 20,
				"In Transit": 40,
				"In Lab": 60,
				"Analyzed": 80,
				"Results Available": 100
			},
			"Lab Test Result": {
				"Draft": 0,
				"In Progress": 33,
				"Reviewed": 66,
				"Approved": 100
			},
			"WWTP Technical Proposal": {
				"Draft": 0,
				"Under Review": 50,
				"Approved": 75,
				"Synced to Sales": 100
			},
			"Customer Proposal": {
				"Draft": 0,
				"Under Review": 33,
				"Approved": 66,
				"Sent to Customer": 100
			}
		}
		
		stages = workflow_stages.get(doctype, {})
		status = getattr(doc, 'workflow_status', None) or getattr(doc, 'status', 'Draft')
		progress = stages.get(status, 0)
		
		return {"success": True, "progress": progress, "status": status}
		
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_workflow_timeline(lead_name):
	"""Get complete workflow timeline for a lead"""
	try:
		# Get workflow tracking document
		tracking_docs = frappe.get_all("Workflow Tracking", 
			filters={"lead": lead_name}, 
			limit=1)
		
		if not tracking_docs:
			return {"success": False, "error": "No workflow tracking found for this lead"}
		
		tracking_doc = frappe.get_doc("Workflow Tracking", tracking_docs[0].name)
		
		# Build timeline from stage history
		timeline = []
		for stage in tracking_doc.stage_history:
			timeline.append({
				"stage": stage.stage_name,
				"status": stage.status,
				"document": stage.document_name,
				"date": stage.date,
				"user": stage.user
			})
		
		# Sort by date
		timeline.sort(key=lambda x: x['date'])
		
		return {
			"success": True, 
			"timeline": timeline,
			"completion_percentage": tracking_doc.completion_percentage,
			"current_stage": tracking_doc.current_stage
		}
		
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_workflow_status(doctype, doc_name, new_status):
	"""Update workflow status for a document"""
	try:
		doc = frappe.get_doc(doctype, doc_name)
		
		# Check permissions
		if not frappe.has_permission(doctype, "write", doc):
			return {"success": False, "error": "Insufficient permissions"}
		
		# Update status
		doc.db_set("workflow_status", new_status)
		
		# Update workflow tracking
		from wt_operations.wt_operations.workflow_hooks import update_workflow_tracking
		update_workflow_tracking(doc, doctype, new_status)
		
		return {"success": True, "new_status": new_status}
		
	except Exception as e:
		return {"success": False, "error": str(e)}