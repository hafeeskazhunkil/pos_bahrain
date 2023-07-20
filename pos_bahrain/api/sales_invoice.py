import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.due_date = source.posting_date
        target.bill_date = source.posting_date
        target.bill_no = source.name
        target.inter_company_invoice_reference = None
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    doc = get_mapped_doc("Sales Invoice", source_name, {
        "Sales Invoice": {
            "doctype": "Purchase Invoice",
            "validation": {
                "docstatus": ["=", 1],
            },
        },
        "Sales Invoice Item": {
            "doctype": "Purchase Invoice Item",
        },
        "Payment Schedule": {
            "doctype": "Payment Schedule",
        },
    }, target_doc, set_missing_values)

    return doc


@frappe.whitelist()
def make_sales_return(source_name, target_doc=None):
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
    sales_return = make_sales_return(source_name, target_doc)
    return _prepend_returned_si(sales_return)


def _prepend_returned_si(si):
    prepend_return_pos_name = frappe.db.get_single_value("POS Bahrain Settings", "prepend_return_pos_name")
    if prepend_return_pos_name and si.offline_pos_name:
        si.offline_pos_name = "RET-{}".format(si.offline_pos_name)
    return si
