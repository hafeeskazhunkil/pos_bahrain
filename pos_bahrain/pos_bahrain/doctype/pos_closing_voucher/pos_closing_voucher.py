# -*- coding: utf-8 -*-
# Copyright (c) 2018, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import now
from frappe.model.document import Document

class POSClosingVoucher(Document):
	def validate(self):
		existing = frappe.db.sql(
			"""
				SELECT 1 FROM `tabPOS Closing Voucher`
				WHERE
					name != %(name)s AND
					company = %(company)s AND
					pos_profile = %(pos_profile)s AND
					user = %(user)s AND
					period_from <= %(period_to)s AND
					period_to >= %(period_from)s
			""",
			values={
				'name': self.name,
				'company': self.company,
				'pos_profile': self.pos_profile,
				'user': self.user,
				'period_from': self.period_from or now(),
				'period_to': self.period_to or now(),
			},
		)
		if existing:
			frappe.throw(
				'Another POS Closing Voucher already exists during this time '
				'frame.'
			)
