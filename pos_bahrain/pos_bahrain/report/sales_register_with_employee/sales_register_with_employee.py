# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.sales_register.sales_register import (
    execute as sales_register,
)
from toolz.curried import groupby, first, compose, valmap, concatv


def execute(filters=None):
    filters.net_amount_col_idx = 18
    return extend_report(sales_register, filters)


def extend_report(base_execute, filters):
    _validate_filters(filters)
    columns, data = base_execute(filters)
    inv_idx = next(x for x, v in enumerate(columns) if "Invoice" in v)
    emp_idx = len(columns)
    return (
        _extend_columns(filters, columns),
        _extend_data(filters, data, inv_idx, emp_idx),
    )


def _validate_filters(filters):
    if not 0 <= frappe.utils.flt(filters.commission_rate) <= 100:
        frappe.throw(frappe._("Commission Rate should be between 0 and 100%"))


def _extend_columns(filters, columns):
    return (
        ["Sales Employee:Link/Employee:120", "Sales Employee Name::150"]
        + columns
        + [
            "{}% Commission on Net Sales:Currency:120".format(
                frappe.utils.flt(filters.commission_rate)
            )
        ]
    )


def _extend_data(filters, data, inv_idx, emp_idx):
    invoices = [x[inv_idx] for x in data]
    get_employee_map = compose(
        valmap(lambda x: [x.get("pb_sales_employee"), x.get("pb_sales_employee_name")]),
        valmap(first),
        groupby("name"),
        lambda: frappe.db.sql(
            """
            SELECT name, pb_sales_employee, pb_sales_employee_name FROM `tabSales Invoice`
            WHERE name IN %(invoices)s
        """,
            values={"invoices": invoices},
            as_dict=1,
        ),
    )
    employees = get_employee_map() if invoices else {}
    set_employee = compose(list, lambda x: concatv(employees[x[inv_idx]], x))
    set_commission = compose(
        list,
        lambda x: concatv(
            x,
            [
                x[filters.net_amount_col_idx]
                * frappe.utils.flt(filters.commission_rate)
                / 100
            ],
        ),
    )

    make_row = compose(set_employee, set_commission)
    extended = [make_row(x) for x in data]

    if not filters.sales_employee:
        return extended

    return [x for x in extended if x[emp_idx] == filters.sales_employee]
