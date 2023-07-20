export default function () {
  return {
    refresh: function (frm) {
      frm.disable_save();
      frm.page.show_menu();
      frm.page.set_primary_action('Send Email', async function () {
        frm.call({ method: 'send_emails', doc: frm.doc });
      });
      frm.page.set_secondary_action('Clear', function () {
        clear(frm);
      });
    },
    batch: function (frm) {
      const { batch } = frm.doc;
      if (batch) {
        frm.call({ method: 'fetch_invoices', doc: frm.doc });
      } else {
        clear(frm);
      }
    },
  };
}

function clear(frm) {
  frm.set_value({
    batch: null,
    no_of_invoices: 0,
    no_of_customers: 0,
    total_qty_sold: 0,
  });
  frm.clear_table('invoices');
  frm.refresh_field('invoices');
}
