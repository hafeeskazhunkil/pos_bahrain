// Copyright (c) 2018, 	9t9it and contributors
// For license information, please see license.txt

// check backported_stock_reconciliation for duplication
frappe.ui.form.off('Stock Entry', 'scan_barcode');
frappe.ui.form.on('Stock Entry', {
  scan_barcode: function (frm) {
    let scan_barcode_field = frm.fields_dict['scan_barcode'];

    let show_description = function (idx, exist = null) {
      let message = '';
      if (exist) {
        message = __('Row #{0}: Qty increased by 1', [idx]);
      } else {
        message = __('Row #{0}: Item added', [idx]);
      }
      scan_barcode_field.set_new_description(message);
      frappe.show_alert({
        message: message,
        indicator: 'green',
      });
    };

    if (frm.doc.scan_barcode) {
      frappe
        .call({
          method:
            'erpnext.selling.page.point_of_sale.point_of_sale.search_serial_or_batch_or_barcode_number',
          args: { search_value: frm.doc.scan_barcode },
        })
        .then((r) => {
          const data = r && r.message;
          if (!data || Object.keys(data).length === 0) {
            scan_barcode_field.set_new_description(
              __('Cannot find Item with this barcode')
            );
            frappe.show_alert({
              message: 'Cannot find Item with this barcode',
              indicator: 'red',
            });
            return;
          }

          let cur_grid = frm.fields_dict.items.grid;

          let row_to_modify = null;
          const existing_item_row = frm.doc.items.find(
            (d) =>
              d.item_code === data.item_code && d.batch_no === data.batch_no
          );
          const blank_item_row = frm.doc.items.find((d) => !d.item_code);

          if (existing_item_row) {
            row_to_modify = existing_item_row;
          } else if (blank_item_row) {
            row_to_modify = blank_item_row;
          }

          if (!row_to_modify) {
            // add new row
            row_to_modify = frappe.model.add_child(
              frm.doc,
              cur_grid.doctype,
              'items'
            );
          }

          show_description(row_to_modify.idx, row_to_modify.item_code);

          frm.from_barcode = true;
          frappe.model.set_value(row_to_modify.doctype, row_to_modify.name, {
            item_code: data.item_code,
            qty: (row_to_modify.qty || 0) + 1,
          });

          ['serial_no', 'batch_no', 'barcode'].forEach((field) => {
            if (
              data[field] &&
              frappe.meta.has_field(row_to_modify.doctype, field)
            ) {
              frappe.model.set_value(
                row_to_modify.doctype,
                row_to_modify.name,
                field,
                data[field]
              );
            }
          });

          if (frm.doc.warehouse) {
            frappe.model.set_value(
              row_to_modify.doctype,
              row_to_modify.name,
              'warehouse',
              frm.doc.warehouse
            );
          }

          scan_barcode_field.set_value('');
          refresh_field('items');
        });
    }
    return false;
  },
});


frappe.ui.form.off('Stock Entry Detail', 'item_code');
frappe.ui.form.on('Stock Entry Detail', {
  item_code: pos_bahrain.scripts.extensions.stock_entry_item_code,
  s_warehouse: function (frm, cdt, cdn) {
    _set_cost_center('s_warehouse', cdt, cdn);
  },
  t_warehouse: function (frm, cdt, cdn) {
    _set_cost_center('t_warehouse', cdt, cdn);
  },
});


function _set_cost_center(fieldname, cdt, cdn) {
  const data = locals[cdt][cdn];
  _get_cost_center(data[fieldname]).then((cost_center) => {
    if (cost_center) {
      frappe.model.set_value(cdt, cdn, 'cost_center', cost_center);
    }
  });
}


async function _get_cost_center(warehouse) {
  const { message: data } = await frappe.db.get_value('Warehouse', warehouse, 'pb_cost_center');
  return data.pb_cost_center ? data.pb_cost_center : null;
}
