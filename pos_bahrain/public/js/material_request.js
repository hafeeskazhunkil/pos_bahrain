frappe.ui.form.on('Material Request', {
  refresh: function (frm) {
    if (frm.doc.material_request_type === "Material Transfer") {
        frm.add_custom_button(__("Stock Transfer"), () => _make_stock_transfer(frm));
    }
  },
});


function _make_stock_transfer(frm) {
  frappe.model.open_mapped_doc({
      method: "pos_bahrain.api.material_request.make_stock_entry",
      frm: frm
  });
}
