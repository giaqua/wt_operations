# Copyright (c) 2025, WT Operations and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from datetime import datetime, timedelta, date
from frappe.utils import now, add_to_date, get_datetime, formatdate, format_datetime
from frappe.utils.password import get_decrypted_password
from frappe import _


class SyncManager:
	"""Manages cross-site synchronization for workflow documents"""
	
	def _serialize_value(self, value):
		"""Convert date/datetime objects to strings for JSON serialization"""
		if isinstance(value, (date, datetime)):
			if isinstance(value, datetime):
				return value.isoformat()
			else:
				return value.strftime('%Y-%m-%d')
		return value
	
	def _serialize_dict(self, data):
		"""Recursively serialize date/datetime objects in a dictionary"""
		if isinstance(data, dict):
			return {key: self._serialize_dict(value) for key, value in data.items()}
		elif isinstance(data, list):
			return [self._serialize_dict(item) for item in data]
		else:
			return self._serialize_value(data)
	
	def __init__(self, external_site_settings=None):
		if external_site_settings:
			self.site_settings = frappe.get_doc("External Site Settings", external_site_settings)
		else:
			# Get the first enabled external site settings
			settings = frappe.get_all("External Site Settings", 
				filters={"enabled": 1}, limit=1)
			if settings:
				self.site_settings = frappe.get_doc("External Site Settings", settings[0].name)
			else:
				frappe.throw(_("No enabled External Site Settings found"))
	
	def sync_document(self, doctype, docname, sync_type="create"):
		"""Sync a document to external site with retry logic"""
		max_attempts = self.site_settings.sync_retry_attempts or 3
		timeout = self.site_settings.sync_timeout_seconds or 30
		
		for attempt in range(max_attempts):
			try:
				if sync_type == "create":
					result = self._create_document_on_external_site(doctype, docname, timeout)
				elif sync_type == "update":
					result = self._update_document_on_external_site(doctype, docname, timeout)
				else:
					frappe.throw(_("Invalid sync type: {0}").format(sync_type))
				
				# Update sync status on success
				self._update_sync_status(doctype, docname, "Synced", None, result)
				self._log_sync_success(doctype, docname, attempt + 1)
				return result
				
			except Exception as e:
				error_msg = str(e)
				self._log_sync_error(doctype, docname, attempt + 1, error_msg)
				
				if attempt == max_attempts - 1:
					# Final attempt failed
					self._update_sync_status(doctype, docname, "Failed", error_msg, None)
					frappe.throw(_("Sync failed after {0} attempts: {1}").format(max_attempts, error_msg))
				
				# Wait before retry (exponential backoff)
				import time
				time.sleep(2 ** attempt)
	
	def _create_document_on_external_site(self, doctype, docname, timeout):
		"""Create document on external site"""
		doc = frappe.get_doc(doctype, docname)
		
		if doctype == "WWTP Technical Questionnaire":
			return self._sync_technical_questionnaire(doc, timeout)
		elif doctype == "WWTP Technical Proposal":
			return self._sync_technical_proposal(doc, timeout)
		elif doctype == "Customer Proposal":
			return self._sync_customer_proposal(doc, timeout)
		elif doctype == "Site Visit Request":
			return self._sync_site_visit_request(doc, timeout)
		else:
			frappe.throw(_("Sync not supported for doctype: {0}").format(doctype))
	
	def _check_document_exists_on_external_site(self, doctype, docname, headers, site_url):
		"""Check if a document exists on the external site"""
		try:
			response = requests.get(
				f"{site_url}/api/resource/{doctype}/{docname}",
				headers=headers,
				timeout=10,
				verify=True
			)
			return response.status_code == 200
		except:
			return False
	
	def _sync_lead_to_external_site(self, lead_name, timeout):
		"""Sync a Lead document to external site"""
		try:
			# Get the Lead document
			lead_doc = frappe.get_doc("Lead", lead_name)
			
			# Prepare Lead data for sync
			# Use getattr with default None to safely access fields that might not exist
			lead_data = {
				"doctype": "Lead",
				"lead_name": getattr(lead_doc, "lead_name", None),
				"company_name": getattr(lead_doc, "company_name", None),
				"status": getattr(lead_doc, "status", None) or "Open",
				"source": getattr(lead_doc, "source", None),
				"email_id": getattr(lead_doc, "email_id", None),
				"mobile_no": getattr(lead_doc, "mobile_no", None),
				"phone": getattr(lead_doc, "phone", None),
				"type": getattr(lead_doc, "type", None),
				"industry": getattr(lead_doc, "industry", None),
			}
			
			# Add address fields if they exist (Lead may not have direct address fields)
			# In Frappe, address can be in linked Address doctype or as direct fields
			if hasattr(lead_doc, "address_line1"):
				lead_data["address_line1"] = lead_doc.address_line1
			if hasattr(lead_doc, "city"):
				lead_data["city"] = lead_doc.city
			if hasattr(lead_doc, "state"):
				lead_data["state"] = lead_doc.state
			if hasattr(lead_doc, "country"):
				lead_data["country"] = lead_doc.country
			if hasattr(lead_doc, "pincode"):
				lead_data["pincode"] = lead_doc.pincode
			
			# Remove None values and empty strings
			lead_data = {k: v for k, v in lead_data.items() if v is not None and v != ""}
			
			# Serialize dates
			if lead_doc.creation:
				lead_data["creation"] = self._serialize_value(lead_doc.creation)
			if hasattr(lead_doc, 'date') and lead_doc.date:
				lead_data["date"] = self._serialize_value(lead_doc.date)
			
			# Get API headers
			site_url = self.site_settings.site_url.rstrip('/')
			settings_name = self.site_settings.name
			
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
			api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
			
			headers = {
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json"
			}
			
			# Check if Lead already exists
			if self._check_document_exists_on_external_site("Lead", lead_name, headers, site_url):
				frappe.logger().info(f"Lead {lead_name} already exists on external site")
				return lead_name
			
			# Try to create with same name first
			lead_data["name"] = lead_name
			
			response = requests.post(
				f"{site_url}/api/resource/Lead",
				headers=headers,
				json=lead_data,
				timeout=timeout,
				verify=True
			)
			
			if response.status_code == 200:
				result = response.json()
				external_name = result.get("data", {}).get("name")
				frappe.logger().info(f"Lead {lead_name} synced to external site as {external_name}")
				return external_name
			elif response.status_code == 417:
				# Maybe name conflict, try without name (let external site auto-generate)
				lead_data.pop("name", None)
				response = requests.post(
					f"{site_url}/api/resource/Lead",
					headers=headers,
					json=lead_data,
					timeout=timeout,
					verify=True
				)
				if response.status_code == 200:
					result = response.json()
					external_name = result.get("data", {}).get("name")
					frappe.logger().info(f"Lead {lead_name} synced to external site as {external_name} (auto-named)")
					return external_name
				else:
					error_text = response.text[:500] if response.text else "Unknown error"
					frappe.log_error(f"Failed to sync Lead {lead_name}: Status {response.status_code} - {error_text}")
					frappe.throw(_("Failed to sync Lead {0}: {1}").format(lead_name, error_text[:200]))
			else:
				error_text = response.text[:500] if response.text else "Unknown error"
				frappe.log_error(f"Failed to sync Lead {lead_name}: Status {response.status_code} - {error_text}")
				frappe.throw(_("Failed to sync Lead {0}: {1}").format(lead_name, error_text[:200]))
				
		except frappe.DoesNotExistError:
			frappe.throw(_("Lead {0} not found").format(lead_name))
		except Exception as e:
			frappe.log_error(f"Error syncing Lead {lead_name}: {str(e)}")
			frappe.throw(_("Error syncing Lead {0}: {1}").format(lead_name, str(e)))
	
	def _sync_opportunity_to_external_site(self, opp_name, lead_name, timeout):
		"""Sync an Opportunity document to external site"""
		try:
			# Get the Opportunity document
			opp_doc = frappe.get_doc("Opportunity", opp_name)
			
			# Prepare Opportunity data for sync
			# Use getattr with default None to safely access fields that might not exist
			opp_data = {
				"doctype": "Opportunity",
				"opportunity_from": getattr(opp_doc, "opportunity_from", None),
				"party_name": getattr(opp_doc, "party_name", None) or lead_name,  # Use lead if party_name not set
				"opportunity_type": getattr(opp_doc, "opportunity_type", None),
				"status": getattr(opp_doc, "status", None) or "Open",
				"source": getattr(opp_doc, "source", None),
				"contact_email": getattr(opp_doc, "contact_email", None),
				"contact_mobile": getattr(opp_doc, "contact_mobile", None),
				"contact_person": getattr(opp_doc, "contact_person", None),
			}
			
			# Add expected_closing if it exists
			if hasattr(opp_doc, "expected_closing") and opp_doc.expected_closing:
				opp_data["expected_closing"] = self._serialize_value(opp_doc.expected_closing)
			
			# Remove None values and empty strings
			opp_data = {k: v for k, v in opp_data.items() if v is not None and v != ""}
			
			# Get API headers
			site_url = self.site_settings.site_url.rstrip('/')
			settings_name = self.site_settings.name
			
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
			api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
			
			headers = {
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json"
			}
			
			# Check if Opportunity already exists
			if self._check_document_exists_on_external_site("Opportunity", opp_name, headers, site_url):
				frappe.logger().info(f"Opportunity {opp_name} already exists on external site")
				return opp_name
			
			# Try to create with same name first
			opp_data["name"] = opp_name
			
			response = requests.post(
				f"{site_url}/api/resource/Opportunity",
				headers=headers,
				json=opp_data,
				timeout=timeout,
				verify=True
			)
			
			if response.status_code == 200:
				result = response.json()
				external_name = result.get("data", {}).get("name")
				frappe.logger().info(f"Opportunity {opp_name} synced to external site as {external_name}")
				return external_name
			elif response.status_code == 417:
				# Maybe name conflict, try without name (let external site auto-generate)
				opp_data.pop("name", None)
				response = requests.post(
					f"{site_url}/api/resource/Opportunity",
					headers=headers,
					json=opp_data,
					timeout=timeout,
					verify=True
				)
				if response.status_code == 200:
					result = response.json()
					external_name = result.get("data", {}).get("name")
					frappe.logger().info(f"Opportunity {opp_name} synced to external site as {external_name} (auto-named)")
					return external_name
				else:
					error_text = response.text[:500] if response.text else "Unknown error"
					frappe.log_error(f"Failed to sync Opportunity {opp_name}: Status {response.status_code} - {error_text}")
					frappe.throw(_("Failed to sync Opportunity {0}: {1}").format(opp_name, error_text[:200]))
			else:
				error_text = response.text[:500] if response.text else "Unknown error"
				frappe.log_error(f"Failed to sync Opportunity {opp_name}: Status {response.status_code} - {error_text}")
				frappe.throw(_("Failed to sync Opportunity {0}: {1}").format(opp_name, error_text[:200]))
				
		except frappe.DoesNotExistError:
			frappe.throw(_("Opportunity {0} not found").format(opp_name))
		except Exception as e:
			frappe.log_error(f"Error syncing Opportunity {opp_name}: {str(e)}")
			frappe.throw(_("Error syncing Opportunity {0}: {1}").format(opp_name, str(e)))
	
	def _sync_scope_of_work_to_external_site(self, scope_name, timeout):
		"""Sync a Scope Of Work document to external site"""
		try:
			# Get the Scope Of Work document
			scope_doc = frappe.get_doc("Scope Of Work", scope_name)
			
			# Prepare Scope Of Work data for sync
			scope_data = {
				"doctype": "Scope Of Work",
				"scope_of_work": scope_doc.scope_of_work,
				"scope_of_work_details": getattr(scope_doc, "scope_of_work_details", None),
			}
			
			# Remove None values and empty strings
			scope_data = {k: v for k, v in scope_data.items() if v is not None and v != ""}
			
			# Get API headers
			site_url = self.site_settings.site_url.rstrip('/')
			settings_name = self.site_settings.name
			
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
			api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
			
			headers = {
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json"
			}
			
			# Check if Scope Of Work already exists (by name since autoname is by fieldname)
			# Try to get the document - if it exists, the name will be the scope_of_work value
			if self._check_document_exists_on_external_site("Scope Of Work", scope_name, headers, site_url):
				frappe.logger().info(f"Scope Of Work {scope_name} already exists on external site")
				return scope_name
			
			# Try to create with same name (scope_of_work field value is the name)
			scope_data["name"] = scope_name
			
			response = requests.post(
				f"{site_url}/api/resource/Scope Of Work",
				headers=headers,
				json=scope_data,
				timeout=timeout,
				verify=True
			)
			
			if response.status_code == 200:
				result = response.json()
				external_name = result.get("data", {}).get("name")
				frappe.logger().info(f"Scope Of Work {scope_name} synced to external site as {external_name}")
				return external_name
			elif response.status_code == 417:
				# Maybe name conflict, try without name (let external site auto-generate)
				scope_data.pop("name", None)
				response = requests.post(
					f"{site_url}/api/resource/Scope Of Work",
					headers=headers,
					json=scope_data,
					timeout=timeout,
					verify=True
				)
				if response.status_code == 200:
					result = response.json()
					external_name = result.get("data", {}).get("name")
					frappe.logger().info(f"Scope Of Work {scope_name} synced to external site as {external_name} (auto-named)")
					return external_name
				else:
					error_text = response.text[:500] if response.text else "Unknown error"
					frappe.log_error(f"Failed to sync Scope Of Work {scope_name}: Status {response.status_code} - {error_text}")
					frappe.throw(_("Failed to sync Scope Of Work {0}: {1}").format(scope_name, error_text[:200]))
			else:
				error_text = response.text[:500] if response.text else "Unknown error"
				frappe.log_error(f"Failed to sync Scope Of Work {scope_name}: Status {response.status_code} - {error_text}")
				frappe.throw(_("Failed to sync Scope Of Work {0}: {1}").format(scope_name, error_text[:200]))
				
		except frappe.DoesNotExistError:
			frappe.throw(_("Scope Of Work {0} not found").format(scope_name))
		except Exception as e:
			frappe.log_error(f"Error syncing Scope Of Work {scope_name}: {str(e)}")
			frappe.throw(_("Error syncing Scope Of Work {0}: {1}").format(scope_name, str(e)))
	
	def _sync_all_scope_of_work_documents(self, timeout):
		"""Sync all Scope Of Work documents to external site"""
		try:
			# Get all Scope Of Work documents
			all_scopes = frappe.get_all("Scope Of Work", fields=["name"])
			
			if not all_scopes:
				frappe.logger().info("No Scope Of Work documents found to sync")
				return
			
			# Get API headers
			site_url = self.site_settings.site_url.rstrip('/')
			settings_name = self.site_settings.name
			
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
			api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
			
			headers = {
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json"
			}
			
			# Sync each Scope Of Work document
			synced_count = 0
			for scope in all_scopes:
				try:
					if not self._check_document_exists_on_external_site("Scope Of Work", scope.name, headers, site_url):
						frappe.logger().info(f"Syncing Scope Of Work {scope.name}...")
						self._sync_scope_of_work_to_external_site(scope.name, timeout)
						synced_count += 1
					else:
						frappe.logger().info(f"Scope Of Work {scope.name} already exists on external site")
				except Exception as e:
					frappe.log_error(f"Failed to sync Scope Of Work {scope.name}: {str(e)}")
					# Continue with other scopes even if one fails
			
			frappe.logger().info(f"Synced {synced_count} new Scope Of Work documents to external site")
			
		except Exception as e:
			frappe.log_error(f"Error syncing all Scope Of Work documents: {str(e)}")
			# Don't throw - allow TQ sync to continue even if some scopes fail
	
	def _sync_technical_questionnaire(self, doc, timeout):
		"""Sync Technical Questionnaire to external site"""
		if not self.site_settings.sync_technical_questionnaires:
			frappe.throw(_("Technical Questionnaire sync is disabled"))
		
		# First, ensure Lead and Opportunity exist on external site
		site_url = self.site_settings.site_url.rstrip('/')
		settings_name = self.site_settings.name
		
		api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
		api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
		
		api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
		api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
		
		headers = {
			"Authorization": f"token {api_key}:{api_secret}",
			"Content-Type": "application/json"
		}
		
		# Check and sync Lead if needed
		if doc.lead:
			if not self._check_document_exists_on_external_site("Lead", doc.lead, headers, site_url):
				frappe.logger().info(f"Lead {doc.lead} not found on external site, syncing it first...")
				try:
					self._sync_lead_to_external_site(doc.lead, timeout)
				except Exception as e:
					frappe.log_error(f"Failed to sync Lead {doc.lead} before syncing TQ: {str(e)}")
					frappe.throw(_("Cannot sync Technical Questionnaire: Failed to sync Lead {0} first. Error: {1}").format(doc.lead, str(e)))
		
		# Check and sync Opportunity if needed
		if doc.opportunity:
			if not self._check_document_exists_on_external_site("Opportunity", doc.opportunity, headers, site_url):
				frappe.logger().info(f"Opportunity {doc.opportunity} not found on external site, syncing it first...")
				try:
					self._sync_opportunity_to_external_site(doc.opportunity, doc.lead, timeout)
				except Exception as e:
					frappe.log_error(f"Failed to sync Opportunity {doc.opportunity} before syncing TQ: {str(e)}")
					frappe.throw(_("Cannot sync Technical Questionnaire: Failed to sync Opportunity {0} first. Error: {1}").format(doc.opportunity, str(e)))
		
		# Sync all Scope Of Work documents to ensure they exist on external site
		frappe.logger().info("Syncing all Scope Of Work documents to external site...")
		self._sync_all_scope_of_work_documents(timeout)
		
		# Also sync any Scope Of Work documents referenced in the TQ child table
		if hasattr(doc, "tq_roles_and_responsibilities") and doc.tq_roles_and_responsibilities:
			scope_references = set()
			for row in doc.tq_roles_and_responsibilities:
				if hasattr(row, "scope_of_work") and row.scope_of_work:
					scope_references.add(row.scope_of_work)
			
			# Sync each referenced Scope Of Work
			for scope_name in scope_references:
				try:
					if not self._check_document_exists_on_external_site("Scope Of Work", scope_name, headers, site_url):
						frappe.logger().info(f"Scope Of Work {scope_name} referenced in TQ not found on external site, syncing it...")
						self._sync_scope_of_work_to_external_site(scope_name, timeout)
				except Exception as e:
					frappe.log_error(f"Failed to sync Scope Of Work {scope_name} before syncing TQ: {str(e)}")
					frappe.throw(_("Cannot sync Technical Questionnaire: Failed to sync Scope Of Work {0} first. Error: {1}").format(scope_name, str(e)))
		
		# Prepare minimal data for external site (only essential fields to reduce payload size)
		# Exclude child tables initially to keep payload small
		# Note: Lead must exist on external site before syncing
		sync_data = {
			"doctype": "WWTP Technical Questionnaire",
			"lead": doc.lead,
			"date": self._serialize_value(doc.date) if doc.date else None,
			"by": doc.by,
			"wastewater_generator_type": doc.wastewater_generator_type,
			"capacity": doc.capacity,
			"is_it_new_wwtp_or_an_upgrade": doc.is_it_new_wwtp_or_an_upgrade or "New",
			"site_visit_required": doc.site_visit_required,
			"sample_collection_required": doc.sample_collection_required,
			# Add workflow fields
			"workflow_status": "Synced to Operations",
			"sync_status": "Synced",
			# Mark as synced from sales and set source site
			"is_synced_from_sales": 1,
			"synced_from_site": getattr(frappe.local, "site", None) or frappe.conf.get("site_name") or "Sales Site"
		}
		
		# Only include opportunity if it exists (to avoid LinkValidationError)
		if doc.opportunity:
			sync_data["opportunity"] = doc.opportunity
		
		# Only include location if it exists
		if doc.location_of_the_wwtp_needed:
			sync_data["location_of_the_wwtp_needed"] = doc.location_of_the_wwtp_needed
		
		# Only include optional fields if they have values (to reduce payload)
		# Truncate long text fields to prevent "Value too big" errors
		optional_fields = {
			"the_available_footprint_dedicated_for_stp_in_sm": doc.the_available_footprint_dedicated_for_stp_in_sm,
			"daily_flow": doc.daily_flow,
			"operation_hours": doc.operation_hours,
			"average_hourly_flow": doc.average_hourly_flow,
			"peak_factor": getattr(doc, "peak_factor", None),
			"peak_hours": getattr(doc, "peak_hours", None),
			"min_flow": getattr(doc, "min_flow", None),
			"special_case_generator_type": getattr(doc, "special_case_generator_type", None),
			"number_of_streams": getattr(doc, "number_of_streams", None),
			"available_equipment__tanks_pumpsect": getattr(doc, "available_equipment__tanks_pumpsect", None),
			"design_of_the_site_condition": getattr(doc, "design_of_the_site_condition", None),
			# Effluent quality fields
			"please_pick_the_target_effluent_type": getattr(doc, "please_pick_the_target_effluent_type", None),
			"ph_eff": getattr(doc, "ph_eff", None),
			"tss_eff": getattr(doc, "tss_eff", None),
			"bod5_eff": getattr(doc, "bod5_eff", None),
			"cod_eff": getattr(doc, "cod_eff", None),
			"turbidity_eff": getattr(doc, "turbidity_eff", None),
			"oil_grease_eff": getattr(doc, "oil_grease_eff", None),
			"tds_eff": getattr(doc, "tds_eff", None),
			"free_chlorine": getattr(doc, "free_chlorine", None),
			"ecoli": getattr(doc, "ecoli", None),
			"wormies": getattr(doc, "wormies", None),
		}
		
		# Add optional fields only if they exist and are not empty
		# Truncate string fields to 140 characters to prevent database errors
		for key, value in optional_fields.items():
			if value:
				if isinstance(value, str) and len(value) > 140:
					value = value[:140]
				sync_data[key] = value
		
		# Include child tables: tq_influent_stream and tq_roles_and_responsibilities
		# Prepare tq_influent_stream child table
		if hasattr(doc, "tq_influent_stream") and doc.tq_influent_stream:
			tq_influent_stream_data = []
			for row in doc.tq_influent_stream:
				row_data = {
					"parameter": getattr(row, "parameter", None),
					"ph": getattr(row, "ph", None),
					"tss": getattr(row, "tss", None),
					"turbidity": getattr(row, "turbidity", None),
					"temperature": getattr(row, "temperature", None),
					"cod": getattr(row, "cod", None),
					"bod5": getattr(row, "bod5", None),
					"tds": getattr(row, "tds", None),
					"total_chlorinates_hydrocarbons": getattr(row, "total_chlorinates_hydrocarbons", None),
					"oil_grease": getattr(row, "oil_grease", None),
					"phenol": getattr(row, "phenol", None),
					"arsenic": getattr(row, "arsenic", None),
					"po4_p": getattr(row, "po4_p", None),
					"sulphate": getattr(row, "sulphate", None),
					"tkn": getattr(row, "tkn", None),
				}
				# Remove None values and empty strings
				row_data = {k: v for k, v in row_data.items() if v is not None and v != ""}
				if row_data:  # Only add non-empty rows
					tq_influent_stream_data.append(row_data)
			
			if tq_influent_stream_data:
				sync_data["tq_influent_stream"] = tq_influent_stream_data
		
		# Prepare tq_roles_and_responsibilities child table
		if hasattr(doc, "tq_roles_and_responsibilities") and doc.tq_roles_and_responsibilities:
			tq_roles_data = []
			for row in doc.tq_roles_and_responsibilities:
				row_data = {
					"scope_of_work": getattr(row, "scope_of_work", None),
					"responsible": getattr(row, "responsible", None),
					"not_required": getattr(row, "not_required", 0),
					"remarks": getattr(row, "remarks", None),
				}
				# Remove None values (but keep 0 for not_required)
				row_data = {k: v for k, v in row_data.items() if v is not None and (k == "not_required" or v != "")}
				# Truncate remarks if too long
				if row_data.get("remarks") and isinstance(row_data["remarks"], str) and len(row_data["remarks"]) > 140:
					row_data["remarks"] = row_data["remarks"][:140]
				if row_data:  # Only add non-empty rows
					tq_roles_data.append(row_data)
			
			if tq_roles_data:
				sync_data["tq_roles_and_responsibilities"] = tq_roles_data
		
		# Remove None values and empty strings to reduce payload size
		sync_data = {k: v for k, v in sync_data.items() if v is not None and v != ""}
		
		# Serialize the entire payload to ensure all date/datetime objects are converted
		sync_data = self._serialize_dict(sync_data)
		
		# Send to external site
		site_url = self.site_settings.site_url.rstrip('/')
		
		# Get API headers - ensure we have a fresh document reference
		# Get credentials directly to avoid any issues with document state
		try:
			# Get settings name - handle both string and document object
			if isinstance(self.site_settings, str):
				settings_name = self.site_settings
				self.site_settings = frappe.get_doc("External Site Settings", settings_name)
			else:
				settings_name = self.site_settings.name
			
			# Ensure we have a valid document
			if not settings_name:
				frappe.throw(_("External Site Settings name is missing"))
			
			# Reload to ensure fresh data
			self.site_settings = frappe.get_doc("External Site Settings", settings_name)
			
			# Get credentials directly using the settings name
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			# Validate and clean credentials
			if not api_key or not api_secret:
				frappe.throw(_("API Key or API Secret is missing. Please check External Site Settings."))
			
			api_key = str(api_key).strip()
			api_secret = str(api_secret).strip()
			
			# Remove any newlines or carriage returns that might have been added
			api_key = api_key.replace('\n', '').replace('\r', '')
			api_secret = api_secret.replace('\n', '').replace('\r', '')
			
			# Debug: Verify credentials are not encrypted
			if api_key.startswith('$') or api_secret.startswith('$'):
				frappe.log_error(f"Credentials appear to be encrypted for {settings_name}")
				frappe.throw(_("Credentials decryption failed. Please re-enter API credentials in External Site Settings."))
			
			# Build authorization header - ensure no extra whitespace
			auth_value = f"token {api_key}:{api_secret}"
			
			# Build headers
			headers = {
				"Authorization": auth_value,
				"Content-Type": "application/json"
			}
			
			# Debug log (without exposing credentials)
			frappe.logger().debug(f"API headers prepared for {settings_name}, auth length: {len(auth_value)}")
			frappe.logger().debug(f"API key length: {len(api_key)}, API secret length: {len(api_secret)}")
			# Verify the header doesn't have unexpected characters
			if '\n' in auth_value or '\r' in auth_value:
				frappe.log_error(f"Authorization header contains newlines for {settings_name}")
				frappe.throw(_("Authorization header contains invalid characters. Please check API credentials."))
			
			# Verify API key format (should be alphanumeric, no special chars except maybe dashes)
			if not api_key.replace('-', '').replace('_', '').isalnum():
				frappe.logger().warning(f"API key contains unexpected characters for {settings_name}")
			
			# Verify API secret format
			if not api_secret.replace('-', '').replace('_', '').isalnum():
				frappe.logger().warning(f"API secret contains unexpected characters for {settings_name}")
			
		except Exception as e:
			frappe.log_error(f"Failed to get API headers for {getattr(self.site_settings, 'name', 'unknown')}: {str(e)}")
			frappe.throw(_("Failed to get API credentials: {0}").format(str(e)))
		
		# Log request for debugging (without sensitive data)
		frappe.logger().info(f"Syncing WWTP Technical Questionnaire {doc.name} to {site_url}")
		
		# Calculate payload size for debugging
		payload_json = json.dumps(sync_data)
		payload_size = len(payload_json.encode('utf-8'))
		frappe.logger().info(f"Payload size: {payload_size} bytes ({len(payload_json)} chars)")
		
		# If payload is too large, log warning
		if payload_size > 500000:  # 500KB limit
			frappe.logger().warning(f"Payload size ({payload_size} bytes) may be too large")
		
		try:
			# Debug: Log header info (without exposing credentials)
			auth_header = headers.get('Authorization', '')
			frappe.logger().info(f"Request headers prepared, Authorization length: {len(auth_header)}")
			frappe.logger().info(f"Request URL: {site_url}/api/resource/WWTP Technical Questionnaire")
			
			# Verify header format matches expected pattern
			if not auth_header.startswith('token '):
				frappe.log_error(f"Invalid Authorization header format: {auth_header[:20]}...", "Sync Header Error")
				frappe.throw(_("Invalid Authorization header format. Please check API credentials."))
			
			# Make the request - ensure headers are properly formatted
			response = requests.post(
				f"{site_url}/api/resource/WWTP Technical Questionnaire",
				headers=headers,
				json=sync_data,
				timeout=timeout,
				verify=True,
				allow_redirects=False  # Don't follow redirects which might lose auth headers
			)
			
			# Log response for debugging
			frappe.logger().info(f"Response status: {response.status_code}")
			if response.status_code != 200:
				frappe.logger().error(f"Response error: {response.text[:1000]}")
		
		except requests.exceptions.RequestException as e:
			error_msg = f"Network error when syncing: {str(e)}"
			frappe.log_error(f"Request exception when syncing {doc.name}: {str(e)}", "Sync Network Error")
			doc.db_set("sync_status", "Failed")
			doc.db_set("sync_error_message", error_msg[:140])  # Truncate for field limit
			frappe.throw(_(error_msg))
		
		if response.status_code == 200:
			result = response.json()
			external_name = result.get("data", {}).get("name")
			
			# Update local document with sync info
			doc.db_set("sync_status", "Synced")
			doc.db_set("workflow_status", "Synced to Operations")
			
			return external_name
		elif response.status_code == 401:
			# Try to get more details from the response
			try:
				error_data = response.json()
				error_detail = error_data.get("exc", "") or error_data.get("message", "")
				# Check if it's actually a LinkValidationError masquerading as 401
				if "LinkValidationError" in str(error_detail) or "Could not find" in str(error_detail):
					# Extract missing links from error
					missing_links = []
					if doc.lead and f"Lead: {doc.lead}" in str(error_detail):
						missing_links.append(f"Lead: {doc.lead}")
					if doc.opportunity and f"Opportunity: {doc.opportunity}" in str(error_detail):
						missing_links.append(f"Opportunity: {doc.opportunity}")
					
					error_msg = f"Link validation failed: The following documents do not exist on the external site:\n\n{', '.join(missing_links)}\n\nPlease ensure these documents exist on the external site before syncing."
					frappe.log_error(f"Link validation error when syncing {doc.name}: {error_detail}", "Sync Link Validation Error")
					frappe.throw(_(error_msg))
			except:
				error_detail = response.text[:1000]
			
			error_msg = "Authentication failed. Please verify:\n1. API Key and Secret are correct\n2. API credentials are valid on the external site\n3. Test connection works in External Site Settings\n4. The API user has permission to create WWTP Technical Questionnaire documents"
			frappe.log_error(f"Authentication error when syncing {doc.name}: {error_detail}", "Sync Authentication Error")
			frappe.throw(_(error_msg))
		elif response.status_code == 417:
			# 417 = Expectation Failed - usually validation errors
			try:
				error_data = response.json()
				error_detail = error_data.get("exc", "") or error_data.get("message", "") or error_data.get("exception", "")
				
				# Check for LinkValidationError
				if "LinkValidationError" in error_detail or "Could not find" in error_detail:
					# Extract missing documents from error message using regex
					import re
					missing_leads = []
					missing_opportunities = []
					missing_scopes = []
					
					# Extract Lead name from error (handle format: "Lead: CRM-LEAD-2025-00001" or "Could not find Lead: CRM-LEAD-2025-00001")
					lead_patterns = [
						r'Lead:\s*([^\s,)]+)',
						r'Could not find Lead:\s*([^\s,)]+)'
					]
					for pattern in lead_patterns:
						lead_match = re.search(pattern, error_detail)
						if lead_match:
							missing_leads.append(lead_match.group(1))
							break
					
					# Extract Opportunity name from error
					opp_patterns = [
						r'Opportunity:\s*([^\s,)]+)',
						r'Could not find Opportunity:\s*([^\s,)]+)'
					]
					for pattern in opp_patterns:
						opp_match = re.search(pattern, error_detail)
						if opp_match:
							missing_opportunities.append(opp_match.group(1))
							break
					
					# Extract Scope Of Work from error (handle format: "Row #1: Scope Of Work: Chemical Consumption...")
					scope_patterns = [
						r'Scope Of Work:\s*([^\n,]+)',
						r'Row #\d+:\s*Scope Of Work:\s*([^\n,]+)'
					]
					for pattern in scope_patterns:
						scope_matches = re.findall(pattern, error_detail)
						if scope_matches:
							# Clean up scope names (remove trailing periods, extra spaces)
							for scope_match in scope_matches:
								scope_name = scope_match.strip().rstrip('.')
								if scope_name and scope_name not in missing_scopes:
									missing_scopes.append(scope_name)
					
					# Try to auto-sync missing documents
					synced = False
					if missing_leads and doc.lead in missing_leads:
						try:
							frappe.logger().info(f"Auto-syncing missing Lead {doc.lead}...")
							self._sync_lead_to_external_site(doc.lead, timeout)
							synced = True
							# Retry the TQ sync after syncing Lead
							frappe.logger().info(f"Retrying Technical Questionnaire sync after syncing Lead...")
							return self._sync_technical_questionnaire(doc, timeout)
						except Exception as e:
							frappe.log_error(f"Failed to auto-sync Lead {doc.lead}: {str(e)}")
					
					if missing_opportunities and doc.opportunity and doc.opportunity in missing_opportunities:
						try:
							frappe.logger().info(f"Auto-syncing missing Opportunity {doc.opportunity}...")
							self._sync_opportunity_to_external_site(doc.opportunity, doc.lead, timeout)
							synced = True
							# Retry the TQ sync after syncing Opportunity
							frappe.logger().info(f"Retrying Technical Questionnaire sync after syncing Opportunity...")
							return self._sync_technical_questionnaire(doc, timeout)
						except Exception as e:
							frappe.log_error(f"Failed to auto-sync Opportunity {doc.opportunity}: {str(e)}")
					
					# Try to auto-sync missing Scope Of Work documents
					if missing_scopes:
						try:
							for scope_name in missing_scopes:
								frappe.logger().info(f"Auto-syncing missing Scope Of Work {scope_name}...")
								try:
									self._sync_scope_of_work_to_external_site(scope_name, timeout)
									synced = True
								except frappe.DoesNotExistError:
									# Scope doesn't exist locally, skip it
									frappe.logger().warning(f"Scope Of Work {scope_name} not found locally, skipping...")
									continue
								except Exception as e:
									frappe.log_error(f"Failed to auto-sync Scope Of Work {scope_name}: {str(e)}")
							
							if synced:
								# Retry the TQ sync after syncing Scope Of Work
								frappe.logger().info(f"Retrying Technical Questionnaire sync after syncing Scope Of Work documents...")
								return self._sync_technical_questionnaire(doc, timeout)
						except Exception as e:
							frappe.log_error(f"Failed to auto-sync Scope Of Work documents: {str(e)}")
					
					# If we couldn't auto-sync, show error
					missing_docs = []
					if missing_leads:
						missing_docs.extend([f"Lead: {lead}" for lead in missing_leads])
					if missing_opportunities:
						missing_docs.extend([f"Opportunity: {opp}" for opp in missing_opportunities])
					if missing_scopes:
						missing_docs.extend([f"Scope Of Work: {scope}" for scope in missing_scopes[:10]])  # Limit to first 10
						if len(missing_scopes) > 10:
							missing_docs.append(f"... and {len(missing_scopes) - 10} more Scope Of Work documents")
					
					if missing_docs:
						error_msg = f"Cannot sync: The following documents do not exist on the external site:\n\n{chr(10).join(missing_docs)}\n\nAttempted to auto-sync but failed. Please ensure these documents exist on the external site before syncing."
					else:
						# Fallback: extract any document references
						doc_refs = re.findall(r'([A-Z]+-[A-Z]+-[0-9-]+)', error_detail)
						if doc_refs:
							error_msg = f"Cannot sync: The following documents may not exist on the external site: {', '.join(set(doc_refs))}\n\nPlease ensure all linked documents exist on the external site before syncing."
						else:
							error_msg = f"Link validation failed: {error_detail[:200]}\n\nPlease ensure all linked documents (Lead, Opportunity, Scope Of Work) exist on the external site before syncing."
					
					# Log full error (without truncation)
					frappe.log_error(
						f"Link validation error when syncing {doc.name}: {error_detail}",
						"Sync Link Validation Error"
					)
					
					# Update sync status with truncated message
					doc.db_set("sync_status", "Failed")
					error_summary = "Missing documents on external site"
					doc.db_set("sync_error_message", error_summary[:140])  # Ensure it fits in field
					
					frappe.throw(_(error_msg))
				else:
					# Other validation errors
					error_msg = f"Validation error: {error_detail[:200]}"
					frappe.log_error(f"Validation error when syncing {doc.name}: {error_detail}", "Sync Validation Error")
					doc.db_set("sync_status", "Failed")
					doc.db_set("sync_error_message", error_msg[:140])  # Truncate for field limit
					frappe.throw(_(error_msg))
			except Exception as parse_error:
				error_text = response.text[:500] if response.text else "Unknown validation error"
				frappe.log_error(f"Error parsing 417 response for {doc.name}: {str(parse_error)}. Response: {error_text}", "Sync Error Parsing")
				doc.db_set("sync_status", "Failed")
				doc.db_set("sync_error_message", "Validation error (417)")
				frappe.throw(_("Validation error when syncing: {0}").format(error_text[:200]))
		else:
			# Other status codes
			error_text = response.text[:1000] if response.text else "Unknown error"
			frappe.log_error(f"Sync failed for {doc.name}: Status {response.status_code} - {error_text}", "Sync Error")
			doc.db_set("sync_status", "Failed")
			doc.db_set("sync_error_message", f"HTTP {response.status_code}: {error_text[:100]}")
			frappe.throw(_("Failed to sync Technical Questionnaire (HTTP {0}): {1}").format(response.status_code, error_text[:300]))
	
	def _sync_technical_proposal(self, doc, timeout):
		"""Sync Technical Proposal to external site"""
		if not self.site_settings.sync_technical_proposals:
			frappe.throw(_("Technical Proposal sync is disabled"))
		
		# Prepare comprehensive data for external site
		sync_data = {
			"doctype": "WWTP Technical Proposal",
			"lead": doc.lead,
			"customer": doc.customer,
			"opportunity": doc.opportunity,
			"wwtp_technical_questionnaire": doc.wwtp_technical_questionnaire,
			"site_visit": doc.site_visit,
			"water_sample": doc.water_sample,
			"proposal_date": self._serialize_value(doc.proposal_date) if doc.proposal_date else None,
			"valid_until": self._serialize_value(doc.valid_until) if doc.valid_until else None,
			"prepared_by": doc.prepared_by,
			"technical_manager": doc.technical_manager,
			"project_title": doc.project_title,
			"project_description": doc.project_description,
			"wastewater_generator_type": doc.wastewater_generator_type,
			"design_capacity": doc.design_capacity,
			"treatment_technology": doc.treatment_technology,
			"process_description": doc.process_description,
			"equipment_cost": doc.equipment_cost,
			"civil_works_cost": doc.civil_works_cost,
			"total_project_cost": doc.total_project_cost,
			# Add workflow fields
			"workflow_status": "Synced to Sales",
			"review_status": "Approved"
		}
		
		# Remove None values and empty strings to reduce payload size
		sync_data = {k: v for k, v in sync_data.items() if v is not None and v != ""}
		
		# Serialize the entire payload to ensure all date/datetime objects are converted
		sync_data = self._serialize_dict(sync_data)
		
		# Send to external site
		site_url = self.site_settings.site_url.rstrip('/')
		
		# Get API headers - get credentials directly
		try:
			settings_name = self.site_settings.name
			self.site_settings = frappe.get_doc("External Site Settings", settings_name)
			
			# Get credentials directly
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			if not api_key or not api_secret:
				frappe.throw(_("API Key or API Secret is missing."))
			
			headers = {
				"Authorization": f"token {api_key.strip()}:{api_secret.strip()}",
				"Content-Type": "application/json"
			}
		except Exception as e:
			frappe.log_error(f"Failed to get API headers: {str(e)}")
			frappe.throw(_("Failed to get API credentials. Please check External Site Settings."))
		
		try:
			response = requests.post(
				f"{site_url}/api/resource/WWTP Technical Proposal",
				headers=headers,
				json=sync_data,
				timeout=timeout,
				verify=True
			)
		except requests.exceptions.RequestException as e:
			frappe.log_error(f"Request exception: {str(e)}")
			frappe.throw(_("Network error when syncing: {0}").format(str(e)))
		
		if response.status_code == 200:
			result = response.json()
			external_name = result.get("data", {}).get("name")
			
			# Update local document with sync info
			doc.db_set("workflow_status", "Synced to Sales")
			
			return external_name
		else:
			frappe.throw(_("Failed to sync Technical Proposal: {0}").format(response.text))
	
	def _sync_customer_proposal(self, doc, timeout):
		"""Sync Customer Proposal to external site"""
		if not self.site_settings.sync_customer_proposals:
			frappe.throw(_("Customer Proposal sync is disabled"))
		
		# Prepare data for external site
		sync_data = {
			"doctype": "Customer Proposal",
			"customer": doc.customer,
			"lead": doc.lead,
			"opportunity": doc.opportunity,
			"wwtp_technical_proposal": doc.wwtp_technical_proposal,
			"issue_date": self._serialize_value(doc.issue_date) if doc.issue_date else None,
			"valid_up_to": self._serialize_value(doc.valid_up_to) if doc.valid_up_to else None,
			"project_title": doc.project_title,
			"project_description": doc.project_description,
			"treatment_technology": doc.treatment_technology,
			# Add workflow fields
			"workflow_status": "Sent to Customer"
		}
		
		# Remove None values and empty strings to reduce payload size
		sync_data = {k: v for k, v in sync_data.items() if v is not None and v != ""}
		
		# Serialize the entire payload to ensure all date/datetime objects are converted
		sync_data = self._serialize_dict(sync_data)
		
		# Send to external site
		site_url = self.site_settings.site_url.rstrip('/')
		
		# Get API headers - get credentials directly
		try:
			settings_name = self.site_settings.name
			self.site_settings = frappe.get_doc("External Site Settings", settings_name)
			
			# Get credentials directly
			api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
			api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
			
			if not api_key or not api_secret:
				frappe.throw(_("API Key or API Secret is missing."))
			
			headers = {
				"Authorization": f"token {api_key.strip()}:{api_secret.strip()}",
				"Content-Type": "application/json"
			}
		except Exception as e:
			frappe.log_error(f"Failed to get API headers: {str(e)}")
			frappe.throw(_("Failed to get API credentials. Please check External Site Settings."))
		
		try:
			response = requests.post(
				f"{site_url}/api/resource/Customer Proposal",
				headers=headers,
				json=sync_data,
				timeout=timeout,
				verify=True
			)
		except requests.exceptions.RequestException as e:
			frappe.log_error(f"Request exception: {str(e)}")
			frappe.throw(_("Network error when syncing: {0}").format(str(e)))
		
		if response.status_code == 200:
			result = response.json()
			external_name = result.get("data", {}).get("name")
			
			# Update local document with sync info
			doc.db_set("workflow_status", "Sent to Customer")
			
			return external_name
		else:
			frappe.throw(_("Failed to sync Customer Proposal: {0}").format(response.text))
	
	def _sync_site_visit_request(self, doc, timeout):
		"""Sync Site Visit Request to external site"""
		# Note: We'll sync even if sync_site_visit_requests field doesn't exist (for backward compatibility)
		# First, ensure Lead exists on external site
		site_url = self.site_settings.site_url.rstrip('/')
		settings_name = self.site_settings.name
		
		api_key = get_decrypted_password("External Site Settings", settings_name, "api_key")
		api_secret = get_decrypted_password("External Site Settings", settings_name, "api_secret")
		
		api_key = str(api_key).strip().replace('\n', '').replace('\r', '')
		api_secret = str(api_secret).strip().replace('\n', '').replace('\r', '')
		
		headers = {
			"Authorization": f"token {api_key}:{api_secret}",
			"Content-Type": "application/json"
		}
		
		# Check and sync Lead if needed
		if doc.lead:
			if not self._check_document_exists_on_external_site("Lead", doc.lead, headers, site_url):
				frappe.logger().info(f"Lead {doc.lead} not found on external site, syncing it first...")
				try:
					self._sync_lead_to_external_site(doc.lead, timeout)
				except Exception as e:
					frappe.log_error(f"Failed to sync Lead {doc.lead} before syncing SVR: {str(e)}")
					frappe.throw(_("Cannot sync Site Visit Request: Failed to sync Lead {0} first. Error: {1}").format(doc.lead, str(e)))
		
		# Prepare Site Visit Request data for sync
		sync_data = {
			"doctype": "Site Visit Request",
			"lead": doc.lead,
			"site_visit_date": self._serialize_value(doc.site_visit_date) if doc.site_visit_date else frappe.utils.today(),
			"status": "Open",  # Always start as Open on external site
			"source_document": doc.name,
			"source_doctype": "Site Visit Request",
			"notes": f"Synced from Site 1 - Original SVR: {doc.name}",
			# Mark as synced from sales
			"is_synced_from_sales": 1,
			"synced_from_site": getattr(frappe.local, "site", None) or frappe.conf.get("site_name") or "Sales Site"
		}
		
		# Add optional fields
		optional_fields = {
			"opportunity": doc.opportunity,
			"technical_questionnaire": doc.technical_questionnaire,
			"visit_type": getattr(doc, "visit_type", None),
			"priority": getattr(doc, "priority", None),
			"visit_purpose": getattr(doc, "visit_purpose", None),
			"special_requirements": getattr(doc, "special_requirements", None),
			"equipment_needed": getattr(doc, "equipment_needed", None),
			"estimated_duration": getattr(doc, "estimated_duration", None),
			"follow_up_required": getattr(doc, "follow_up_required", 0),
			"follow_up_date": self._serialize_value(getattr(doc, "follow_up_date", None)) if getattr(doc, "follow_up_date", None) else None,
			"contact_person": getattr(doc, "contact_person", None),
			"contact_number": getattr(doc, "contact_number", None),
			"email": getattr(doc, "email", None),
			"site_address": getattr(doc, "site_address", None),
			"city": getattr(doc, "city", None),
			"state": getattr(doc, "state", None),
		}
		
		# Add optional fields only if they have values
		for key, value in optional_fields.items():
			if value is not None and value != "":
				if isinstance(value, str) and len(value) > 140:
					value = value[:140]  # Truncate long strings
				sync_data[key] = value
		
		# Remove None values and empty strings
		sync_data = {k: v for k, v in sync_data.items() if v is not None and v != ""}
		
		# Serialize the entire payload
		sync_data = self._serialize_dict(sync_data)
		
		# Send to external site
		try:
			response = requests.post(
				f"{site_url}/api/resource/Site Visit Request",
				headers=headers,
				json=sync_data,
				timeout=timeout,
				verify=True,
				allow_redirects=False
			)
			
			# Log response for debugging
			frappe.logger().info(f"Site Visit Request sync response status: {response.status_code}")
			if response.status_code != 200:
				frappe.logger().error(f"Response error: {response.text[:1000]}")
		
		except requests.exceptions.RequestException as e:
			error_msg = f"Network error when syncing Site Visit Request: {str(e)}"
			frappe.log_error(f"Request exception when syncing {doc.name}: {str(e)}", "SVR Sync Network Error")
			frappe.throw(_(error_msg))
		
		if response.status_code == 200:
			result = response.json()
			external_name = result.get("data", {}).get("name")
			
			# Update local document with sync info
			doc.db_set("external_sync_status", "Synced")
			doc.db_set("external_request_name", external_name)
			doc.db_set("external_request_url", f"{site_url}/app/site-visit-request/{external_name}")
			
			return external_name
		elif response.status_code == 401:
			error_msg = "Authentication failed. Please verify API credentials."
			frappe.log_error(f"Authentication error when syncing Site Visit Request {doc.name}", "SVR Sync Auth Error")
			frappe.throw(_(error_msg))
		elif response.status_code == 417:
			# Link validation error
			try:
				error_data = response.json()
				error_detail = error_data.get("exc", "") or error_data.get("message", "")
				frappe.log_error(f"Link validation error when syncing Site Visit Request {doc.name}: {error_detail}", "SVR Sync Link Error")
				frappe.throw(_("Link validation failed. Please ensure all linked documents (Lead, Opportunity) exist on the external site."))
			except:
				frappe.throw(_("Validation error when syncing Site Visit Request: {0}").format(response.text[:200]))
		else:
			error_text = response.text[:500] if response.text else "Unknown error"
			frappe.log_error(f"Failed to sync Site Visit Request {doc.name}: Status {response.status_code} - {error_text}")
			frappe.throw(_("Failed to sync Site Visit Request: {0}").format(error_text[:200]))
	
	def _update_sync_status(self, doctype, docname, status, error_message, external_name):
		"""Update sync status on local document"""
		doc = frappe.get_doc(doctype, docname)
		doc.db_set("sync_status", status)
		
		if error_message:
			doc.db_set("sync_error_message", error_message)
		
		if external_name and hasattr(doc, "external_document_name"):
			doc.db_set("external_document_name", external_name)
	
	def _log_sync_success(self, doctype, docname, attempt):
		"""Log successful sync"""
		self.site_settings.db_set("last_sync_date", now())
		
		# Update sync statistics
		stats = self._get_sync_statistics()
		stats["successful_syncs"] = stats.get("successful_syncs", 0) + 1
		stats["last_success"] = now()
		self.site_settings.db_set("sync_statistics", json.dumps(stats))
		
		frappe.logger().info(f"Sync successful: {doctype} {docname} (attempt {attempt})")
	
	def _log_sync_error(self, doctype, docname, attempt, error_msg):
		"""Log sync error"""
		error_log = f"{now()}: {doctype} {docname} - Attempt {attempt} - {error_msg}\n"
		
		current_log = self.site_settings.sync_error_log or ""
		# Keep only last 1000 characters to prevent log from growing too large
		new_log = (error_log + current_log)[:1000]
		self.site_settings.db_set("sync_error_log", new_log)
		
		# Update sync statistics
		stats = self._get_sync_statistics()
		stats["failed_syncs"] = stats.get("failed_syncs", 0) + 1
		stats["last_error"] = now()
		self.site_settings.db_set("sync_statistics", json.dumps(stats))
		
		frappe.logger().error(f"Sync error: {doctype} {docname} - Attempt {attempt} - {error_msg}")
	
	def _get_sync_statistics(self):
		"""Get current sync statistics"""
		try:
			return json.loads(self.site_settings.sync_statistics or "{}")
		except:
			return {}
	
	def auto_sync_pending_documents(self):
		"""Auto sync pending documents if auto sync is enabled"""
		if not self.site_settings.auto_sync_enabled:
			return
		
		# Find documents with pending sync status
		pending_docs = []
		
		if self.site_settings.sync_technical_questionnaires:
			tq_docs = frappe.get_all("WWTP Technical Questionnaire",
				filters={"sync_status": "Pending", "docstatus": 1},
				fields=["name"])
			pending_docs.extend([("WWTP Technical Questionnaire", doc.name) for doc in tq_docs])
		
		if self.site_settings.sync_technical_proposals:
			tp_docs = frappe.get_all("WWTP Technical Proposal",
				filters={"workflow_status": "Approved", "docstatus": 1},
				fields=["name"])
			pending_docs.extend([("WWTP Technical Proposal", doc.name) for doc in tp_docs])
		
		if self.site_settings.sync_customer_proposals:
			cp_docs = frappe.get_all("Customer Proposal",
				filters={"workflow_status": "Approved", "docstatus": 1},
				fields=["name"])
			pending_docs.extend([("Customer Proposal", doc.name) for doc in cp_docs])
		
		# Sync pending documents
		for doctype, docname in pending_docs:
			try:
				self.sync_document(doctype, docname)
			except Exception as e:
				frappe.logger().error(f"Auto sync failed for {doctype} {docname}: {str(e)}")
				continue


def sync_document_to_external_site(doctype, docname, external_site_settings=None):
	"""Public function to sync a document to external site"""
	sync_manager = SyncManager(external_site_settings)
	return sync_manager.sync_document(doctype, docname)


def auto_sync_pending_documents():
	"""Scheduled function to auto sync pending documents"""
	# Get all enabled external site settings
	settings_list = frappe.get_all("External Site Settings", 
		filters={"enabled": 1, "auto_sync_enabled": 1})
	
	for settings in settings_list:
		try:
			sync_manager = SyncManager(settings.name)
			sync_manager.auto_sync_pending_documents()
		except Exception as e:
			frappe.logger().error(f"Auto sync failed for site {settings.name}: {str(e)}")
			continue