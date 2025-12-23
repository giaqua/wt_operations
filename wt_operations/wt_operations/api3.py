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
def create_lab_test_result_from_sample(water_sample):
	"""Create Lab Test Result from Water Sample"""
	try:
		# Get water sample document
		sample_doc = frappe.get_doc("Water Sample", water_sample)
		
		# Check if lab test result already exists
		existing = frappe.get_all("Lab Test Result", 
			filters={"sample_tag": water_sample}, 
			limit=1)
		
		if existing:
			return {"success": False, "error": "Lab Test Result already exists", "existing_name": existing[0].name}
		
		# Create new Lab Test Result
		lab_test = frappe.new_doc("Lab Test Result")
		lab_test.sample_tag = water_sample
		lab_test.date_sample_received = sample_doc.date_collected
		lab_test.sample_receipt_date = frappe.utils.now_datetime()
		lab_test.test_priority = sample_doc.lab_priority or "Medium"
		lab_test.deadline_date = sample_doc.expected_results_date
		lab_test.compliance_status = "Draft"
		
		# Set lab technician if available
		if sample_doc.collected_by:
			lab_test.lab_technician = sample_doc.collected_by
		
		# Auto-select test template based on sample type
		if sample_doc.sample_type:
			template = get_default_test_template(sample_doc.sample_type)
			if template:
				lab_test.test_template = template
		
		# Save the document
		lab_test.insert()
		
		# Update water sample status
		sample_doc.db_set("sample_status", "In Lab")
		
		return {"success": True, "lab_test_name": lab_test.name}
		
	except Exception as e:
		frappe.log_error(f"Failed to create lab test result from sample: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_test_template_parameters(template_name):
	"""Get parameters from lab test template"""
	try:
		template_doc = frappe.get_doc("Lab Test Template", template_name)
		
		parameters = []
		for param in template_doc.standard_parameters:
			parameters.append({
				"parameter_name": param.parameter_name,
				"unit": param.unit,
				"normal_range": param.normal_range,
				"test_method": param.test_method
			})
		
		return {"success": True, "parameters": parameters}
		
	except Exception as e:
		frappe.log_error(f"Failed to get test template parameters: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def check_lab_result_compliance(lab_test_result, regulatory_standard):
	"""Check lab test result compliance against regulatory standard"""
	try:
		# Get documents
		lab_doc = frappe.get_doc("Lab Test Result", lab_test_result)
		standard_doc = frappe.get_doc("Compliance Standard", regulatory_standard)
		
		non_compliant_parameters = []
		compliant_count = 0
		total_parameters = len(lab_doc.lab_test_results_parameters)
		
		# Check each parameter against standard
		for param in lab_doc.lab_test_results_parameters:
			if not param.result_value:
				continue
				
			# Find matching standard parameter
			standard_param = None
			for std_param in standard_doc.parameters:
				if std_param.parameter_name.lower() == param.parameter_name.lower():
					standard_param = std_param
					break
			
			if standard_param:
				is_compliant = check_parameter_against_standard(
					param.result_value, 
					standard_param.max_limit,
					standard_param.min_limit
				)
				
				if is_compliant:
					compliant_count += 1
					param.compliance_status = "Compliant"
				else:
					non_compliant_parameters.append(param.parameter_name)
					param.compliance_status = "Non-Compliant"
		
		# Determine overall compliance status
		if len(non_compliant_parameters) == 0:
			compliance_status = "Compliant"
		else:
			compliance_status = "Non-Compliant"
		
		# Update lab test result
		lab_doc.compliance_status = compliance_status
		lab_doc.save()
		
		return {
			"success": True, 
			"compliance_status": compliance_status,
			"non_compliant_parameters": non_compliant_parameters,
			"compliance_percentage": (compliant_count / total_parameters) * 100 if total_parameters > 0 else 0
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to check lab result compliance: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_water_sample_from_lab_results(lab_test_result, sample_tag):
	"""Update Water Sample with lab test results"""
	try:
		# Get documents
		lab_doc = frappe.get_doc("Lab Test Result", lab_test_result)
		sample_doc = frappe.get_doc("Water Sample", sample_tag)
		
		# Update water sample with key parameters
		parameter_mapping = {
			"pH": "ph",
			"TSS": "tss", 
			"COD": "cod",
			"BOD5": "bod5",
			"TDS": "tds",
			"Oil & Grease": "oil_grease",
			"E.coli": "ecoli",
			"Turbidity": "turbidity"
		}
		
		for param in lab_doc.lab_test_results_parameters:
			if param.parameter_name in parameter_mapping and param.result_value:
				field_name = parameter_mapping[param.parameter_name]
				sample_doc.db_set(field_name, param.result_value)
		
		# Update status fields
		sample_doc.db_set("sample_status", "Results Available")
		sample_doc.db_set("results_available", 1)
		sample_doc.db_set("analysis_completed", lab_doc.analysis_completion_date or frappe.utils.nowdate())
		sample_doc.db_set("compliance_status", lab_doc.compliance_status)
		
		return {"success": True}
		
	except Exception as e:
		frappe.log_error(f"Failed to update water sample from lab results: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_retest_lab_result(original_test):
	"""Create a retest Lab Test Result for non-compliant results"""
	try:
		# Get original test
		original_doc = frappe.get_doc("Lab Test Result", original_test)
		
		# Create new test document
		retest_doc = frappe.new_doc("Lab Test Result")
		retest_doc.sample_tag = f"{original_doc.sample_tag}-RETEST"
		retest_doc.date_sample_received = original_doc.date_sample_received
		retest_doc.sample_receipt_date = frappe.utils.now_datetime()
		retest_doc.test_priority = "High"  # Retests get high priority
		retest_doc.test_template = original_doc.test_template
		retest_doc.regulatory_standard = original_doc.regulatory_standard
		retest_doc.lab_technician = original_doc.lab_technician
		retest_doc.compliance_status = "Draft"
		
		# Calculate new deadline (shorter for retest)
		from frappe.utils import add_days, nowdate
		retest_doc.deadline_date = add_days(nowdate(), 2)  # 2 days for retest
		
		# Copy parameters from original test
		for param in original_doc.lab_test_results_parameters:
			retest_doc.append("lab_test_results_parameters", {
				"parameter_name": param.parameter_name,
				"unit": param.unit,
				"normal_range": param.normal_range,
				"method": param.method
			})
		
		# Add note about being a retest
		retest_doc.review_notes = f"Retest for non-compliant results from {original_test}"
		
		# Save the document
		retest_doc.insert()
		
		return {"success": True, "retest_name": retest_doc.name}
		
	except Exception as e:
		frappe.log_error(f"Failed to create retest: {str(e)}")
		return {"success": False, "error": str(e)}


def get_default_test_template(sample_type):
	"""Get default test template based on sample type"""
	template_mapping = {
		"Influent": "Influent Analysis Template",
		"Effluent": "Effluent Analysis Template", 
		"Process Water": "Process Water Template",
		"Sludge": "Sludge Analysis Template",
		"Composite": "Comprehensive Analysis Template"
	}
	
	template_name = template_mapping.get(sample_type)
	if template_name:
		# Check if template exists
		if frappe.db.exists("Lab Test Template", template_name):
			return template_name
	
	# Return default template if specific one not found
	default_templates = frappe.get_all("Lab Test Template", 
		filters={"is_default": 1}, 
		limit=1)
	
	if default_templates:
		return default_templates[0].name
	
	return None


def check_parameter_against_standard(result_value, max_limit=None, min_limit=None):
	"""Check if parameter value is within standard limits"""
	try:
		value = float(result_value)
		
		if max_limit is not None and value > float(max_limit):
			return False
			
		if min_limit is not None and value < float(min_limit):
			return False
			
		return True
		
	except (ValueError, TypeError):
		return False