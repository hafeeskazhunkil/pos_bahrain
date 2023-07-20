# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, flt, add_days
from toolz import merge, pluck


def execute(filters=None):
    filters.day_before_from_date = add_days(filters.from_date, -1)
    columns, data = _get_columns(filters), _get_data(filters)
    return columns, data


def _get_columns(filters):
    return [
        {
            "label": _("DocType"),
            "fieldname": "doctype",
            "fieldtype": "Data",
            "options": "DocType",
            "width": 120,
        },
        {
            "label": _("Asset"),
            "fieldname": "name",
            "fieldtype": "Dynamic Link",
            "options": "doctype",
            "width": 120,
        },
        {
            "label": _("Asset Name"),
            "fieldname": "asset_name",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Cost as on") + " " + formatdate(filters.day_before_from_date),
            "fieldname": "cost_as_on_from_date",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Cost of New Purchase"),
            "fieldname": "cost_of_new_purchase",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Cost of Sold Asset"),
            "fieldname": "cost_of_sold_asset",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Cost of Scrapped Asset"),
            "fieldname": "cost_of_scrapped_asset",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Cost as on") + " " + formatdate(filters.to_date),
            "fieldname": "cost_as_on_to_date",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Accumulated Depreciation as on")
            + " "
            + formatdate(filters.day_before_from_date),
            "fieldname": "accumulated_depreciation_as_on_from_date",
            "fieldtype": "Currency",
            "width": 270,
        },
        {
            "label": _("Depreciation Amount during the period"),
            "fieldname": "depreciation_amount_during_the_period",
            "fieldtype": "Currency",
            "width": 240,
        },
        {
            "label": _("Depreciation Eliminated due to disposal of assets"),
            "fieldname": "depreciation_eliminated_during_the_period",
            "fieldtype": "Currency",
            "width": 300,
        },
        {
            "label": _("Accumulated Depreciation as on")
            + " "
            + formatdate(filters.to_date),
            "fieldname": "accumulated_depreciation_as_on_to_date",
            "fieldtype": "Currency",
            "width": 270,
        },
        {
            "label": _("Net Asset value as on")
            + " "
            + formatdate(filters.day_before_from_date),
            "fieldname": "net_asset_value_as_on_from_date",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Net Asset value as on") + " " + formatdate(filters.to_date),
            "fieldname": "net_asset_value_as_on_to_date",
            "fieldtype": "Currency",
            "width": 200,
        },
    ]


def _get_data(filters):
    data = []
    assets = _get_assets(filters)
    asset_costs = _get_asset_costs(filters)

    for asset_cost in asset_costs:
        row = frappe._dict(asset_cost)

        row.cost_as_on_to_date = (
            flt(row.cost_as_on_from_date)
            + flt(row.cost_of_new_purchase)
            - flt(row.cost_of_sold_asset)
            - flt(row.cost_of_scrapped_asset)
        )

        row.update(
            next(
                asset for asset in assets if asset["name"] == asset_cost.get("name", "")
            )
        )

        row.accumulated_depreciation_as_on_to_date = (
            flt(row.accumulated_depreciation_as_on_from_date)
            + flt(row.depreciation_amount_during_the_period)
            - flt(row.depreciation_eliminated)
        )

        row.net_asset_value_as_on_from_date = flt(row.cost_as_on_from_date) - flt(
            row.accumulated_depreciation_as_on_from_date
        )

        row.net_asset_value_as_on_to_date = flt(row.cost_as_on_to_date) - flt(
            row.accumulated_depreciation_as_on_to_date
        )

        data.append(merge(row, {"doctype": "Asset"}))

    depreciation_gl_entries = _get_depreciation_gl_entries(filters)
    if depreciation_gl_entries:
        data.append({})

    for gl_entry in depreciation_gl_entries:
        accumulated_depreciation_as_on_from_date = 0
        depreciation_amount_during_the_period = gl_entry.get("amount")
        accumulated_depreciation_as_on_to_date = (
            accumulated_depreciation_as_on_from_date
            + depreciation_amount_during_the_period
        )
        data.append(
            {
                "name": gl_entry.get("name"),
                "asset_name": gl_entry.get("account"),
                "cost_as_on_from_date": 0,
                "cost_of_new_purchase": 0,
                "cost_of_sold_asset": 0,
                "cost_of_scrapped_asset": 0,
                "cost_as_on_to_date": 0,
                "accumulated_depreciation_as_on_from_date": accumulated_depreciation_as_on_from_date,
                "depreciation_amount_during_the_period": gl_entry.get("amount"),
                "depreciation_eliminated_during_the_period": 0,
                "accumulated_depreciation_as_on_to_date": accumulated_depreciation_as_on_to_date,
                "net_asset_value_as_on_from_date": 0,
                "net_asset_value_as_on_to_date": 0,
                "doctype": "GL Entry",
            }
        )

    return data


