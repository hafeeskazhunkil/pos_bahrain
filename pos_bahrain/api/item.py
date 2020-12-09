# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _


def _groupby(key, list_of_dicts):
    from itertools import groupby
    from operator import itemgetter

    keywise = {}
    for k, v in groupby(
        sorted(list_of_dicts, key=itemgetter(key)),
        itemgetter(key),
    ):
        keywise[k] = list(v)
    return keywise


@frappe.whitelist()
def get_more_pos_data(profile, company):
    pos_profile = frappe.get_doc('POS Profile', profile)
    if not pos_profile:
        return frappe.throw(
            _('POS Profile: {} is not valid.'.format(profile))
        )
    warehouse = pos_profile.warehouse or frappe.db.get_value(
        'Company', pos_profile.company, 'default_warehouse',
    )
    if not warehouse:
        return frappe.throw(
            _(
                'No valid Warehouse found. Please select warehouse in '
                'POS Profile.'
            )
        )
    return {
        'batch_no_details': get_batch_no_details(warehouse),
        'uom_details': get_uom_details(),
        'exchange_rates': get_exchange_rates(),
    }


def get_batch_no_details(warehouse):
    batches = frappe.db.sql(
        """
            SELECT
                name,
                item,
                expiry_date,
                (
                    SELECT SUM(actual_qty)
                    FROM `tabStock Ledger Entry`
                    WHERE batch_no=b.name AND
                        item_code=b.item AND
                        warehouse=%(warehouse)s
                ) as qty
            FROM `tabBatch` AS b
            WHERE IFNULL(expiry_date, '4000-10-10') >= CURDATE()
            ORDER BY expiry_date
        """,
        values={'warehouse': warehouse},
        as_dict=1,
    )
    return _groupby(
        'item',
        filter(lambda x: x.get('qty'), batches)
    )


def get_uom_details():
    uoms = frappe.db.sql(
        """
            SELECT
                parent AS item_code,
                uom,
                conversion_factor
            FROM `tabUOM Conversion Detail`
        """,
        as_dict=1
    )
    return _groupby('item_code', uoms)


def _merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_exchange_rates():
    from erpnext.setup.utils import get_exchange_rate
    mops = frappe.db.sql(
        """
            SELECT
                name AS mode_of_payment,
                alt_currency AS currency
            FROM `tabMode of Payment`
            WHERE in_alt_currency=1
        """,
        as_dict=1
    )
    return {mop.mode_of_payment: mop for mop in map(lambda x: _merge_dicts(
        x,
        {
            'conversion_rate': get_exchange_rate(
                x.currency,
                frappe.defaults.get_user_default('currency'),
            ),
        }
    ), mops)}
