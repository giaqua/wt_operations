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
def calculate_site_visit_deadline(priority="Medium", visit_type="Initial Assessment"):
	"""Calculate deadline for site visit request based on priority and type"""
	try:
		from frappe.utils import add_days, nowdate
		
		# Base deadline days based on priority
		priority_days = {
			"Urgent": 1,
			"High": 2,
			"Medium": 3,
			"Low": 5
		}
		
		# Additional days based on visit type
		type_days = {
			"Emergency Visit": 0,
			"Initial Assessment": 0,
			"Technical Survey": 1,
			"Follow-up Visit": 2,
			"Routine Inspection": 3
		}
		
		base_days = priority_days.get(priority, 3)
		additional_days = type_days.get(visit_type, 0)
		total_days = base_days + additional_days
		
		deadline = add_days(nowdate(), total_days)
		
		return {"success": True, "deadline": deadline, "days": total_days}
		
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def send_site_visit_assignment_notification(site_visit_request, assigned_user):
	"""Send notification when site visit request is assigned"""
	try:
		# Get the document
		doc = frappe.get_doc("Site Visit Request", site_visit_request)
		
		# Create notification
		notification = frappe.new_doc("Notification Log")
		notification.subject = f"Site Visit Request Assigned: {doc.name}"
		notification.email_content = f"""
		<p>Dear {frappe.get_value('User', assigned_user, 'full_name')},</p>
		
		<p>You have been assigned a new site visit request:</p>
		
		<ul>
			<li><strong>Request ID:</strong> {doc.name}</li>
			<li><strong>Lead:</strong> {doc.lead}</li>
			<li><strong>Priority:</strong> {doc.priority}</li>
			<li><strong>Visit Date:</strong> {doc.site_visit_date}</li>
			<li><strong>Deadline:</strong> {doc.deadline_date}</li>
		</ul>
		
		<p>Please review the request and take necessary action.</p>
		
		<p>Best regards,<br>WT Operations System</p>
		"""
		notification.document_type = "Site Visit Request"
		notification.document_name = site_visit_request
		notification.from_user = frappe.session.user
		notification.to_user = assigned_user
		notification.insert()
		
		return {"success": True}
		
	except Exception as e:
		frappe.log_error(f"Failed to send assignment notification: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def escalate_overdue_site_visit_requests():
	"""Escalate overdue site visit requests"""
	try:
		from frappe.utils import getdate, nowdate
		
		current_date = getdate(nowdate())
		
		# Find overdue site visit requests
		overdue_requests = frappe.get_all("Site Visit Request",
			filters={
				"deadline_date": ["<", current_date],
				"status": ["not in", ["Completed", "Cancelled"]],
				"docstatus": ["!=", 2]
			},
			fields=["name", "deadline_date", "escalation_level", "assigned_to", "priority"]
		)
		
		escalated_count = 0
		
		for request_info in overdue_requests:
			try:
				doc = frappe.get_doc("Site Visit Request", request_info.name)
				
				# Calculate days overdue
				days_overdue = (current_date - getdate(request_info.deadline_date)).days
				
				# Determine new escalation level
				new_escalation_level = min(days_overdue, 5)  # Max escalation level 5
				
				if new_escalation_level > request_info.escalation_level:
					# Update escalation level
					doc.db_set("escalation_level", new_escalation_level)
					
					# Send escalation notification
					send_escalation_notification(doc, new_escalation_level, days_overdue)
					
					escalated_count += 1
					
			except Exception as e:
				frappe.log_error(f"Error escalating site visit request {request_info.name}: {str(e)}")
		
		return {"success": True, "escalated_count": escalated_count}
		
	except Exception as e:
		frappe.log_error(f"Error in escalate_overdue_site_visit_requests: {str(e)}")
		return {"success": False, "error": str(e)}


def send_escalation_notification(doc, escalation_level, days_overdue):
	"""Send escalation notification for overdue site visit request"""
	try:
		# Determine recipients based on escalation level
		recipients = []
		
		if doc.assigned_to:
			recipients.append(doc.assigned_to)
		
		# Add manager for higher escalation levels
		if escalation_level >= 2:
			# Get Site Manager role users
			site_managers = frappe.get_all("Has Role", 
				filters={"role": "Site Manager"}, 
				fields=["parent"])
			recipients.extend([sm.parent for sm in site_managers])
		
		# Add Operations Manager for critical escalations
		if escalation_level >= 4:
			ops_managers = frappe.get_all("Has Role", 
				filters={"role": "Operations Manager"}, 
				fields=["parent"])
			recipients.extend([om.parent for om in ops_managers])
		
		# Remove duplicates
		recipients = list(set(recipients))
		
		# Send notifications
		for recipient in recipients:
			notification = frappe.new_doc("Notification Log")
			notification.subject = f"ESCALATION Level {escalation_level}: Overdue Site Visit Request {doc.name}"
			notification.email_content = f"""
			<p>Dear {frappe.get_value('User', recipient, 'full_name')},</p>
			
			<p><strong>URGENT:</strong> Site Visit Request {doc.name} is {days_overdue} days overdue and has been escalated to level {escalation_level}.</p>
			
			<ul>
				<li><strong>Request ID:</strong> {doc.name}</li>
				<li><strong>Lead:</strong> {doc.lead}</li>
				<li><strong>Priority:</strong> {doc.priority}</li>
				<li><strong>Original Deadline:</strong> {doc.deadline_date}</li>
				<li><strong>Days Overdue:</strong> {days_overdue}</li>
				<li><strong>Escalation Level:</strong> {escalation_level}</li>
			</ul>
			
			<p>Immediate action is required to resolve this overdue request.</p>
			
			<p>Best regards,<br>WT Operations System</p>
			"""
			notification.document_type = "Site Visit Request"
			notification.document_name = doc.name
			notification.from_user = "Administrator"
			notification.to_user = recipient
			notification.insert()
			
	except Exception as e:
		frappe.log_error(f"Failed to send escalation notification for {doc.name}: {str(e)}")