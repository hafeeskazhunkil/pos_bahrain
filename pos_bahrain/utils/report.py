from frappe import _
from toolz import merge


def make_column(key, label=None, type="Data", width=120, **kwargs):
    return merge({
        "label": _(label or key.replace("_", " ").title()),
        "fieldname": key,
        "fieldtype": type,
        "width": width,
    }, kwargs)
