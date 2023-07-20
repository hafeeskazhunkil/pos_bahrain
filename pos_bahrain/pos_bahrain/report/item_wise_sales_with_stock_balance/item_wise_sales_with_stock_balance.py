# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from pos_bahrain.pos_bahrain.report.item_wise_sales_register_with_employee.item_wise_sales_register_with_employee import (
	execute as item_wise_sales_register_with_employee
)

from toolz import compose, concatv, first, merge
from toolz.curried import groupby, valmap


def execute(filters=None):
	columns, data = item_wise_sales_register_with_employee(filters)
	item_idx = next(x for x, v in enumerate(columns) if 'Item Code' in v)
	return _extend_columns(columns), _extend_data(data, filters, item_idx)


def _extend_columns(columns):
	return columns + ['Balance Qty:Float:90', 'Valuation Rate:Float:120', 'Total Valuation Rate:Float:120']


def _get_clauses(filters):
	return ' AND '.join(
		concatv(
			['item_code IN %(items)s'],
			['warehouse = %(warehouse)s'] if filters.warehouse else []
		)
	)


def _extend_data(data, filters, item_idx):
	items = list(set(map(lambda x: x[item_idx], data)))
	balance_qty = _get_balance_qty(items, filters)
	valuation_rate = _get_valuation_rate(items)
	set_valuation_rate = compose(
		list,
		lambda x: concatv(
			x,
			[
				balance_qty.get(x[item_idx], 0.0),
				valuation_rate.get(x[item_idx], 0.0),
				balance_qty.get(x[item_idx], 0.00) * valuation_rate.get(x[item_idx], 0.00)
			]
		)
	)
	return [set_valuation_rate(x) for x in data]


def _get_balance_qty(items, filters):
	clauses = _get_clauses(filters)
	return compose(
		valmap(lambda x: x['qty']),
		valmap(first),
		groupby('item_code'),
		lambda: frappe.db.sql(
			"""
				SELECT
					item_code,
					SUM(actual_qty) as qty
				FROM `tabBin`
				WHERE {clauses}
				GROUP BY item_code
			""".format(clauses=clauses),
			values=merge(filters, {'items': items}),
			as_dict=1
		)
	)()


def _get_valuation_rate(items):
	return compose(
		valmap(lambda x: x['valuation_rate']),
		valmap(first),
		groupby('name'),
		lambda: frappe.get_all(
			'Item',
			filters=[['name', 'in', items]],
			fields=['name', 'valuation_rate']
		)
	)()
