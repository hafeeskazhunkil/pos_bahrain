export default function () {
  return {
    filters: [
      {
        fieldname: 'from_date',
        label: __('From Date'),
        fieldtype: 'Date',
        width: '80',
        reqd: 1,
        default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
      },
      {
        fieldname: 'to_date',
        label: __('To Date'),
        fieldtype: 'Date',
        width: '80',
        reqd: 1,
        default: frappe.datetime.get_today(),
      },
      {
        fieldtype: 'Link',
        fieldname: 'warehouse',
        label: 'Warehouse',
        options: 'Warehouse'
      },
      {
        fieldtype: 'Link',
        fieldname: 'company',
        label: 'Company',
        options: 'Company'
      },
      {
        fieldtype: 'Link',
        fieldname: 'cost_center',
        label: 'Cost Center',
        options: 'Cost Center'
      },
    ],
    formatter: function (value, row, column, data, default_formatter) {
      const formatted = default_formatter(value, row, column, data);
      if (data.bold) {
        return $(`<span>${formatted}</span>`)
          .css('font-weight', 'bold')
          .wrap('<p />')
          .parent()
          .html();
      }
      return formatted;
    },
  };
}
