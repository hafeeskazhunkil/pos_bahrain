# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from six import string_types
from toolz import merge, concat


@frappe.whitelist()
def make_invoice(doc_list={}, email_queue_list={}, customers_list={}):
    from erpnext.accounts.doctype.sales_invoice.pos import make_invoice

    result = make_invoice(
        doc_list=[], email_queue_list=email_queue_list, customers_list=customers_list,
    )

    docs = json.loads(doc_list) if isinstance(doc_list, string_types) else doc_list

    prev_synced_invoices = [
        x[0]
        for x in frappe.get_all(
            "Sales Invoice",
            fields="offline_pos_name",
            filters={
                "offline_pos_name": ("in", list(concat([x.keys() for x in docs])))
            },
            as_list=1,
        )
    ]

    for doc_list_item in docs:
        for name, doc in doc_list_item.items():
            frappe.utils.background_jobs.enqueue(
                make_invoice, job_name=name, doc_list=[{name: doc}]
            )

    return merge(result, {"invoice": prev_synced_invoices})
