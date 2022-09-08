from .sales_invoice import set_location


def before_save(doc, method):
    set_location(doc)
