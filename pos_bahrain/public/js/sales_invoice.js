frappe.ui.form.on('Sales Invoice', {
  refresh: function (frm) {
    _create_custom_buttons(frm);
    pos_bahrain.scripts.extensions.hide_sales_return('Return / Credit Note', 'Make');
  },
});


function _create_custom_buttons(frm) {
  if (frm.doc.docstatus !== 1) {
    return;
  }
  if (!frm.doc.pb_related_pi) {
    frm.add_custom_button(__("Purchase Invoice"), function () {
      _make_purchase_invoice(frm);
    }, __("Make"));
  }
}


function _make_purchase_invoice(frm) {
  frappe.model.open_mapped_doc({
    method: "pos_bahrain.api.sales_invoice.make_purchase_invoice",
    frm,
  });
}
