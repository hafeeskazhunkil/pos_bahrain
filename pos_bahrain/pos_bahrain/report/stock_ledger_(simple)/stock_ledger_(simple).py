# Copyright (c) 2019, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from functools import partial
from erpnext.stock.report.stock_ledger.stock_ledger import execute as stock_ledger
from toolz import compose, unique, pluck, groupby, valmap, first, merge

from pos_bahrain.utils import pick

_fields = [
    "date",
    "item_code",
    "item_name",
    "brand",
    "default_supplier",
    "stock_uom",
    "actual_qty",
    "qty_after_transaction",
    "incoming_rate",
    "valuation_rate",
    "stock_value",
    "voucher_type",
    "voucher_no",
    "batch_no",
]


def execute(filters=None):
    columns, data = stock_ledger(filters)
    return _get_columns(columns), _get_data(data, filters)


_get_columns = compose(
    list,
    partial(filter, lambda x: x.get("fieldname") in _fields),
    lambda x: x[:5]
    + [
        {
            "label": _("Default Supplier"),
            "fieldname": "default_supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 100,
        }
    ]
    + x[5:],
)


def _get_data(data, filters):
    item_codes = compose(list, unique, partial(pluck, "item_code"))(data)
    if not item_codes:
        return data
    query = frappe.db.sql(
        """
            SELECT
                i.item_code AS item_code,
                id.default_supplier AS default_supplier
            FROM `tabItem` AS i
            LEFT JOIN `tabItem Default` AS id ON i.name = id.parent
            WHERE i.item_code IN %(item_codes)s
                AND id.company = %(company)s
        """,
        values={"item_codes": item_codes, "company": filters.company},
        as_dict=1,
    )

    suppliers_map = compose(
        partial(valmap, lambda x: x.get("default_supplier")),
        partial(valmap, first),
        partial(groupby, "item_code"),
    )(query)

    make_row = compose(
        partial(pick, _fields),
        lambda x: merge(x, {"default_supplier": suppliers_map.get(x.get("item_code"))}),
    )

    def filter_by_supplier(item):
        if not filters.default_supplier:
            return True
        return item.get("default_supplier") == filters.default_supplier

    make_data = compose(
        list, partial(filter, filter_by_supplier), partial(map, make_row)
    )
    return make_data(data)
