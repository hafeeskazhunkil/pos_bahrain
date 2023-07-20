function _apply_pb_discount_percentage(doctype) {
  frappe.ui.form.on(doctype, {
    pb_discount_percentage: function (frm) {
      frm.doc.items.forEach(({ doctype, name }) => {
        frappe.model.set_value(
          doctype,
          name,
          'discount_percentage',
          frm.doc.pb_discount_percentage
        );
      });
    },
  });
}

function _apply_pb_discount_percentage_on_item_code(doctype) {
  frappe.ui.form.on(doctype, {
    item_code: function (frm, cdt, cdn) {
      setTimeout(function () {
        frappe.model.set_value(
          cdt,
          cdn,
          'discount_percentage',
          frm.doc.pb_discount_percentage
        );
      }, 300);
    },
  });
}

['Quotation', 'Sales Order', 'Sales Invoice'].forEach((doctype) =>
  _apply_pb_discount_percentage(doctype)
);
[
  'Quotation Item',
  'Sales Order Item',
  'Sales Invoice Item',
].forEach((doctype) => _apply_pb_discount_percentage_on_item_code(doctype));
