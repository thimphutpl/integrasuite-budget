import frappe


def set_cost_center_from_branch(doc, method=None):
    """Book a document to its Branch's cost center: the header, every item row and every tax row.

    validate hook for every doctype with a Branch (MR -> PO -> PR -> PI, Stock Entry, SO -> DN -> SI).
    ERPNext fills each item row with the item / company default cost center as soon as an item is
    picked, and only copies the header into empty rows, so the rows would never get the branch's
    one. The GL entries are booked from the rows. Running on validate also covers API and imports.
    Already submitted documents are not touched: validate does not run on cancel or update after submit.

    Tax rows come from a Taxes and Charges Template with the template's own cost center (company
    default), and their GL entries are booked from it, so they follow the branch too.
    """
    if not doc.branch:
        return

    cost_center = frappe.db.get_value("Branch", doc.branch, "cost_center")
    if not cost_center:
        return

    doc.cost_center = cost_center
    for row in [*doc.items, *(doc.get("taxes") or [])]:
        row.cost_center = cost_center
