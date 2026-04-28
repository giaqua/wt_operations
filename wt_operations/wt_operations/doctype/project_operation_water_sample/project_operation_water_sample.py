# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectOperationWaterSample(Document):
	def before_save(self):
            if self.sample_process_location:
                 self.sample_process_location_lab = self.sample_process_location or ""
      
	# pass



