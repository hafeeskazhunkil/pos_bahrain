# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from functools import partial
from toolz import compose, pluck, merge, concatv

from pos_bahrain.utils import pick
from pos_bahrain.utils.report import make_column


def execute(filters=None):
    columns = _get_columns(filters)
    keys = compose(list, partial(pluck, "fieldname"))(columns)
    clauses, values = _get_filters(filters)
    data = _get_data(clauses, values, keys)
    return columns, data


def _get_columns(filters):
    join_columns = compose(list, concatv)
    return join_columns(
        [
            make_column("posting_date", "Date", type="Date", width=90),
            make_column("voucher_type", hidden=1),
            make_column(
                "voucher_no",
                "Bill No",
                type="Dynamic Link",
                options="voucher_type",
                width=150,
            ),
            make_column("particulars"),
            make_column("expiry_date", type="Date", width=90),
            make_column("receipt", type="Float", width=90),
            make_column("issue", type="Float", width=90),
        ],
    )


def _get_filters(filters):
    clauses = concatv(
        ["sle.posting_date BETWEEN %(from_date)s AND %(to_date)s"],
        ["sle.item_code = %(item_code)s"],
        ["sle.warehouse = %(warehouse)s"] if filters.warehouse else [],
    )
    values = merge(
        pick(["item_code", "price_list", "warehouse"], filters),
        {"from_date": filters.date_range[0], "to_date": filters.date_range[1]},
    )
    return (
        {"clauses": " AND ".join(clauses)},
        values,
    )


def _get_data(clauses, values, keys):
    result = frappe.db.sql(
        """
            SELECT
                sle.posting_date AS posting_date,
                sle.voucher_type AS voucher_type,
                sle.voucher_no AS voucher_no,
                sle.actual_qty AS qty,
                b.expiry_date AS expiry_date
            FROM `tabStock Ledger Entry` AS sle
            LEFT JOIN `tabItem` AS i ON i.name = sle.item_code
            LEFT JOIN `tabBatch` AS b ON b.name = sle.batch_no
            WHERE {clauses}
            ORDER BY sle.posting_date
        """.format(
            **clauses
        ),
        values=values,
        as_dict=1,
    )

    def set_particalurs_and_qtys(row):
        voucher_type = row.get("voucher_type")
        qty = row.get("qty")
        if voucher_type in ["Sales Invoice", "Delivery Note"]:
            return merge(row, {"particulars": "Sales", "receipt": None, "issue": -qty})
        if voucher_type in ["Purchase Invoice", "Purchase Receipt"]:
            return merge(
                row,
                {
                    "particulars": "Purchase",
                    "receipt": qty if qty > 0 else None,
                    "issue": -qty if qty < 0 else None,
                },
            )
        if voucher_type in ["Stock Entry", "Stock Reconciliation"]:
            return merge(
                row, {"particulars": "Adjustment", "receipt": qty, "issue": None}
            )
        return row

    make_row = compose(partial(pick, keys), set_particalurs_and_qtys)
    return [make_row(x) for x in result]
