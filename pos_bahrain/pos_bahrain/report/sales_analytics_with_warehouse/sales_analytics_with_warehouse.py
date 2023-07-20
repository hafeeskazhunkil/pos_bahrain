# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.selling.report.sales_analytics.sales_analytics import Analytics


def execute(filters=None):
    return AnalyticsExtended(filters).run()


class AnalyticsExtended(Analytics):
    def get_sales_transactions_based_on_customers_or_suppliers(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total as value_field"
        else:
            value_field = "total_qty as value_field"

        if self.filters.tree_type == "Customer":
            entity = "customer as entity"
            entity_name = "customer_name as entity_name"
        else:
            entity = "supplier as entity"
            entity_name = "supplier_name as entity_name"

        def get_data(filters):
            return frappe.get_all(
                self.filters.doc_type,
                fields=["name", entity, entity_name, value_field, self.date_field],
                filters=filters,
            )

        self.entries = get_data(
            {
                "docstatus": 1,
                "company": self.filters.company,
                self.date_field: (
                    "between",
                    [self.filters.from_date, self.filters.to_date],
                ),
                "set_warehouse": self.filters.warehouse,
            }
        )

        if self.filters.warehouse:
            entries_by_pos = get_data(
                {
                    "docstatus": 1,
                    "company": self.filters.company,
                    self.date_field: (
                        "between",
                        [self.filters.from_date, self.filters.to_date],
                    ),
                    "set_warehouse": "",
                    "pos_profile": (
                        "in",
                        _get_pos_profiles_by_warehouse(self.filters.warehouse),
                    ),
                }
            )
            self.entries = self.entries + entries_by_pos

        self.entity_names = {}
        for d in self.entries:
            self.entity_names.setdefault(d.entity, d.entity_name)

    def get_sales_transactions_based_on_items(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_amount"
        else:
            value_field = "stock_qty"

        def get_data(query, filters):
            return frappe.db.sql(
                """
                    SELECT 
                        i.item_code AS entity,
                        i.item_name AS entity_name,
                        i.stock_uom, 
                        i.{value_field} AS value_field, 
                        s.{date_field}
                    FROM `tab{doctype} Item` i , `tab{doctype}` s
                    WHERE s.name = i.parent
                    AND i.docstatus = 1 
                    AND s.company = %(company)s
                    AND s.{date_field} BETWEEN %(from_date)s AND %(to_date)s
                    {query}
                """.format(
                    date_field=self.date_field,
                    value_field=value_field,
                    doctype=self.filters.doc_type,
                    query=query,
                ),
                filters,
                as_dict=1,
            )

        self.entries = get_data(
            ("AND s.set_warehouse = %(warehouse)s" if self.filters.warehouse else ""),
            self.filters,
        )

        if self.filters.warehouse:
            clauses = [
                "AND (s.set_warehouse IS NULL OR s.set_warehouse = '')",  # don't forget AND for the first clause
                "s.pos_profile IN %(pos_profiles)s",
            ]
            entries_by_pos = get_data(
                " AND ".join(clauses),
                {
                    **self.filters,
                    "pos_profiles": _get_pos_profiles_by_warehouse(
                        self.filters.warehouse
                    ),
                },
            )
            self.entries = self.entries + entries_by_pos

        self.entity_names = {}
        for d in self.entries:
            self.entity_names.setdefault(d.entity, d.entity_name)

    def get_sales_transactions_based_on_item_group(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_amount"
        else:
            value_field = "qty"

        def get_data(query, filters):
            return frappe.db.sql(
                """
                    SELECT 
                        i.item_group AS entity, 
                        i.{value_field} AS value_field, 
                        s.{date_field}
                    FROM `tab{doctype} Item` i , `tab{doctype}` s
                    WHERE s.name = i.parent
                    AND i.docstatus = 1 
                    AND s.company = %(company)s
                    AND s.{date_field} between %(from_date)s and %(to_date)s
                    {query}
                """.format(
                    date_field=self.date_field,
                    value_field=value_field,
                    doctype=self.filters.doc_type,
                    query=query,
                ),
                filters,
                as_dict=1,
            )

        self.entries = get_data(
            ("AND s.set_warehouse = %(warehouse)s" if self.filters.warehouse else ""),
            self.filters,
        )

        if self.filters.warehouse:
            clauses = [
                "AND (s.set_warehouse IS NULL OR s.set_warehouse = '')",  # don't forget AND for the first clause
                "s.pos_profile IN %(pos_profiles)s",
            ]
            entries_by_pos = get_data(
                " AND ".join(clauses),
                {
                    **self.filters,
                    "pos_profiles": _get_pos_profiles_by_warehouse(
                        self.filters.warehouse
                    ),
                },
            )
            self.entries = self.entries + entries_by_pos

        self.get_groups()

    def get_sales_transactions_based_on_customer_or_territory_group(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total as value_field"
        else:
            value_field = "total_qty as value_field"

        if self.filters.tree_type == "Customer Group":
            entity_field = "customer_group as entity"
        elif self.filters.tree_type == "Supplier Group":
            entity_field = "supplier as entity"
            self.get_supplier_parent_child_map()
        else:
            entity_field = "territory as entity"

        def get_data(filters):
            return frappe.get_all(
                self.filters.doc_type,
                fields=[entity_field, value_field, self.date_field],
                filters=filters,
            )

        self.entries = get_data(
            {
                "docstatus": 1,
                "company": self.filters.company,
                self.date_field: (
                    "between",
                    [self.filters.from_date, self.filters.to_date],
                ),
                "set_warehouse": self.filters.warehouse,
            }
        )

        if self.filters.warehouse:
            entries_by_pos = get_data(
                {
                    "docstatus": 1,
                    "company": self.filters.company,
                    self.date_field: (
                        "between",
                        [self.filters.from_date, self.filters.to_date],
                    ),
                    "set_warehouse": "",
                    "pos_profile": (
                        "in",
                        _get_pos_profiles_by_warehouse(self.filters.warehouse),
                    ),
                }
            )
            self.entries = self.entries + entries_by_pos

        self.get_groups()


def _get_pos_profiles_by_warehouse(warehouse):
    return [
        x.get("name")
        for x in frappe.get_all("POS Profile", filters={"warehouse": warehouse})
    ]
