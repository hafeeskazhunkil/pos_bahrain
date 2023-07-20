// Copyright (c) 2016, 	9t9it and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Sales and Purchase History'] = {
  filters: [
    {
      fieldname: 'item_code',
      label: __('Item Code'),
      fieldtype: 'Link',
      options: 'Item',
      reqd: 1,
    },
    {
      label: __('Date'),
      fieldtype: 'DateRange',
      fieldname: 'date_range',
      reqd: 1,
      default: [frappe.datetime.month_start(), frappe.datetime.month_end()],
    },
    {
      fieldname: 'warehouse',
      label: __('Warehouse'),
      fieldtype: 'Link',
      options: 'Warehouse',
    },
  ],
};
