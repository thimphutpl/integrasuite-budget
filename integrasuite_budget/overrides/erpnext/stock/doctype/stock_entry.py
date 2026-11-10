import frappe


def set_cost_center_from_branch(doc, method=None):
    """Book a Stock Entry to its Branch's cost center: the header and every item row.

    The GL entries take the cost center from the item rows, and ERPNext fills those with the
    company default as soon as the form opens, so copying the header into empty rows (what
    PO/PR/PI rely on) never applies here. Runs on validate, so it also covers API and imports.
    """
    if not doc.branch:
        return

    cost_center = frappe.db.get_value("Branch", doc.branch, "cost_center")
    if not cost_center:
        return

    doc.cost_center = cost_center
    for row in doc.items:
        row.cost_center = cost_center
