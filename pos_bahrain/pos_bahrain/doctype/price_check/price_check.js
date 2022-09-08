// Copyright (c) 2021, 	9t9it and contributors
// For license information, please see license.txt

frappe.ui.form.on('Price Check', {
	refresh: function(frm){
		cur_frm.disable_save();
		cur_frm.set_value("price","");
		cur_frm.fields_dict.check.$input.on("click", function(evt){
			setTimeout(clear_fields(), 5000)
		})
	},
	check : function(frm){
		check_price(frm);
	}
});

function clear_fields(){
	console.log("Clear field ::::::::::::::::::::::s")
}
function check_price(frm){
	console.log("check called")
	frappe.call({
		method:
		  'pos_bahrain.api.price_checker.search_barcode',
		args: { 
			"barcode" : frm.doc.barcode 
		},
		callback: function(r){
			if(r.message == "Item/Price not found"){
				frappe.msgprint("Item/Price not found")
				cur_frm.set_value("barcode","")
				cur_frm.set_value("item_name","")
				cur_frm.set_value("price","")
				return
			}
			else{
				cur_frm.set_value("barcode","")
				cur_frm.set_value("item_name",r.message[0].item_name)
				cur_frm.set_value("price",r.message[0].price_list_rate)
				cur_frm.refresh_fields()

			}
			cur_frm.fields_dict.my_field.$input.on("click", function(evt){

			})
			
		}
	  });
}
