# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.model.document import Document
from frappe.utils import now
from frappe.utils.password import get_decrypted_password
from frappe import _


class ExternalSiteSettings(Document):
	def validate(self):
		"""Validate external site settings"""
		if self.sync_retry_attempts and self.sync_retry_attempts < 1:
			frappe.throw(_("Sync retry attempts must be at least 1"))
		
		if self.sync_timeout_seconds and self.sync_timeout_seconds < 5:
			frappe.throw(_("Sync timeout must be at least 5 seconds"))
	
	@frappe.whitelist()
	def test_connection(self):
		"""Test the connection to the external ERPNext site"""
		try:
			# Get fresh document data to ensure we have the latest values
			# When called via AJAX, self might not have all fields populated
			if hasattr(self, 'name') and self.name:
				doc = frappe.get_doc("External Site Settings", self.name)
			else:
				doc = self
			
			# Validate required fields
			site_url = (doc.site_url or "").strip()
			
			# Password fields are encrypted, need to decrypt them
			# Only decrypt if document is saved (has a name)
			if hasattr(doc, 'name') and doc.name:
				try:
					api_key = get_decrypted_password("External Site Settings", doc.name, "api_key")
				except:
					# If decryption fails, try using the value directly (might be unencrypted)
					api_key = (doc.api_key or "").strip()
				
				try:
					api_secret = get_decrypted_password("External Site Settings", doc.name, "api_secret")
				except:
					# If decryption fails, try using the value directly (might be unencrypted)
					api_secret = (doc.api_secret or "").strip()
			else:
				# Document not saved yet, use values directly (they should be plain text in memory)
				api_key = (doc.api_key or "").strip()
				api_secret = (doc.api_secret or "").strip()
			
			if not site_url:
				frappe.throw(_("Site URL is required"))
			if not api_key:
				frappe.throw(_("API Key is required"))
			if not api_secret:
				frappe.throw(_("API Secret is required"))
			
			# Normalize site URL (remove trailing slash)
			site_url = site_url.rstrip('/')
			
			# Debug logging (remove in production if needed)
			frappe.logger().debug(f"Testing connection to {site_url} with API Key: {api_key[:10]}...")
			
			# Test API connection
			headers = {
				"Authorization": f"token {api_key}:{api_secret}",
				"Content-Type": "application/json"
			}
			
			# Test with a simple API call - try multiple endpoints
			test_endpoints = [
				"/api/method/frappe.auth.get_logged_user",
				"/api/method/ping",
				"/api/resource/User/Administrator"
			]
			
			last_error = None
			last_status = None
			
			for endpoint in test_endpoints:
				try:
					response = requests.get(
						f"{site_url}{endpoint}",
						headers=headers,
						timeout=10,
						verify=True  # Verify SSL certificates
					)
					
					last_status = response.status_code
					
					if response.status_code == 200:
						connection_status = "Connected"
						user_info = "User"
						try:
							if endpoint == "/api/method/frappe.auth.get_logged_user":
								user_info = response.json().get("message", "User")
						except:
							pass
						message = _("Connection successful! Authenticated as: {0}").format(user_info)
						if hasattr(self, 'name') and self.name:
							self.db_set("connection_status", connection_status)
						return {
							"status": "success",
							"message": message,
							"connection_status": connection_status,
							"status_code": response.status_code
						}
					elif response.status_code == 401:
						# 401 means authentication failed
						error_detail = "Authentication failed"
						try:
							error_data = response.json()
							if "message" in error_data:
								error_detail = error_data["message"]
						except:
							error_detail = response.text[:200] if response.text else "Invalid credentials"
						
						connection_status = f"Authentication Failed (401)"
						message = _("Authentication failed. Please verify:\n1. API Key is correct\n2. API Secret is correct\n3. API Key/Secret pair is valid on the external site")
						
						if hasattr(self, 'name') and self.name:
							self.db_set("connection_status", connection_status)
						return {
							"status": "failed",
							"message": message,
							"connection_status": connection_status,
							"status_code": 401,
							"error_detail": error_detail,
							"debug_info": {
								"site_url": site_url,
								"api_key_length": len(api_key),
								"api_secret_length": len(api_secret)
							}
						}
					else:
						last_error = f"Status {response.status_code}"
						continue
						
				except requests.exceptions.SSLError as e:
					last_error = f"SSL Error: {str(e)}"
					continue
				except requests.exceptions.ConnectionError as e:
					last_error = f"Connection Error: {str(e)}"
					break  # No point trying other endpoints if we can't connect
				except requests.exceptions.Timeout:
					last_error = "Connection timeout"
					break
				except Exception as e:
					last_error = str(e)
					continue
			
			# If we get here, all endpoints failed
			connection_status = f"Failed - Status: {last_status or 'Unknown'}"
			message = _("Connection failed. {0}").format(last_error or "Please check your site URL and credentials.")
			
			if hasattr(self, 'name') and self.name:
				self.db_set("connection_status", connection_status)
			return {
				"status": "failed",
				"message": message,
				"connection_status": connection_status,
				"status_code": last_status,
				"error_detail": last_error
			}
				
		except Exception as e:
			connection_status = f"Error: {str(e)}"
			# Update connection status using db_set for AJAX calls
			if hasattr(self, 'name') and self.name:
				self.db_set("connection_status", connection_status)
			
			return {
				"status": "error",
				"message": _("Connection error: {0}").format(str(e)),
				"connection_status": connection_status,
				"exception_type": type(e).__name__
			}
	
	def get_api_headers(self):
		"""Get API headers for external site requests"""
		# Password fields are encrypted, need to decrypt them
		# Always get fresh values from database to ensure decryption works
		api_key = None
		api_secret = None
		
		try:
			api_key = get_decrypted_password("External Site Settings", self.name, "api_key")
		except Exception as e:
			frappe.log_error(f"Failed to decrypt API key for {self.name}: {str(e)}")
			frappe.throw(_("Failed to decrypt API Key. Please re-enter the API Key in External Site Settings."))
		
		try:
			api_secret = get_decrypted_password("External Site Settings", self.name, "api_secret")
		except Exception as e:
			frappe.log_error(f"Failed to decrypt API secret for {self.name}: {str(e)}")
			frappe.throw(_("Failed to decrypt API Secret. Please re-enter the API Secret in External Site Settings."))
		
		# Validate credentials
		if not api_key or not api_secret:
			frappe.throw(_("API Key or API Secret is missing. Please check External Site Settings."))
		
		# Strip any whitespace
		api_key = str(api_key).strip()
		api_secret = str(api_secret).strip()
		
		# Validate they're not empty after stripping
		if not api_key or not api_secret:
			frappe.throw(_("API Key or API Secret is empty. Please check External Site Settings."))
		
		# Construct authorization header
		auth_header = f"token {api_key}:{api_secret}"
		
		return {
			"Authorization": auth_header,
			"Content-Type": "application/json"
		}
	
	def create_site_visit_request(self, stp_doc):
		"""Create a site visit request on the external ERPNext site"""
		if not self.enabled:
			frappe.throw(_("External site integration is disabled"))
		
		try:
			headers = self.get_api_headers()
			
			# Prepare site visit request data with comprehensive field mapping
			site_visit_data = {
				"doctype": "Site Visit Request",
				"lead": stp_doc.lead,
				"opportunity": stp_doc.opportunity,
				"site_visit_date": frappe.utils.today(),
				"status": "Open",
				"source_document": stp_doc.name,
				"source_doctype": "WWTP Technical Questionnaire",
				"notes": f"Auto-generated from WWTP Technical Questionnaire: {stp_doc.name}"
			}
			
			# Add optional fields if they exist in the external doctype
			optional_fields = {
				"visit_purpose": f"STP Technical Assessment - {stp_doc.wastewater_generator_type or 'Wastewater Treatment'}",
				"priority": "High" if stp_doc.sample_collection_required else "Medium",
				"visit_type": "Technical Survey",
				"estimated_duration": "2-4 hours",
				"special_requirements": f"STP Capacity: {stp_doc.capacity or 'TBD'}, Footprint: {stp_doc.the_available_footprint_dedicated_for_stp_in_sm or 'TBD'} sqm",
				"equipment_needed": "Water quality testing equipment, measuring tools, camera" if stp_doc.sample_collection_required else "Measuring tools, camera",
				"follow_up_required": 1 if stp_doc.sample_collection_required else 0
			}
			
			# Add optional fields to the data
			site_visit_data.update(optional_fields)
			
			# Create the site visit request
			response = requests.post(
				f"{self.site_url}/api/resource/Site Visit Request",
				headers=headers,
				json=site_visit_data,
				timeout=30
			)
			
			if response.status_code == 200:
				result = response.json()
				site_visit_name = result.get("data", {}).get("name", "Unknown")
				frappe.msgprint(
					_("Site visit request created successfully on external site: {0}").format(site_visit_name),
					alert=True
				)
				return site_visit_name
			elif response.status_code == 400:
				# Handle field validation errors
				error_data = response.json()
				error_message = error_data.get("message", "Validation error")
				frappe.msgprint(
					_("Field validation error on external site: {0}").format(error_message),
					alert=True
				)
				# Try with minimal required fields only
				return self.create_minimal_site_visit_request(stp_doc, headers)
			else:
				frappe.throw(_("Failed to create site visit request: {0}").format(response.text))
				
		except Exception as e:
			frappe.throw(_("Error creating site visit request: {0}").format(str(e)))
	
	def post_resource(self, resource, payload):
		"""Generic method to POST JSON to external site"""
		if not self.enabled:
			frappe.throw(_("External site integration is disabled"))
		
		try:
			headers = self.get_api_headers()
			response = requests.post(
				f"{self.site_url}/api/resource/{resource}",
				headers=headers,
				json=payload,
				timeout=30
			)
			return response.status_code, response.json() if response.content else {}
		except Exception as e:
			frappe.throw(_("Error posting to external site: {0}").format(str(e)))
	
	def create_site_visit_request_from_svr(self, svr_doc):
		"""Create a site visit request on external site from local SVR doc"""
		if not self.enabled:
			frappe.throw(_("External site integration is disabled"))
		
		try:
			# Build payload with minimal required fields
			site_visit_data = {
				"doctype": "Site Visit Request",
				"site_visit_date": svr_doc.site_visit_date or frappe.utils.today(),
				"status": "Open",
				"source_document": svr_doc.name,
				"source_doctype": "Site Visit Request",
				"notes": f"Synced from Site 1 - Original SVR: {svr_doc.name}"
			}
			
			# Add optional fields if they exist
			if svr_doc.lead:
				site_visit_data["lead"] = svr_doc.lead
			if svr_doc.priority:
				site_visit_data["priority"] = svr_doc.priority
			if svr_doc.visit_type:
				site_visit_data["visit_type"] = svr_doc.visit_type
			if svr_doc.visit_purpose:
				site_visit_data["visit_purpose"] = svr_doc.visit_purpose
			if svr_doc.special_requirements:
				site_visit_data["special_requirements"] = svr_doc.special_requirements
			if svr_doc.equipment_needed:
				site_visit_data["equipment_needed"] = svr_doc.equipment_needed
			if svr_doc.estimated_duration:
				site_visit_data["estimated_duration"] = svr_doc.estimated_duration
			
			# Create the site visit request
			status_code, result = self.post_resource("Site Visit Request", site_visit_data)
			
			if status_code == 200:
				external_name = result.get("data", {}).get("name", "Unknown")
				
				# Generate and attach TQ PDF if technical_questionnaire exists
				if svr_doc.technical_questionnaire:
					self.attach_tq_pdf_to_external_svr(svr_doc.technical_questionnaire, external_name)
				
				return external_name
			else:
				error_message = result.get("message", "Unknown error")
				frappe.throw(_("Failed to create site visit request on external site: {0}").format(error_message))
				
		except Exception as e:
			frappe.throw(_("Error creating site visit request on external site: {0}").format(str(e)))
	
	def attach_tq_pdf_to_external_svr(self, tq_name, external_svr_name):
		"""Generate TQ PDF and attach it to external SVR"""
		try:
			# Generate PDF from TQ
			html = frappe.get_print("WWTP Technical Questionnaire", tq_name)
			pdf_content = frappe.utils.pdf.get_pdf(html)
			
			# Convert to base64
			import base64
			pdf_base64 = base64.b64encode(pdf_content).decode()
			
			# Upload file to external site
			file_data = {
				"doctype": "File",
				"attached_to_doctype": "Site Visit Request",
				"attached_to_name": external_svr_name,
				"file_name": f"WWTP_TQ_{tq_name}.pdf",
				"is_private": 1,
				"content": pdf_base64
			}
			
			status_code, result = self.post_resource("File", file_data)
			
			if status_code == 200:
				frappe.msgprint(_("TQ PDF attached to external SVR successfully"), alert=True)
			else:
				frappe.msgprint(_("Failed to attach TQ PDF to external SVR"), alert=True)
				
		except Exception as e:
			frappe.msgprint(_("Error attaching TQ PDF: {0}").format(str(e)), alert=True)
	
	def create_technical_proposal_from_local(self, proposal_doc):
		"""Create a technical proposal on external site from local proposal doc"""
		if not self.enabled:
			frappe.throw(_("External site integration is disabled"))
		
		try:
			# Build payload with proposal data
			proposal_data = {
				"doctype": "WWTP Technical Proposal",
				"lead": proposal_doc.lead,
				"opportunity": proposal_doc.opportunity,
				"wwtp_technical_questionnaire": proposal_doc.wwtp_technical_questionnaire,
				"site_visit": proposal_doc.site_visit,
				"water_sample": proposal_doc.water_sample,
				"proposal_date": proposal_doc.proposal_date,
				"valid_until": proposal_doc.valid_until,
				"prepared_by": proposal_doc.prepared_by,
				"technical_manager": proposal_doc.technical_manager,
				"project_title": proposal_doc.project_title,
				"project_description": proposal_doc.project_description,
				"wastewater_generator_type": proposal_doc.wastewater_generator_type,
				"design_capacity": proposal_doc.design_capacity,
				"current_capacity": proposal_doc.current_capacity,
				"site_conditions_summary": proposal_doc.site_conditions_summary,
				"existing_facility_assessment": proposal_doc.existing_facility_assessment,
				"site_accessibility_rating": proposal_doc.site_accessibility_rating,
				"power_availability_rating": proposal_doc.power_availability_rating,
				"ground_conditions_rating": proposal_doc.ground_conditions_rating,
				"environmental_impact_assessment": proposal_doc.environmental_impact_assessment,
				"influent_characteristics": proposal_doc.influent_characteristics,
				"effluent_requirements": proposal_doc.effluent_requirements,
				"treatment_challenges": proposal_doc.treatment_challenges,
				"compliance_status": proposal_doc.compliance_status,
				"treatment_technology": proposal_doc.treatment_technology,
				"process_description": proposal_doc.process_description,
				"treatment_stages": proposal_doc.treatment_stages,
				"civil_requirements": proposal_doc.civil_requirements,
				"site_preparation_needs": proposal_doc.site_preparation_needs,
				"utility_connections": proposal_doc.utility_connections,
				"operation_hours": proposal_doc.operation_hours,
				"maintenance_requirements": proposal_doc.maintenance_requirements,
				"chemical_consumption": proposal_doc.chemical_consumption,
				"energy_consumption": proposal_doc.energy_consumption,
				"environmental_permits_required": proposal_doc.environmental_permits_required,
				"discharge_permit_status": proposal_doc.discharge_permit_status,
				"environmental_monitoring": proposal_doc.environmental_monitoring,
				"equipment_cost": proposal_doc.equipment_cost,
				"civil_works_cost": proposal_doc.civil_works_cost,
				"electrical_cost": proposal_doc.electrical_cost,
				"total_project_cost": proposal_doc.total_project_cost,
				"design_period": proposal_doc.design_period,
				"procurement_period": proposal_doc.procurement_period,
				"construction_period": proposal_doc.construction_period,
				"commissioning_period": proposal_doc.commissioning_period,
				"total_implementation_time": proposal_doc.total_implementation_time,
				"technical_risks": proposal_doc.technical_risks,
				"environmental_risks": proposal_doc.environmental_risks,
				"mitigation_strategies": proposal_doc.mitigation_strategies,
				"technical_recommendations": proposal_doc.technical_recommendations,
				"next_steps": proposal_doc.next_steps,
				"follow_up_required": proposal_doc.follow_up_required
			}
			
			# Create the technical proposal
			status_code, result = self.post_resource("WWTP Technical Proposal", proposal_data)
			
			if status_code == 200:
				external_name = result.get("data", {}).get("name", "Unknown")
				
				# Generate and attach proposal PDF if needed
				self.attach_proposal_pdf_to_external(proposal_doc.name, external_name)
				
				return external_name
			else:
				error_message = result.get("message", "Unknown error")
				frappe.throw(_("Failed to create technical proposal on external site: {0}").format(error_message))
				
		except Exception as e:
			frappe.throw(_("Error creating technical proposal on external site: {0}").format(str(e)))
	
	def attach_proposal_pdf_to_external(self, local_proposal_name, external_proposal_name):
		"""Generate proposal PDF and attach it to external proposal"""
		try:
			# Generate PDF from proposal
			html = frappe.get_print("WWTP Technical Proposal", local_proposal_name)
			pdf_content = frappe.utils.pdf.get_pdf(html)
			
			# Convert to base64
			import base64
			pdf_base64 = base64.b64encode(pdf_content).decode()
			
			# Upload file to external site
			file_data = {
				"doctype": "File",
				"attached_to_doctype": "WWTP Technical Proposal",
				"attached_to_name": external_proposal_name,
				"file_name": f"WWTP_Technical_Proposal_{local_proposal_name}.pdf",
				"is_private": 1,
				"content": pdf_base64
			}
			
			status_code, result = self.post_resource("File", file_data)
			
			if status_code == 200:
				frappe.msgprint(_("Technical Proposal PDF attached to external proposal successfully"), alert=True)
			else:
				frappe.msgprint(_("Failed to attach Technical Proposal PDF to external proposal"), alert=True)
				
		except Exception as e:
			frappe.msgprint(_("Error attaching Technical Proposal PDF: {0}").format(str(e)), alert=True)
	
	def sync_document_with_retry(self, doctype, docname, sync_type="create"):
		"""Sync document with retry logic and error handling"""
		from wt_operations.wt_operations.sync_manager import SyncManager
		
		try:
			sync_manager = SyncManager(self.name)
			return sync_manager.sync_document(doctype, docname, sync_type)
		except Exception as e:
			self.log_sync_error(doctype, docname, str(e))
			raise
	
	def log_sync_error(self, doctype, docname, error_message):
		"""Log sync error to the error log"""
		error_entry = f"{now()}: {doctype} {docname} - {error_message}\n"
		current_log = self.sync_error_log or ""
		# Keep only last 1000 characters
		new_log = (error_entry + current_log)[:1000]
		self.db_set("sync_error_log", new_log)
		
		# Update statistics
		self.update_sync_statistics("error")
	
	def log_sync_success(self, doctype, docname):
		"""Log successful sync"""
		self.db_set("last_sync_date", now())
		self.update_sync_statistics("success")
		frappe.logger().info(f"Sync successful: {doctype} {docname}")
	
	def update_sync_statistics(self, result_type):
		"""Update sync statistics"""
		try:
			stats = json.loads(self.sync_statistics or "{}")
		except:
			stats = {}
		
		if result_type == "success":
			stats["successful_syncs"] = stats.get("successful_syncs", 0) + 1
			stats["last_success"] = now()
		elif result_type == "error":
			stats["failed_syncs"] = stats.get("failed_syncs", 0) + 1
			stats["last_error"] = now()
		
		self.db_set("sync_statistics", json.dumps(stats))
	
	def get_sync_status_summary(self):
		"""Get a summary of sync status"""
		try:
			stats = json.loads(self.sync_statistics or "{}")
			return {
				"successful_syncs": stats.get("successful_syncs", 0),
				"failed_syncs": stats.get("failed_syncs", 0),
				"last_success": stats.get("last_success"),
				"last_error": stats.get("last_error"),
				"last_sync_date": self.last_sync_date
			}
		except:
			return {
				"successful_syncs": 0,
				"failed_syncs": 0,
				"last_success": None,
				"last_error": None,
				"last_sync_date": self.last_sync_date
			}
