// Copyright (c) 2016, 	9t9it and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require('assets/erpnext/js/financial_statements.js', function () {
  frappe.query_reports['Balance Sheet Customized'] = $.extend(
    {},
    erpnext.financial_statements
  );

  frappe.query_reports['Balance Sheet Customized']['filters'] = [
    {
      fieldname: 'company',
      label: __('Company'),
      fieldtype: 'Link',
      options: 'Company',
      default: frappe.defaults.get_user_default('Company'),
      reqd: 1,
    },
    {
      fieldname: 'finance_book',
      label: __('Finance Book'),
      fieldtype: 'Link',
      options: 'Finance Book',
    },
    {
      fieldname: 'start_date',
      label: __('Start Date'),
      fieldtype: 'Date',
      default: frappe.datetime.month_start(),
      reqd: 1,
    },
    {
      fieldname: 'end_date',
      label: __('End Date'),
      fieldtype: 'Date',
      default: frappe.datetime.add_months(frappe.datetime.month_start(), 1),
      reqd: 1,
    },
    {
      fieldname: 'project',
      label: __('Project'),
      fieldtype: 'MultiSelect',
      get_data: function () {
        var projects = frappe.query_report.get_filter_value('project') || '';

        const values = projects.split(/\s*,\s*/).filter((d) => d);
        const txt = projects.match(/[^,\s*]*$/)[0] || '';
        let data = [];

        frappe.call({
          type: 'GET',
          method: 'frappe.desk.search.search_link',
          async: false,
          no_spinner: true,
          args: {
            doctype: 'Project',
            txt: txt,
            filters: {
              name: ['not in', values],
            },
          },
          callback: function (r) {
            data = r.results;
          },
        });
        return data;
      },
    },
//    {
//      fieldname: 'presentation_currency',
//      label: __('Currency'),
//      fieldtype: 'Select',
//      options: erpnext.get_presentation_currency_list(),
//    },
    {
      fieldname: 'cost_center',
      label: __('Cost Center'),
      fieldtype: 'MultiSelect',
      get_data: function () {
        var cost_centers =
          frappe.query_report.get_filter_value('cost_center') || '';

        const values = cost_centers.split(/\s*,\s*/).filter((d) => d);
        const txt = cost_centers.match(/[^,\s*]*$/)[0] || '';
        let data = [];

        frappe.call({
          type: 'GET',
          method: 'frappe.desk.search.search_link',
          async: false,
          no_spinner: true,
          args: {
            doctype: 'Cost Center',
            txt: txt,
            filters: {
              company: frappe.query_report.get_filter_value('company'),
              name: ['not in', values],
            },
          },
          callback: function (r) {
            data = r.results;
          },
        });
        return data;
      },
    },
    {
      fieldname: 'accumulated_values',
      label: __('Accumulated Values'),
      fieldtype: 'Check',
    },
    {
      fieldname: 'include_default_book_entries',
      label: __('Include Default Book Entries'),
      fieldtype: 'Check',
      default: 1,
    },
  ];
});
