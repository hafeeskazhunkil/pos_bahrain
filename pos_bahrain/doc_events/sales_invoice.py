# -*- coding: utf-8 -*-
# Copyright (c) 2018, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from erpnext.setup.utils import get_exchange_rate


def on_submit(doc, method):
    for payment in doc.payments:
        if not payment.mop_currency:
            currency = frappe.db.get_value(
                'Mode of Payment', payment.mode_of_payment, 'alt_currency'
            )
            conversion_rate = get_exchange_rate(
                currency, frappe.defaults.get_user_default('currency')
            ) if currency else 1.0
            frappe.db.set_value(
                'Sales Invoice Payment',
                payment.name,
                'mop_currency',
                currency or frappe.defaults.get_user_default('currency'),
            )
            frappe.db.set_value(
                'Sales Invoice Payment',
                payment.name,
                'mop_conversion_rate',
                conversion_rate,
            )
            frappe.db.set_value(
                'Sales Invoice Payment',
                payment.name,
                'mop_amount',
                flt(payment.base_amount) / flt(conversion_rate),
            )
