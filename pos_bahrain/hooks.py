# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "pos_bahrain"
app_title = "Pos Bahrain"
app_publisher = "	9t9it"
app_description = "Pos Customization"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hafeesk@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/css/pos_css.css"
# app_include_js = "/assets/pos_bahrain/js/pos_bahrain.js"
app_include_css = "/assets/css/jmi.min.css"
app_include_js = [
	'/assets/js/jmi.min.js',
	'/assets/pos_bahrain/js/batch_quick_entry.js',
]

# include js, css files in header of web template
# web_include_css = "/assets/pos_bahrain/css/pos_bahrain.css"
# web_include_js = "/assets/pos_bahrain/js/pos_bahrain.js"

# include js in page
page_js = {
	"pos" : "public/js/pos_page_js.js",
	"point-of-sale" : "public/js/pos_page_js.js"
}

# include js in doctype views
doctype_js = {
	'Mode of Payment': 'public/js/mode_of_payment.js',
	'Stock Entry': 'public/js/stock_entry.js',
	'Company': 'public/js/company.js',
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

fixtures = [
	{
		'doctype': 'Custom Field',
		'filters': [['name', 'in', [
			'Sales Invoice-pos_total_qty',
			'POS Closing Voucher Details-opening_amount',
			'POS Closing Voucher Details-expected_amount_with_opening',
			'Mode of Payment-currency_section',
			'Mode of Payment-in_alt_currency',
			'Mode of Payment-alt_currency',
			'Sales Invoice Payment-pos_section',
			'Sales Invoice Payment-mop_currency',
			'Sales Invoice Payment-cb11',
			'Sales Invoice Payment-mop_conversion_rate',
			'Sales Invoice Payment-mop_amount',
			'Batch-naming_series',
			'Company-default_warehouse',
		]]]
	},
	{
		'doctype': 'Property Setter',
		'filters': [['name', 'in', [
			'Batch-search_fields',
			'Batch-batch_id-reqd',
			'Batch-batch_id-bold',
			'Batch-expiry_date-in_list_view',
			'Batch-expiry_date-bold',
		]]]
	},
]

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "pos_bahrain.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "pos_bahrain.install.before_install"
# after_install = "pos_bahrain.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pos_bahrain.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	'Batch': {
		'autoname': 'pos_bahrain.doc_events.batch.autoname',
	},
	'Sales Invoice': {
		'on_submit': 'pos_bahrain.doc_events.sales_invoice.on_submit',
	},
}

on_session_creation = 'pos_bahrain.doc_events.set_user_defaults'

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pos_bahrain.tasks.all"
# 	],
# 	"daily": [
# 		"pos_bahrain.tasks.daily"
# 	],
# 	"hourly": [
# 		"pos_bahrain.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pos_bahrain.tasks.weekly"
# 	]
# 	"monthly": [
# 		"pos_bahrain.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "pos_bahrain.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
	'erpnext.stock.get_item_details.get_item_details':
		'pos_bahrain.api.get_item_details.get_item_details',
}