def _get_asset_costs(filters):
    ac_clause = (
        "AND asset_category = %(asset_category)s"
        if filters.get("asset_category")
        else ""
    )
    return frappe.db.sql(
        """
        SELECT 
            asset_name, 
            name,
            IFNULL(
                SUM(
                    CASE 
                        WHEN purchase_date < %(from_date)s 
                        THEN 
                            CASE 
                                WHEN 
                                    IFNULL(disposal_date, 0) = 0 
                                    OR disposal_date >= %(from_date)s 
                                THEN gross_purchase_amount
                                ELSE 0
                            END
                        ELSE 0
                    END
                ),
                0
            ) AS cost_as_on_from_date,
            IFNULL(
                SUM(
                    CASE 
                        WHEN purchase_date >= %(from_date)s 
                        THEN gross_purchase_amount
                        ELSE 0 
                    END
                ),
                0
            ) AS cost_of_new_purchase,
            IFNULL(
                SUM(
                    CASE 
                        WHEN IFNULL(disposal_date, 0) != 0
                        AND disposal_date >= %(from_date)s
                        AND disposal_date <= %(to_date)s 
                        THEN
                            CASE 
                                WHEN status = "Sold" 
                                THEN gross_purchase_amount
                                ELSE 0
                            END
                        ELSE 0
                    END
                ),
                0
            ) as cost_of_sold_asset,
            IFNULL(
                SUM(
                    CASE 
                        WHEN 
                            IFNULL(disposal_date, 0) != 0
                            AND disposal_date >= %(from_date)s
                            AND disposal_date <= %(to_date)s 
                        THEN 
                            CASE 
                                WHEN status = "Scrapped" 
                                THEN gross_purchase_amount
                                ELSE 0
                            END
                        ELSE 0
                    END
                ),
                0
            ) AS cost_of_scrapped_asset
        FROM `tabAsset`
        WHERE docstatus=1 
        AND company=%(company)s 
        AND purchase_date <= %(to_date)s
        {ac_clause}
        GROUP BY name
    """.format(
            ac_clause=ac_clause
        ),
        filters,
        as_dict=1,
    )


def _get_assets(filters):
    # ac_clause = (
    #     "WHERE results.asset_category = %(asset_category)s"
    #     if filters.get("asset_category")
    #     else ""
    # )
    return frappe.db.sql(
        """
            SELECT 
                results.name,
                results.asset_category,
                SUM(results.accumulated_depreciation_as_on_from_date) AS accumulated_depreciation_as_on_from_date,
                SUM(results.depreciation_eliminated_during_the_period) AS depreciation_eliminated_during_the_period,
                SUM(results.depreciation_amount_during_the_period) AS depreciation_amount_during_the_period
            FROM 
            (
                SELECT
                    a.name,
                    a.asset_category,
                    IFNULL(
                        SUM(
                            CASE 
                                WHEN 
                                    ds.schedule_date < %(from_date)s 
                                    AND (ifnull(a.disposal_date, 0) = 0 OR a.disposal_date >= %(from_date)s) 
                                THEN ds.depreciation_amount 
                                ELSE 0
                            END
                        ),
                        0
                    ) as accumulated_depreciation_as_on_from_date,
                    IFNULL(
                        SUM(
                            CASE 
                                WHEN 
                                    ifnull(a.disposal_date, 0) != 0 
                                    AND a.disposal_date >= %(from_date)s
                                    AND a.disposal_date <= %(to_date)s 
                                    AND ds.schedule_date <= a.disposal_date 
                                THEN ds.depreciation_amount
                                ELSE 0 
                            END
                        ), 
                    0) as depreciation_eliminated_during_the_period,
                    IFNULL(
                        SUM(
                            CASE 
                                WHEN 
                                    ds.schedule_date >= %(from_date)s 
                                    AND ds.schedule_date <= %(to_date)s
                                    AND (IFNULL(a.disposal_date, 0) = 0 OR ds.schedule_date <= a.disposal_date) 
                                THEN ds.depreciation_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS depreciation_amount_during_the_period
                FROM 
                    `tabAsset` a,
                    `tabDepreciation Schedule` ds
                WHERE 
                    a.docstatus=1 
                    AND a.company=%(company)s 
                    AND a.purchase_date <= %(to_date)s 
                    AND a.name = ds.parent 
                    AND ifnull(ds.journal_entry, '') != ''
                GROUP BY a.name
                UNION
                SELECT 
                    a.name,
                    a.asset_category,
                    IFNULL(
                        SUM(
                            CASE 
                                WHEN 
                                    IFNULL(a.disposal_date, 0) != 0 
                                    AND (a.disposal_date < %(from_date)s OR a.disposal_date > %(to_date)s) 
                                THEN 0
                                ELSE a.opening_accumulated_depreciation
                            END
                        ),
                        0
                    ) AS accumulated_depreciation_as_on_from_date,
                    IFNULL(
                        SUM(
                            CASE 
                                WHEN 
                                    a.disposal_date >= %(from_date)s 
                                    AND a.disposal_date <= %(to_date)s 
                                    THEN a.opening_accumulated_depreciation
                                ELSE 0
                            END
                        ), 
                        0) AS depreciation_eliminated_during_the_period,
                        0 AS depreciation_amount_during_the_period
                FROM `tabAsset` a
                WHERE
                    a.docstatus=1 
                    AND a.company=%(company)s 
                    AND a.purchase_date <= %(to_date)s
                GROUP BY a.name
            ) AS results
            GROUP BY results.name
            """,
        {
            "to_date": filters.to_date,
            "from_date": filters.from_date,
            "company": filters.company,
        },
        as_dict=1,
    )


def _get_depreciation_gl_entries(filters):
    accounts = frappe.get_all(
        "Asset Category Account",
        filters={"parent": filters.get("asset_category")},
        fields=["accumulated_depreciation_account"],
    )
    return frappe.db.sql(
        """
        SELECT 
            name,
            account,
            credit AS amount
            FROM `tabGL Entry`
        WHERE 
            account IN %(account)s
            AND against_voucher_type IS NULL
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
        {
            "account": list(pluck("accumulated_depreciation_account", accounts)),
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date"),
        },
        as_dict=1,
    )
