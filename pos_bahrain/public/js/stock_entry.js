// Copyright (c) 2018, 	9t9it and contributors
// For license information, please see license.txt

select_batch_and_serial_no = erpnext.stock.select_batch_and_serial_no;

erpnext.stock.select_batch_and_serial_no = (frm, item) => {
  if (item && item.has_batch_no && frm.doc.purpose === 'Material Receipt') {
    frappe.require(
      'assets/erpnext/js/utils/serial_no_batch_selector.js',
      function() {
        const SerialNoBatchSelector = erpnext.SerialNoBatchSelector.extend({
          get_batch_fields: function() {
            const fields = this._super();
            if (fields) {
              const batches = fields.find(
                ({ fieldname }) => fieldname === 'batches'
              );
              if (batches) {
                const batch_no = batches.fields.find(
                  ({ fieldname }) => fieldname === 'batch_no'
                );
                if (batch_no) {
                  batch_no.get_query = () => ({
                    filters: { item: this.item_code },
                  });
                }
              }
            }
            return fields;
          },
        });
        new SerialNoBatchSelector({
          frm: frm,
          item: item,
          warehouse_details: {
            type: 'Target Warehouse',
            name: cstr(item.t_warehouse) || '',
          },
        });
      }
    );
  } else {
    select_batch_and_serial_no(frm, item);
  }
};
