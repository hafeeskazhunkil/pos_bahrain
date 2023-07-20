// Copyright (c) 2020, 	9t9it and contributors
// For license information, please see license.txt

frappe.ui.form.on(
  'Backported Stock Reconciliation',
  pos_bahrain.scripts.backported_stock_reconciliation
);

frappe.ui.form.on(
  'Backported Stock Reconciliation Item',
  pos_bahrain.scripts.backported_stock_reconciliation
    .backported_stock_reconciliation_item
);

const BackportedStockReconciliation = erpnext.stock.StockController.extend({
  setup: function () {
    var me = this;

    this.setup_posting_date_time_check();

    if (
      me.frm.doc.company &&
      erpnext.is_perpetual_inventory_enabled(me.frm.doc.company)
    ) {
      this.frm.add_fetch('company', 'cost_center', 'cost_center');
    }
    this.frm.fields_dict['expense_account'].get_query = function () {
      if (erpnext.is_perpetual_inventory_enabled(me.frm.doc.company)) {
        return {
          filters: {
            company: me.frm.doc.company,
            is_group: 0,
          },
        };
      }
    };
    this.frm.fields_dict['cost_center'].get_query = function () {
      if (erpnext.is_perpetual_inventory_enabled(me.frm.doc.company)) {
        return {
          filters: {
            company: me.frm.doc.company,
            is_group: 0,
          },
        };
      }
    };
    this.frm.fields_dict['warehouse'].get_query = function () {
      return {
        filters: { company: me.frm.doc.company },
      };
    };
  },

  refresh: function () {
    if (this.frm.doc.docstatus == 1) {
      this.show_stock_ledger();
      if (erpnext.is_perpetual_inventory_enabled(this.frm.doc.company)) {
        this.show_general_ledger();
      }
    }
    this.frm.fields_dict['scan_barcode'] &&
      this.frm.fields_dict['scan_barcode'].set_value('');
    this.frm.fields_dict['scan_barcode'] &&
      this.frm.fields_dict['scan_barcode'].set_new_description('');
  },

  scan_barcode: function () {
    let scan_barcode_field = this.frm.fields_dict['scan_barcode'];

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

    if (this.frm.doc.scan_barcode) {
      frappe
        .call({
          method:
            'erpnext.selling.page.point_of_sale.point_of_sale.search_serial_or_batch_or_barcode_number',
          args: { search_value: this.frm.doc.scan_barcode },
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

          let cur_grid = this.frm.fields_dict.items.grid;

          let row_to_modify = null;
          const existing_item_row = this.frm.doc.items.find(
            (d) =>
              d.item_code === data.item_code && d.batch_no === data.batch_no
          );
          const blank_item_row = this.frm.doc.items.find((d) => !d.item_code);

          if (existing_item_row) {
            row_to_modify = existing_item_row;
          } else if (blank_item_row) {
            row_to_modify = blank_item_row;
          }

          if (!row_to_modify) {
            // add new row
            row_to_modify = frappe.model.add_child(
              this.frm.doc,
              cur_grid.doctype,
              'items'
            );
          }

          show_description(row_to_modify.idx, row_to_modify.item_code);

          this.frm.from_barcode = true;
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

          if (this.frm.doc.warehouse) {
            frappe.model.set_value(
              row_to_modify.doctype,
              row_to_modify.name,
              'warehouse',
              this.frm.doc.warehouse
            );
          }

          scan_barcode_field.set_value('');
          refresh_field('items');
        });
    }
    return false;
  },

  company: function () {
    this.frm.set_query('warehouse', () => {
      return {
        filters: { company: this.frm.doc.company },
      };
    });
  },

  items_add: function (doc, cdt, cdn) {
    this.frm.from_barcode = false;
    if (!this.frm.doc.warehouse) {
      return;
    }
    frappe.model.set_value(cdt, cdn, 'warehouse', doc.warehouse);
  },
});

cur_frm.cscript = new BackportedStockReconciliation({ frm: cur_frm });
