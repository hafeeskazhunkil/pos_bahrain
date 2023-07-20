# -*- coding: utf-8 -*-
# Copyright (c) 2019, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def update_customer_phone(doc,method):
	for row in doc.links:
		if(row.link_doctype == "Customer"):
			frappe.db.sql("""UPDATE
				`tabCustomer`
			SET
				pb_phone = '%(phone)s'
			WHERE name='%(customer)s'    
			"""%{"phone":doc.phone, "customer":row.link_name})
