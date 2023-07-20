erpnext.TransactionController = erpnext.TransactionController.extend({
  set_query_for_batch: function (doc, cdt, cdn) {
    var me = this;
    var item = frappe.get_doc(cdt, cdn);

    if (!item.item_code) {
      frappe.throw(__('Please enter Item Code to get batch no'));
    } else if (doc.doctype == 'Purchase Receipt') {
      return {
        filters: { item: item.item_code },
      };
    } else if (doc.doctype == 'Purchase Invoice') {
      let filters = { item_code: item.item_code };

      filters['posting_date'] =
        me.frm.doc.posting_date || frappe.datetime.nowdate();

      if (item.warehouse) filters['warehouse'] = item.warehouse;

      return {
        query: 'pos_bahrain.api.batch.get_batch_no',
        filters: filters,
      };
    } else {
      let filters = { item_code: item.item_code };

      if (doc.doctype !== 'Purchase Invoice') {
        filters['posting_date'] =
          me.frm.doc.posting_date || frappe.datetime.nowdate();
      }

      if (doc.is_return) {
        filters['is_return'] = 1;
      }

      if (item.warehouse) filters['warehouse'] = item.warehouse;

      return {
        query: 'erpnext.controllers.queries.get_batch_no',
        filters: filters,
      };
    }
  },
});
