# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import (
    execute as item_wise_sales_register,
)
from toolz import compose, partial


def execute(filters=None):
    columns, data = item_wise_sales_register(filters)
    return _extend_report(columns, data, filters)


def _extend_report(columns, data, filters):
    brand_idx = 2
    item_code_idx = 0
    return _extend_columns(columns, brand_idx), _extend_data(data, filters, brand_idx, item_code_idx)


def _extend_columns(columns, brand_idx):
    return columns[:brand_idx] + ["Brand:Link/Brand:120"] + columns[brand_idx:]


def _extend_data(data, filters, brand_idx, item_code_idx):
    def make_row(x):
        item_code = x[item_code_idx]
        brand = brands.get(item_code)
        return x[:brand_idx] + [brand] + x[brand_idx:]

    item_codes = list(set(map(lambda x: x[item_code_idx], data)))
    brands = _get_brands(item_codes)

    make_data = compose(
        list,
        partial(filter, lambda x: x[brand_idx] == filters.brand if filters.brand else True),
        partial(map, lambda x: make_row(x)),
    )

    return make_data(data)


def _get_brands(item_codes):
    data = frappe.get_all(
        "Item", filters=[["item_code", "in", item_codes]], fields=["brand", "item_code"]
    )
    return {x.get("item_code"): x.get("brand") for x in data}
