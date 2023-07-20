// Copyright (c) 2016, 	9t9it and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Cheque Summary'] = {
  filters: [
    {
      fieldname: 'date_range',
      label: __('Date Range'),
      fieldtype: 'DateRange',
      reqd: 1,
      default: [frappe.datetime.month_start(), frappe.datetime.month_end()],
    },
  ],
};
