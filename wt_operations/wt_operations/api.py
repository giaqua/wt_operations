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
