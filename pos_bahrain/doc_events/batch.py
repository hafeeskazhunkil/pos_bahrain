# -*- coding: utf-8 -*-
# Copyright (c) 2018, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.naming import make_autoname


def autoname(doc, method):
    """
        This override should be deprecated and removed when Batch changes in
        current develop branch, which implements the same feature, is merged
        into master.
    """
    if doc.naming_series \
            and frappe.db.get_value('Item', doc.item, 'create_new_batch'):
        doc.batch_id = make_autoname(doc.naming_series)
        doc.name = doc.batch_id
