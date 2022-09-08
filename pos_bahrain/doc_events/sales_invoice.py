# -*- coding: utf-8 -*-
# Copyright (c) 2018, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, today
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_delivery_note
from pos_bahrain.api.sales_invoice import get_customer_account_balance
from functools import partial
from toolz import first, compose, pluck, unique


def validate(doc, method):
    if (
        doc.is_pos
        and not doc.is_return
        and not doc.amended_from
        and doc.offline_pos_name
        and frappe.db.exists(
            "Sales Invoice",
            {"offline_pos_name": doc.offline_pos_name, "name": ("!=", doc.name)},
        )
    ):
        frappe.throw("Cannot create duplicate offline POS invoice")
    for payment in doc.payments:
        if payment.amount:
            bank_method = frappe.get_cached_value(
                "Mode of Payment", payment.mode_of_payment, "pb_bank_method"
            )
            if bank_method and not payment.pb_reference_no:
                frappe.throw(
                    "Reference Number necessary in payment row #{}".format(payment.idx)
                )
            if bank_method == "Cheque" and not payment.pb_reference_date:
                frappe.throw(
                    "Reference Date necessary in payment row #{}".format(payment.idx)
                )

    _validate_return_series(doc)
    doc.pb_available_balance = get_customer_account_balance(doc.customer)

def before_save(doc, method):
    set_cost_center(doc)
    set_location(doc)
    

def on_submit(doc, method):
    for payment in doc.payments:
        if not payment.mop_currency:
            currency = frappe.db.get_value(
                "Mode of Payment", payment.mode_of_payment, "alt_currency"
            )
            conversion_rate = (
                get_exchange_rate(
                    currency, frappe.defaults.get_user_default("currency")
                )
                if currency
                else 1.0
            )
            frappe.db.set_value(
                "Sales Invoice Payment",
                payment.name,
                "mop_currency",
                currency or frappe.defaults.get_user_default("currency"),
            )
            frappe.db.set_value(
                "Sales Invoice Payment",
                payment.name,
                "mop_conversion_rate",
                conversion_rate,
            )
            frappe.db.set_value(
                "Sales Invoice Payment",
                payment.name,
                "mop_amount",
                flt(payment.base_amount) / flt(conversion_rate),
            )

    _make_gl_entry_for_provision_credit(doc)
    _make_gl_entry_on_credit_issued(doc)
    _make_return_dn(doc)
    gl_entries_update(doc)
    update_credit_note(doc)


def before_cancel(doc, method):
    gl_entries_cancel(doc)
    update_credit_note_cancel(doc)
    parent = _get_parent_by_account(doc.name)
    if not parent:
        return

    je_doc = frappe.get_doc("Journal Entry", parent)
    je_doc.cancel()


def on_cancel(doc, method):
    gl_entries_cancel(doc)
    cancel_jv(doc)
    if not doc.pb_returned_to_warehouse:
        return

    get_dns = compose(
        list,
        unique,
        partial(pluck, "parent"),
        frappe.db.sql,
    )
    dns = get_dns(
        """
            SELECT dni.parent AS parent
            FROM `tabDelivery Note Item` AS dni
            LEFT JOIN `tabDelivery Note` AS dn ON dn.name = dni.parent
            WHERE
                dn.docstatus = 1 AND
                dn.is_return = 1 AND
                dni.against_sales_invoice = %(against_sales_invoice)s
        """,
        values={"against_sales_invoice": doc.return_against},
        as_dict=1,
    )
    if not dns:
        return
    if len(dns) > 1:
        frappe.throw(
            _(
                "Multiple Delivery Notes found for this Sales Invoice. "
                "Please cancel from the return Delivery Note manually."
            )
        )

    dn_doc = frappe.get_doc("Delivery Note", first(dns))
    for i, item in enumerate(dn_doc.items):
        if item.item_code != doc.items[i].item_code or item.qty != doc.items[i].qty:
            frappe.throw(
                _(
                    "Mismatched <code>item_code</code> / <code>qty</code> "
                    "found in <em>items</em> table."
                )
            )
    dn_doc.cancel()

def cancel_jv(doc):
    if(doc.pb_credit_note_no):
        jv_doc = frappe.get_doc("Journal Entry", doc.pb_credit_note_no)
        jv_doc.cancel()

def _validate_return_series(doc):
    if not doc.is_return:
        return
    return_series = frappe.db.get_single_value("POS Bahrain Settings", "return_series")
    if return_series:
        if doc.naming_series != return_series:
            frappe.throw(
                _(
                    "Only naming series <strong>{}</strong> is allowed for Credit Note. Please change it.".format(
                        return_series
                    )
                )
            )


