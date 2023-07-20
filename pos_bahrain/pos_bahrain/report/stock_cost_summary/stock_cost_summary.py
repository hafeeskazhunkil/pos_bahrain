# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from functools import partial
from toolz import pluck, compose, concatv, groupby, first, valmap
from pos_bahrain.utils.report import make_column


def execute(filters=None):
    from erpnext.stock.report.stock_balance.stock_balance import execute

    columns, data = execute(filters)
    return _get_rearranged_data(_get_columns(columns), _get_data(data, columns))


def _get_rearranged_data(columns, data):
    column_fieldnames = list(pluck("fieldname", columns))

    def get_column_data(column_name, row):
        column_data = column_fieldnames.index(column_name)
        return row[column_data]

    def get_arrangement(rows):
        return [
            get_column_data("parent_item_group", rows),
            get_column_data("item_group", rows),
            get_column_data("sku_counts", rows),
            get_column_data("bal_val", rows),
            get_column_data("ret_val", rows),
        ]

    rearranged_data = compose(
        list,
        partial(map, get_arrangement),
    )

    return get_arrangement(columns), rearranged_data(data)


def _get_columns(columns):
    return list(
        concatv(
            columns,
            [
                make_column(
                    "parent_item_group",
                    "Parent Item Group",
                    "Link",
                    options="Item Group",
                ),
                make_column("ret_val", "Retail", "Currency"),
                make_column("sku_counts", "SKU Counts", "Float"),
            ],
        )
    )


def _get_data(data, columns):
    column_fieldnames = list(pluck("fieldname", columns))

    def get_column_data(column_name, row):
        column_data = column_fieldnames.index(column_name)
        return row[column_data]

    def get_distinct_data(column_name):
        return compose(
            list, set, partial(map, partial(get_column_data, column_name)), lambda: data
        )()

    def get_merged_data(rows):
        parent_item_groups = _get_parent_item_groups(get_distinct_data("item_group"))
        item_selling_prices = _get_item_selling_prices(get_distinct_data("item_code"))
        return compose(
            list,
            partial(
                map,
                lambda x: list(
                    concatv(
                        x,
                        [
                            parent_item_groups.get(get_column_data("item_group", x)),
                            item_selling_prices.get(
                                get_column_data("item_code", x), 0.00
                            )
                            * get_column_data("bal_qty", x),
                            1.0,  # for number of sku
                        ],
                    )
                ),
            ),
            lambda: rows,
        )()

    data_by_item_group = compose(
        partial(
            valmap,
            lambda x: [
                sum(z) if isinstance(first(z), float) else first(z) for z in zip(*x)
            ],
        ),
        partial(groupby, lambda x: x[2]),  # index 2 is item group
    )

    return compose(list, lambda x: x.values(), data_by_item_group, get_merged_data)(
        data
    )


def _get_parent_item_groups(item_groups):
    data = frappe.db.get_all(
        "Item Group",
        filters=[["name", "in", item_groups]],
        fields=["name", "parent_item_group"],
    )
    return {x.get("name"): x.get("parent_item_group") for x in data}


def _get_item_selling_prices(items):
    price_list = "Standard Selling"
    data = frappe.db.get_all(
        "Item Price",
        filters=[["item_code", "in", items], ["price_list", "=", price_list]],
        fields=["item_code", "price_list_rate"],
    )
    return {x.get("item_code"): x.get("price_list_rate") for x in data}
