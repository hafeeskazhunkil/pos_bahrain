// Copyright (c) 2020, 	9t9it and contributors
// For license information, please see license.txt

const script = pos_bahrain.scripts.gl_payment();

frappe.ui.form.on('GL Payment', script);
frappe.ui.form.on('GL Payment Item', script.gl_payment_item);
