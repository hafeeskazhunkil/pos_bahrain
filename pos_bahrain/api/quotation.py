import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate, getdate
from frappe import _


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    return _make_sales_invoice(source_name, target_doc)


def _make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
    customer = _make_customer(source_name, ignore_permissions)

    def set_missing_values(source, target):
        if customer:
            target.customer = customer.name
            target.customer_name = customer.customer_name
        target.ignore_pricing_rule = 1
        target.flags.ignore_permissions = ignore_permissions
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

        # Terms and Conditions
        target.tc_name = target.meta.get_field("tc_name").default
        if target.tc_name:
            target.terms = frappe.db.get_value(
                "Terms and Conditions", target.tc_name, "terms"
            )

    def update_item(obj, target, source_parent):
        target.cost_center = None
        target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)
        target.reference_dt = "Quotation"
        target.reference_dn = obj.parent

    doclist = get_mapped_doc(
        "Quotation",
        source_name,
        {
            "Quotation": {
                "doctype": "Sales Invoice",
                "validation": {"docstatus": ["=", 1]},
            },
            "Quotation Item": {
                "doctype": "Sales Invoice Item",
                "postprocess": update_item,
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True,
            },
            "Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
        },
        target_doc,
        set_missing_values,
        ignore_permissions=ignore_permissions,
    )

    return doclist


def _make_customer(source_name, ignore_permissions=False):
    quotation = frappe.db.get_value(
        "Quotation",
        source_name,
        ["order_type", "party_name", "customer_name"],
        as_dict=1,
    )

    if quotation and quotation.get("party_name"):
        if not frappe.db.exists("Customer", quotation.get("party_name")):
            lead_name = quotation.get("party_name")
            customer_name = frappe.db.get_value(
                "Customer",
                {"lead_name": lead_name},
                ["name", "customer_name"],
                as_dict=True,
            )
            if not customer_name:
                from erpnext.crm.doctype.lead.lead import _make_customer

                customer_doclist = _make_customer(
                    lead_name, ignore_permissions=ignore_permissions
                )
                customer = frappe.get_doc(customer_doclist)
                customer.flags.ignore_permissions = ignore_permissions
                if quotation.get("party_name") == "Shopping Cart":
                    customer.customer_group = frappe.db.get_value(
                        "Shopping Cart Settings", None, "default_customer_group"
                    )

                try:
                    customer.insert()
                    return customer
                except frappe.NameError:
                    if (
                        frappe.defaults.get_global_default("cust_master_name")
                        == "Customer Name"
                    ):
                        customer.run_method("autoname")
                        customer.name += "-" + lead_name
                        customer.insert()
                        return customer
                    else:
                        raise
                except frappe.MandatoryError:
                    frappe.local.message_log = []
                    frappe.throw(
                        _("Please create Customer from Lead {0}").format(lead_name)
                    )
            else:
                return customer_name
        else:
            return frappe.get_doc("Customer", quotation.get("party_name"))
