# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from functools import partial
from toolz import concatv, compose, groupby, valmap, itemmap


def execute(filters=None):
	from erpnext.stock.report.stock_balance.stock_balance import execute
	columns, data = execute(filters)
	return _get_columns(columns), _get_data(data)


def _get_columns(columns):
	return list(
		concatv(
			[columns[2]],
			columns[7:15],
			[
				{
					"fieldname": "per_value",
					"fieldtype": "Percent",
					"width": 100,
					"label": "% Value",
				},
			]
		)
	)


def _get_data(data):
	def add_fields(row):
		return list(
			concatv(
				[row[2]],
				row[7:15]
			)
		)

	def sum_data(row):
		row_data = list(map(lambda x: x[1:], row))
		return [sum(x) for x in zip(*row_data)]

	data_by_item_groups = compose(
		partial(valmap, sum_data),
		partial(groupby, lambda x: x[0]),
		partial(map, add_fields)
	)

	merged_data = _merge_kv(data_by_item_groups(data))
	total_value = sum(list(map(lambda x: x[8], merged_data)))
	merged_data_with_per = list(
		map(lambda x: list(concatv(x, [(x[8] / total_value) * 100])), merged_data)
	)

	return sorted(
		merged_data_with_per, 
		key=lambda x: x[0]
	)


def _merge_kv(data):
	res = []
	for key, value in data.items():
		res.append(list(concatv([key], value)))
	return res
