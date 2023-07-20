# -*- coding: utf-8 -*-
# Copyright (c) 2019, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.utils import cint
from frappe.model.document import Document
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


class POSBahrainSettings(Document):
    def on_update(self):
        hide_batch_price = not cint(self.use_batch_price)
        make_property_setter(
            "Batch", "pb_price_sec", "hidden", hide_batch_price, "Check"
        )
        make_property_setter(
            "Batch", "pb_price_sec", "print_hide", hide_batch_price, "Check"
        )

        hide_barcode_uom = not cint(self.use_barcode_uom)
        make_property_setter(
            "Item Barcode", "pb_uom", "hidden", hide_barcode_uom, "Check"
        )

        hide_sales_employee = not cint(self.show_sales_employee)
        make_property_setter(
            "Sales Invoice",
            "pb_sales_employee",
            "reqd" if hide_sales_employee else "hidden",
            False,
            "Check",
        )
        make_property_setter(
            "Sales Invoice",
            "pb_sales_employee",
            "hidden" if hide_sales_employee else "reqd",
            True,
            "Check",
        )
