frappe.ui.form.on('Sales Invoice', {
  refresh: function (frm) {
    get_employee(frm);
    _create_custom_buttons(frm);
    pos_bahrain.scripts.extensions.hide_sales_return('Return / Credit Note', 'Create');
  },
  customer: function (frm) {
    _set_customer_account_balance(frm);
  },
  validate: function(frm){
    check_duplicate(frm);
  }
 
});

frappe.ui.form.on('Sales Invoice Item', {
  item_code: function (frm, cdt, cdn) {
    get_total_stock_qty(frm, cdt, cdn)
  },
});

function check_duplicate(frm) {
  if (frm.doc.is_pos && frm.doc.offline_pos_name && frm.doc.is_return) {
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        'doctype': 'Sales Invoice',
        'filters': [['offline_pos_name', 'LIKE', split_str_og(frm.doc.offline_pos_name) + '%']],
        'fields': ['offline_pos_name'],
        'fieldname': ['offline_pos_name']
      },
      callback: function (r) {
        var biggest = 0;
        var offline_pos;
        r.message.forEach(pos_name => {
          var amended_pos = split_str(pos_name.offline_pos_name)
          if (amended_pos.amend_no > biggest) {
            biggest = amended_pos.amend_no
            offline_pos = amended_pos.amended_str
          }
        });
        frm.set_value("offline_pos_name", offline_pos);
      }
    });
  }
}

function split_str(str_) {
  var amended_str;
  var amend_no = 0;
  var split_str = str_.split("-");
  if (split_str.length == 2) {
    amend_no = 1
    amended_str = (str_ + " - 1");
  }
  if (split_str.length == 3) {
    amend_no = Number(split_str[2]) + 1;
    amended_str = split_str[0] + "-" + split_str[1] + "- " + amend_no;
  }
  return { "amended_str": amended_str, "amend_no": amend_no };
}

function split_str_og(str_) {
  var amended_str_ws;
  var amended_str;
  var split_str = str_.split("-");
  if (split_str.length == 3) {
    var amend_no = Number(split_str[2]) + 1;
    amended_str_ws = split_str[0] + "-" + split_str[1];
    amended_str = amended_str_ws.replace(/\s+$/, '')
  }
  else amended_str = str_
  return amended_str;
}

function _create_custom_buttons(frm) {
  if (frm.doc.docstatus !== 1) {
    return;
  }
  frm.add_custom_button(__("Purchase Invoice"), function () {
    _make_purchase_invoice(frm);
  }, __("Create"));
}


function _make_purchase_invoice(frm) {
  frappe.model.open_mapped_doc({
    method: "pos_bahrain.api.sales_invoice.make_purchase_invoice",
    frm,
  });
}


async function _set_customer_account_balance(frm) {
  if(frm.doc.customer != null){
    const account_balance = await _get_customer_account_balance(frm.doc.customer);
    frm.set_value("pb_available_balance", account_balance);
  } 
}


async function _get_customer_account_balance(customer) {
  const { message: data } = await frappe.call({
    method: "pos_bahrain.api.sales_invoice.get_customer_account_balance",
    args: { customer },
  })
  return data;
}

function get_employee(frm) {
  if (!frm.doc.pb_sales_employee && frm.doc.__islocal) {
    frappe.call({
      method: "pos_bahrain.api.sales_invoice.get_logged_employee_id",
      callback: function (r) {
        if (r.message != 0) {
          frm.set_value("pb_sales_employee", r.message)
        }
      }
    })
  }
}

function get_total_stock_qty(frm, cdt, cdn) {
  var d = locals[cdt][cdn];
  if (d.item_code === undefined) {
    return;
  }
  frappe.call({
    method: "pos_bahrain.api.stock.get_total_stock_qty",
    args: {
      item_code: d.item_code
    },
    callback: function (r) {
      frappe.model.set_value(cdt, cdn, "total_available_qty", r.message);
    }
  })
}

frappe.ui.form.on('Sales Invoice', {
  validate: function (frm) {
    if (cur_frm.doc.is_return) {
      cur_frm.set_value("main_invoice", "");
      cur_frm.set_value("return_si_no", "");
      cur_frm.set_value("credit_note_invoice", "");
      cur_frm.set_value("main_si", "");
      cur_frm.set_value("credit_note_balance", cur_frm.doc.grand_total);
     }
  }
})
cur_frm.fields_dict.return_si_no.get_query = function(doc) {
	return {
		filters: {
			customer: doc.customer,
			company:doc.company,
			docstatus:1,
			is_return : 1
					
		}
	}
}
frappe.ui.form.on('Sales Invoice Advance',"refresh", function(){
  if (cur_frm.doc.advances){
  for (var i =0; i < cur_frm.doc.advances.length; i++){
   if (cur_frm.doc.items[i].reference_type = "Sales Invoice") {  
  cur_frm.doc.credit_note_invoice=cur_frm.doc.advances[i].reference_name
  }
   }
   }
  })
frappe.ui.form.on('Sales Invoice',"validate", function(){
  if (cur_frm.doc.advances){
  for (var i =0; i < cur_frm.doc.advances.length; i++){
   if (cur_frm.doc.items[i].reference_type = "Sales Invoice") {  
  cur_frm.doc.credit_note_invoice=cur_frm.doc.advances[i].reference_name
  }
   }
   }
  })

 frappe.ui.form.on("Sales Invoice", "ignore_payments_for_return", function(frm, doctype, name){
    if (frm.doc.is_return && frm.doc.ignore_payments_for_return){
    cur_frm.clear_table("payments"); 
    frm.doc.is_pos = 0
    cur_frm.refresh_fields();
    }
    });
  frappe.ui.form.on("Sales Invoice", "validate", function(frm, doctype, name){
      if (frm.doc.is_return && frm.doc.ignore_payments_for_return){
      cur_frm.clear_table("payments"); 
      frm.doc.is_pos = 0
      cur_frm.refresh_fields();
      }
      });
      frappe.ui.form.on("Sales Invoice Item", "qty", function(frm, cdt, cdn) {
        $.each(frm.doc.advances || [], function(i, d) {
            d.allocated_amount=cur_frm.doc.rounded_total-cur_frm.doc.base_write_off_amount;
        });
        refresh_field("advances");
        })
        frappe.ui.form.on("Sales Invoice Item", "rate", function(frm, cdt, cdn) {
        $.each(frm.doc.advances || [], function(i, d) {
            d.allocated_amount=cur_frm.doc.rounded_total-cur_frm.doc.base_write_off_amount;
        });
        refresh_field("advances");
        })
        frappe.ui.form.on("Sales Invoice", "validate", function(frm, cdt, cdn) {
        $.each(frm.doc.advances || [], function(i, d) {
            if(cur_frm.doc.grand_total<=d.advance_amount){
            d.allocated_amount=cur_frm.doc.rounded_total-cur_frm.doc.base_write_off_amount;
            }
            else{
               d.allocated_amount=d.advance_amount;
            }
        });
        refresh_field("advances");
        
        })
      