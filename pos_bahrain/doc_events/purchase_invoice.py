# -*- coding: utf-8 -*-
# Copyright (c) 2019, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from pos_bahrain.doc_events.purchase_receipt import set_or_create_batch
from pos_bahrain.doc_events.sales_invoice import set_cost_center


def before_validate(doc, method):
    set_or_create_batch(doc, method)


def before_save(doc, method):
    set_cost_center(doc)


def on_submit(doc, method):
    if doc.bill_no and frappe.db.exists('Sales Invoice', doc.bill_no):
        frappe.db.set_value("Sales Invoice", doc.bill_no, "pb_related_pi", doc.name)
