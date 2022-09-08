erpnext.pos.PointOfSale = erpnext.pos.PointOfSale.extend({
  onload: function() {
    this._super();
    this.setinterval_to_sync_master_data(600000);
  },
  init_master_data: async function(r, freeze = true) {
    this._super(r);
    try {
      const { message: pos_data = {} } = await frappe.call({
        method: 'pos_bahrain.api.item.get_more_pos_data',
        args: {
          profile: this.pos_profile_data.name,
          company: this.doc.company,
        },
        freeze,
        freeze_message: __('Syncing Item details'),
      });

      await this.set_opening_entry();
      return pos_data;
    } catch (e) {
      frappe.msgprint({
        indicator: 'orange',
        title: __('Warning'),
        message: __(
          'Unable to load extended Item details. Usage will be restricted.'
        ),
      });
    }
  },
  setinterval_to_sync_master_data: function(delay) {
    setInterval(async () => {
      const { message } = await frappe.call({ method: 'frappe.handler.ping' });
      if (message) {
        const r = await frappe.call({
          method: 'erpnext.accounts.doctype.sales_invoice.pos.get_pos_data',
        });
        localStorage.setItem('doc', JSON.stringify(r.message.doc));
        this.init_master_data(r, false);
        this.load_data(false);
        this.make_item_list();
        this.set_missing_values();
      }
    }, delay);
  },
  set_opening_entry: async function() {
    const { message: pos_voucher } = await frappe.call({
      method: 'pos_bahrain.api.pos_voucher.get_unclosed',
      args: {
        user: frappe.session.user,
        pos_profile: this.pos_profile_data.name,
        company: this.doc.company,
      },
    });
    if (pos_voucher) {
      this.pos_voucher = pos_voucher;
    } else {
      const dialog = new frappe.ui.Dialog({
        title: __('Enter Opening Cash'),
        fields: [
          {
            fieldtype: 'Datetime',
            fieldname: 'period_from',
            label: __('Start Date Time'),
            default: frappe.datetime.now_datetime(),
          },
          {
            fieldtype: 'Currency',
            fieldname: 'opening_amount',
            label: __('Amount'),
          },
        ],
      });
      dialog.show();
      dialog.get_close_btn().hide();
      dialog.set_primary_action('Enter', async () => {
        try {
          const { message: voucher_name } = await frappe.call({
            method: 'pos_bahrain.api.pos_voucher.create_opening',
            args: {
              posting: dialog.get_value('period_from'),
              opening_amount: dialog.get_value('opening_amount'),
              company: this.doc.company,
              pos_profile: this.pos_profile_data.name,
            },
          });
          if (!voucher_name) {
            throw Exception;
          }
          this.pos_voucher = voucher_name;
        } catch (e) {
          frappe.msgprint({
            message: __('Unable to create POS Closing Voucher opening entry.'),
            title: __('Warning'),
            indicator: 'orange',
          });
        } finally {
          dialog.hide();
          dialog.$wrapper.remove();
        }
      });
    }
  },
  show_items_in_item_cart: function() {
    this._super();
    this.wrapper
      .find('.items')
      .find('.pos-bill-item > .cell:nth-child(3)')
      .each((i, el) => {
        const value = el.innerText;
        if (value !== '0') {
          el.innerText = flt(value, this.precision);
        }
      });
  },
  make_menu_list: function() {
    this._super();
    this.page.menu
      .find('a.grey-link:contains("Cashier Closing")')
      .parent()
      .hide();
    this.page.add_menu_item('POS Closing Voucher', async () => {
      if (this.connection_status) {
        if (!this.pos_voucher) {
          await this.set_opening_entry();
        }
        frappe.dom.freeze('Syncing');
        this.sync_sales_invoice();
        await frappe.after_server_call();
        frappe.set_route('Form', 'POS Closing Voucher', this.pos_voucher, {
          period_to: frappe.datetime.now_datetime(),
        });
        frappe.dom.unfreeze();
        this.pos_voucher = null;
      } else {
        frappe.msgprint({
          message: __('Please perform this when online.'),
        });
      }
    });
  },
  update_paid_amount_status: function (update_paid_amount) {
		if (this.frm.doc.offline_pos_name) {
			update_paid_amount = update_paid_amount ? false : true;
		}

		this.refresh(update_paid_amount);
	},

	refresh: function (update_paid_amount) {
		var me = this;
		this.refresh_fields(update_paid_amount);
		this.set_primary_action();
		this.apply_pricing_rule();
	},
  
  refresh_fields: function(update_paid_amount) {
    this.apply_pricing_rule();
    this.discount_amount_applied = false;
    this._calculate_taxes_and_totals();
    this.calculate_discount_amount();
    this.show_items_in_item_cart();
    this.set_taxes();
    this.calculate_outstanding_amount(update_paid_amount);
    this.set_totals();
    this.update_total_qty();
  },
  update_total_qty: function() {
    var me = this;
    var qty_total = 0;
    $.each(this.frm.doc['items'] || [], function(i, d) {
      if (d.item_code) {
        qty_total += d.qty;
      }
    });
    this.frm.doc.qty_total = qty_total;
    this.wrapper.find('.qty-total').text(this.frm.doc.qty_total);
  },
  update_serial_no: function() {
		// var me = this;

		// //Remove the sold serial no from the cache
		// $.each(this.frm.doc.items, function(index, data) {
		// 	var sn = data.serial_no.split('\n')
		// 	if(sn.length) {
		// 		var serial_no_list = me.serial_no_data[data.item_code]
		// 		if(serial_no_list) {
		// 			$.each(sn, function(i, serial_no) {
		// 				if(in_list(Object.keys(serial_no_list), serial_no)) {
		// 					delete serial_no_list[serial_no]
		// 				}
		// 			})
		// 			me.serial_no_data[data.item_code] = serial_no_list;
		// 		}
		// 	}
		// })
	},
  create_invoice: function() {
    var me = this;
    var invoice_data = {};
    function get_barcode_uri(text) {
      return JsBarcode(document.createElement('canvas'), text, {
        height: 40,
        displayValue: false,
      })._renderProperties.element.toDataURL();
    }
    this.si_docs = this.get_doc_from_localstorage();
    if (this.frm.doc.offline_pos_name) {
      this.update_invoice();
    } else {
      this.frm.doc.offline_pos_name = $.now();
      this.frm.doc.pos_name_barcode_uri = get_barcode_uri(
        this.frm.doc.offline_pos_name
      );
      this.frm.doc.posting_date = frappe.datetime.get_today();
      this.frm.doc.posting_time = frappe.datetime.now_time();
      this.frm.doc.pos_total_qty = this.frm.doc.qty_total;
      this.frm.doc.pos_profile = this.pos_profile_data['name'];
      this.frm.doc.pb_set_cost_center = this.pos_profile_data['write_off_cost_center'];
      invoice_data[this.frm.doc.offline_pos_name] = this.frm.doc;
      this.si_docs.push(invoice_data);
      this.update_localstorage();
      this.set_primary_action();
    }
    return invoice_data;
  },
  sync_sales_invoice: function() {
    const me = this;

    // instead of replacing instance variables
    const si_docs = this.get_submitted_invoice() || [];
    const email_queue_list = this.get_email_queue() || {};
    const customers_list = this.get_customers_details() || {};
    const pos_profile = this.pos_profile_data || {};

    if (si_docs.length || email_queue_list || customers_list) {
      frappe.call({
        method: "erpnext.accounts.doctype.sales_invoice.pos.make_invoice",
        freeze: true,
        args: {
          doc_list: si_docs,
          email_queue_list,
          customers_list,
          pos_profile
        },
        callback: function (r) {
          if (r.message) {
            me.freeze = false;
            me.customers = r.message.synced_customers_list;
            me.address = r.message.synced_address;
            me.contacts = r.message.synced_contacts;
            me.removed_items = r.message.invoice;
            me.removed_email = r.message.email_queue;
            me.removed_customers = r.message.customers;
            me.remove_doc_from_localstorage();
            me.remove_email_queue_from_localstorage();
            me.remove_customer_from_localstorage();
            me.prepare_customer_mapper();
            me.autocomplete_customers();
            me.render_list_customers();
          }
        }
      });
    }
  },
  refresh: function() {
    this._super();
    if (!this.pos_voucher) {
      this.set_opening_entry();
    }
  },
  remove_selected_item: function() {
    const selected_item_idx = parseInt(this.selected_cart_idx) + 1;
    this.remove_item = []
    this.remove_item.push(selected_item_idx);
    this.remove_zero_qty_items_from_cart()
    this.update_paid_amount_status(false);

    // clean ui
    this.selected_row.hide();
    this.selected_cart_idx = null;
    this.selected_row = null;
  }
});

erpnext.pos.PointOfSale = pos_bahrain.addons.extend_pos(
  erpnext.pos.PointOfSale
);