def _make_return_dn(doc):
    if not doc.is_return or not doc.pb_returned_to_warehouse:
        return

    return_against_update_stock = frappe.db.get_value(
        "Sales Invoice",
        doc.return_against,
        "update_stock",
    )
    if return_against_update_stock:
        return

    dns = frappe.get_all(
        "Delivery Note Item",
        filters={"against_sales_invoice": doc.return_against, "docstatus": 1},
        fields=["parent", "item_code", "batch_no", "warehouse"],
    )
    dn_parents = compose(
        list,
        unique,
        partial(pluck, "parent"),
    )(dns)
    if not dns:
    #    frappe.throw(_("There are no Delivery Note items to returned to"))
        return
    if len(dn_parents) > 1:
        frappe.throw(
            _(
                "Multiple Delivery Notes found for this Sales Invoice. "
                "Please make Delivery Note return manually."
            )
        )

    item_warehouses = {x.get("item_code"): x.get("warehouse") for x in dns}
    item_batch_nos = {x.get("item_code"): x.get("batch_no") for x in dns}

    dn_doc = make_delivery_note(doc.return_against)

    excluded_items = []
    for item in dn_doc.items:
        si_item = list(
            filter(
                lambda x: x.item_code == item.item_code,
                doc.items,
            ),
        )
        if si_item:
            item.qty = first(si_item).qty
            item.stock_qty = first(si_item).stock_qty
            item.warehouse = item_warehouses.get(item.item_code)
            item.batch_no = item_batch_nos.get(item.item_code)

    dn_doc.items = list(filter(lambda x: x.item_code not in excluded_items, dn_doc.items))
    dn_doc.is_return = 1
    dn_doc.return_against = first(dn_parents)
    dn_doc.set_warehouse = doc.pb_returned_to_warehouse
    dn_doc.run_method("calculate_taxes_and_totals")
    dn_doc.insert()
    dn_doc.submit()


def _get_parent_by_account(name):
    data = frappe.db.sql(
        """
        SELECT je.name 
        FROM `tabJournal Entry` je
        JOIN `tabJournal Entry Account` jea
        ON jea.parent = je.name
        WHERE jea.reference_type = "Sales Invoice"
        AND jea.reference_name = %s
        """,
        name,
        as_dict=1,
    )
    if not data:
        return

    provision_account = frappe.db.get_single_value(
        "POS Bahrain Settings",
        "credit_note_provision_account",
    )
    if not provision_account:
        return

    je_name = data[0].get("name")
    provision_account = frappe.db.sql(
        """
        SELECT 1 FROM `tabJournal Entry Account`
        WHERE parent = %s
        AND account = %s
        """,
        (je_name, provision_account),
    )

    return je_name if provision_account else None


def set_cost_center(doc):
    if doc.pb_set_cost_center:
        for row in doc.items:
            row.cost_center = doc.pb_set_cost_center
        for row in doc.taxes:
            row.cost_center = doc.pb_set_cost_center


def set_location(doc):
    for row in doc.items:
        row.pb_location = _get_location(row.item_code, row.warehouse)


def _get_location(item_code, warehouse):
    locations = frappe.get_all(
        "Item Storage Location",
        filters={"parent": item_code, "warehouse": warehouse},
        fields=["storage_location"],
    )

    location = None
    if locations:
        location = first(locations).get("storage_location")

    return location


def _make_gl_entry_on_credit_issued(doc):
    if doc.is_return:
        return
    
    if not doc.pb_use_credit_if_available:
        return
        
    enable_jv_concept = frappe.db.get_single_value(
        "POS Bahrain Settings", "enable_jv_concept"
    )
    if not enable_jv_concept:
        return

    provision_account = frappe.db.get_single_value(
        "POS Bahrain Settings", "credit_note_provision_account"
    )
    if not provision_account:
        return

    account_balance = doc.pb_available_balance
    if not account_balance:
        return

    carry_over = (
        account_balance
        if account_balance < doc.outstanding_amount
        else doc.outstanding_amount
    )

    if not carry_over:
        return

    je_doc = frappe.new_doc("Journal Entry")
    je_doc.posting_date = today()
    je_doc.append(
        "accounts",
        {
            "account": doc.debit_to,
            "party_type": "Customer",
            "party": doc.customer,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": carry_over,
            "reference_type": "Sales Invoice",
            "reference_name": doc.name,
        },
    )
    je_doc.append(
        "accounts",
        {
            "account": provision_account,
            "party_type": "Customer",
            "party": doc.customer,
            "debit_in_account_currency": carry_over,
            "credit_in_account_currency": 0,
        },
    )

    je_doc.save()
    je_doc.submit()

    after_balance = doc.pb_available_balance - carry_over
    frappe.db.set_value("Sales Invoice", doc.name, "pb_after_balance", after_balance)


