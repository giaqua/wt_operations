# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
# import frappe.utils
from frappe.utils import flt


class OffSpecCODInvoiceCalculator(Document):
	def before_save(self):
		if self.base_reception_tariff > 0 and len(self.tier_tariff_structure) > 0:
			for tier in self.tier_tariff_structure:
				if tier.premium > 0:
					tier.tier_tariff = self.base_reception_tariff * tier.premium

		self.calculate_daily_off_spec()

	def calculate_daily_off_spec(self):
		doc = self
		cod = flt(doc.cod)
		inlet_vol = flt(doc.inlet_treated_vol)
		baseline = flt(doc.contractual_cod_baseline_m1ppm)

		matched_tier = None

		for row in doc.tier_tariff_structure:
			if row.cod_range_start <= cod <= row.cod_range_end:
				matched_tier = row
				break

		if not matched_tier:
			frappe.throw(
				_("No matching tier found in Tier Tariff Structure for COD value {0}").format(cod)
			)
		elif not inlet_vol or not baseline:
			doc.daily_off_spec = 0
		else:
			tier_tariff = flt(matched_tier.tier_tariff) * flt(matched_tier.premium)
			doc.daily_off_spec = inlet_vol * (cod / baseline) * tier_tariff
					
