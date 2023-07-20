import frappe
from frappe.desk.reportview import get_match_cond
from toolz import first
from functools import partial


def get_batch_no(doctype, txt, searchfield, start, page_len, filters):
    batch_nos = frappe.db.sql(
        """
        SELECT 
            batch.name,
            CONCAT('MFG-', batch.manufacturing_date),
            CONCAT('EXP-', batch.expiry_date)
        FROM `tabBatch` batch
        WHERE
            batch.name LIKE %(txt)s
            AND batch.disabled = 0
            AND batch.docstatus < 2
            AND batch.item = %(item_code)s
            AND (batch.expiry_date IS NULL OR batch.expiry_date >= %(posting_date)s)
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "item_code": filters.get("item_code"),
            "posting_date": filters.get("posting_date"),
            "txt": "%{0}%".format(txt),
            "start": start,
            "page_len": page_len,
        },
    )

    return _add_actual_qty(filters.get("warehouse"), batch_nos)


def _add_actual_qty(warehouse, batch_nos):
    def make_data(meta, row):
        name = row[0]
        actual_qty = meta.get(name, 0)
        return tuple([name, str(actual_qty), *row[1:]])

    batches = list(map(lambda x: first(x), batch_nos))
    sl_entries = frappe.db.sql(
        """
        SELECT 
            sle.batch_no,
            ROUND(SUM(sle.actual_qty), 2)
        FROM `tabStock Ledger Entry` sle
        WHERE 
            sle.batch_no IN %(batches)s
            AND sle.warehouse = %(warehouse)s
        GROUP BY sle.batch_no
        """,
        {"batches": batches, "warehouse": warehouse},
    )
    batches_actual_qty = {x[0]: x[1] for x in sl_entries}
    data = partial(make_data, batches_actual_qty)
    return [data(x) for x in batch_nos]