def _make_gl_entry_for_provision_credit(doc):
    if not doc.is_return or doc.is_pos or not doc.credit_note:
        return

    enable_jv_concept = frappe.db.get_single_value(
        "POS Bahrain Settings", "enable_jv_concept"
    )
    if not enable_jv_concept:
        return

    provision_account = frappe.db.get_single_value(
        "POS Bahrain Settings", "credit_note_provision_account"
    )
    if not provision_account:
        return

    account_balance = get_customer_account_balance(doc.customer)
    if not account_balance:
        return

    je_doc = frappe.new_doc("Journal Entry")
    je_doc.posting_date = today()

    jv_naming_series = frappe.db.get_single_value(
        "POS Bahrain Settings", "jv_credit_note_series"
    )
    if jv_naming_series:
        je_doc.naming_series = jv_naming_series
    
    je_doc.append(
        "accounts",
        {
            "account": provision_account,
            "party_type": "Customer",
            "party": doc.customer,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": abs(doc.grand_total - doc.outstanding_amount),
        },
    )
    je_doc.append(
        "accounts",
        {
            "account": doc.debit_to,
            "party_type": "Customer",
            "party": doc.customer,
            "debit_in_account_currency": abs(doc.grand_total - doc.outstanding_amount),
            "credit_in_account_currency": 0,
        },
    )

    je_doc.save()
    je_doc.submit()
    frappe.db.sql("""UPDATE `tabSales Invoice` SET pb_credit_note_no='%(jv)s' where name='%(si)s'"""%
                    {"jv":je_doc.name, "si":doc.name})

def gl_entries_cancel(doc):
    gl_name = frappe.db.sql(
        """
        SELECT name 
        FROM `tabGL Entry`
        WHERE voucher_type = "Sales Invoice"
        AND voucher_no =%(main_invoice)s  AND debit = 0 and party = %(customer)s 
        """, values={"main_invoice": doc.main_invoice, "customer":doc.customer},

        as_dict=1,)
    # print("/////////",gl_name)    
    if not doc.is_return and gl_name:
        for name in gl_name:
            frappe.db.set_value("GL Entry", name, "credit", doc.paid_amount)
            frappe.db.set_value("GL Entry", name, "credit_in_account_currency", doc.paid_amount)
            frappe.db.set_value("Sales Invoice", doc.main_invoice, "outstanding_amount", -doc.paid_amount)
            doc.set_status(update=True)

def gl_entries_update(doc):
    return_against = frappe.db.get_value("Sales Invoice",doc.return_si_no, "return_against")
    gl_name = frappe.db.sql(
        """
        SELECT name,credit
        FROM `tabGL Entry`
        WHERE voucher_type = "Sales Invoice"
        AND voucher_no =%(main_invoice)s  and party = %(customer)s and debit = 0
        """, values={"main_invoice": doc.main_invoice, "customer":doc.customer},

        as_dict=1,
    )
    # print("/////////",gl_name)
    if not doc.is_return and gl_name:
        for name in gl_name:
            frappe.db.set_value("GL Entry", name, "credit", gl_name.credit-doc.total_advance)
            frappe.db.set_value("GL Entry", name, "credit_in_account_currency", gl_name.credit-doc.total_advance)
            frappe.db.set_value("GL Entry", name, "remarks", "Credit Note Adjustment")
            frappe.db.set_value("Sales Invoice", doc.main_invoice, "outstanding_amount", 0)
            doc.set_status(update=True)

