async function show_prices(frm) {
  if (frm.doc.__islocal || !frappe.user_roles.includes('Accounts Manager')) {
    return;
  }
  const { item_code } = frm.doc;
  const { message: { selling_price, buying_price } = {} } = await frappe.call({
    method: 'pos_bahrain.api.item.get_standard_prices',
    args: { item_code },
  });

  const section = frm.dashboard.add_section(
    `<h5 style="margin-top: 0px;">${__('Standard Prices')}</h5>`
  ).append(`
    <div class="row">
      <div class="col-xs-4 small">
      ${__('Standard Selling')}: ${format_currency(selling_price)}
      </div>
      <div class="col-xs-4 small">
      ${__('Standard Buying')}: ${format_currency(buying_price)}
      </div>
      <div class="col-xs-4 small">
      ${__('Standard Margin')}: ${
    selling_price
      ? (((selling_price - (buying_price || 0)) / selling_price) * 100).toFixed(
          2
        ) + '%'
      : 'N/A'
  }
      </div>
    </div>
  `);
}

export default {
  refresh: function(frm) {
    show_prices(frm);
  },
};
