import frappe


def set_cost_center_from_branch(doc, method=None):
    """Book a document to its Branch's cost center: the header and every item row.

    validate hook for doctypes whose item rows ERPNext fills with the item / company default cost
    center (Stock Entry, Sales Order). ERPNext only copies the header into empty rows, so those
    rows would never get the branch's one. Running on validate also covers API and imports.
    """
    if not doc.branch:
        return

    cost_center = frappe.db.get_value("Branch", doc.branch, "cost_center")
    if not cost_center:
        return

    doc.cost_center = cost_center
    for row in doc.items:
        row.cost_center = cost_center