def update_credit_note(doc, cancel=False):
        cn_inv = frappe.get_doc('Sales Invoice',doc.name)
        return_against = frappe.db.get_value("Sales Invoice",doc.credit_note_invoice, "return_against")
        if doc.is_return :
            doc.credit_note_balance = doc.grand_total
        if not doc.is_return and doc.credit_note_invoice:
            cn_balance = frappe.db.get_value("Sales Invoice",doc.credit_note_invoice,"credit_note_balance")
            main_outstanding = frappe.db.get_value("Sales Invoice",return_against,"outstanding_amount")
            frappe.db.set_value("Sales Invoice", doc.credit_note_invoice, "credit_note_balance", cn_balance+doc.total_advance)
            # frappe.db.set_value("Sales Invoice", doc.main_si, "outstanding_amount", 0)
            frappe.db.set_value("Sales Invoice", doc.credit_note_invoice, "outstanding_amount", 0)
            frappe.db.set_value("Sales Invoice", doc.name, "outstanding_amount", 0)
        #     doc.write_off_amount = doc.total_advance
        #     frappe.db.set_value("Sales Invoice", doc.name, "write_off_amount", doc.total_advance)
            frappe.db.set_value("Sales Invoice", doc.name, "base_paid_amount", doc.total_advance)
            frappe.db.set_value("Sales Invoice", doc.name, "paid_amount", doc.total_advance)
            frappe.db.set_value("Sales Invoice", doc.name, "status", "Paid")
            frappe.db.set_value("Sales Invoice", doc.credit_note_invoice, "status", "Return")

        gl_no = frappe.db.sql(
            """
            SELECT name 
            FROM `tabGL Entry`
            WHERE voucher_type = "Sales Invoice"
            AND voucher_no =%(main_si)s  and party = %(customer)s and credit = 0
            """, values={"main_si": doc.name, "customer":doc.customer},

            as_dict=1,
        )
        # print("/////////",gl_no.credit)
        
        if not doc.is_return and doc.credit_note_invoice and gl_no:
            for name in gl_no:
                # gl_credit = frappe.db.get_value("GL Entry",name,"credit")
                frappe.db.set_value("GL Entry", name, "credit", doc.total_advance)
                frappe.db.set_value("GL Entry", name, "credit_in_account_currency",doc.total_advance)
                # frappe.db.set_value("GL Entry", name, "against_voucher", doc.name)
                # frappe.db.set_value("GL Entry", name, "voucher_no", doc.name)
                frappe.db.set_value("GL Entry", name, "remarks", "Credit Note Adjustment")
                frappe.db.set_value("Sales Invoice", return_against, "outstanding_amount", main_outstanding+doc.total_advance)
                frappe.db.set_value("Sales Invoice", doc.name, "main_si", return_against)
                doc.set_status(update=True)
        gl_name = frappe.db.sql(
            """
            SELECT name 
            FROM `tabGL Entry`
            WHERE voucher_type = "Sales Invoice"
            AND voucher_no =%(main_si)s  and party = %(customer)s and debit = 0
            """, values={"main_si": return_against, "customer":doc.customer, "remarks":"Credit Note Adjustment"},

            as_dict=1,
        )
        if not doc.is_return and doc.credit_note_invoice:        
            for name in gl_name:
                gl_credit = frappe.db.get_value("GL Entry",name,"credit")
                frappe.db.set_value("GL Entry", name, "credit", gl_credit-doc.total_advance)
                frappe.db.set_value("GL Entry", name, "credit_in_account_currency",gl_credit-doc.total_advance)
                frappe.db.set_value("GL Entry", name, "remarks", "Credit Note Adjustment")
                doc.set_status(update=True)
def update_credit_note_cancel(doc):
    if doc.credit_note_invoice:
        cn_balance = frappe.db.get_value("Sales Invoice",doc.credit_note_invoice,"credit_note_balance")
        frappe.db.set_value("Sales Invoice", doc.credit_note_invoice, "credit_note_balance", cn_balance-doc.total_advance)
    return_against = frappe.db.get_value("Sales Invoice",doc.credit_note_invoice, "return_against")    
    gl_no = frappe.db.sql(
        """
        SELECT name 
        FROM `tabGL Entry`
        WHERE voucher_type = "Sales Invoice"
        AND voucher_no =%(main_si)s  and party = %(customer)s and debit = 0 and remarks = "Credit Note Adjustment"
        """, values={"main_si": return_against, "customer":doc.customer},

        as_dict=1,
    )
        # print("/////////",gl_name)
    if not doc.is_return and doc.credit_note_invoice and gl_no:
        for name in gl_no:
            gl_credit = frappe.db.get_value("GL Entry",name,"credit")
            main_outstanding = frappe.db.get_value("Sales Invoice",return_against,"outstanding_amount")
            paid_amount = frappe.db.get_value("Sales Invoice",return_against,"paid_amount")
            frappe.db.set_value("GL Entry", name, "credit", gl_credit+doc.total_advance)
            frappe.db.set_value("GL Entry", name, "credit_in_account_currency", gl_credit+doc.total_advance)
            # frappe.db.set_value("GL Entry", name, "against_voucher", doc.main_si)
            # frappe.db.set_value("GL Entry", name, "voucher_no", doc.main_si)
            frappe.db.set_value("GL Entry", name, "remarks", "Credit Note Adjustment")
            frappe.db.set_value("Sales Invoice", return_against, "outstanding_amount", main_outstanding-doc.total_advance)
            doc.set_status(update=True)


def update_cn_write_off_amt_amount(doc):
    # cn_inv = frappe.get_doc('Sales Invoice',doc.name)
    # cn_inv.flags.ignore_validate_update_after_submit = True
    if not doc.is_return and doc.credit_note_invoice:
        cn_balance = frappe.db.get_value("Sales Invoice",doc.credit_note_invoice,"credit_note_balance")
        frappe.db.set_value("Sales Invoice", doc.credit_note_invoice, "credit_note_balance", cn_balance-doc.total_advance)
    
