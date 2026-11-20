"""Generic Custom Field helpers and fields shared by several modules, used by each module's custom_field.py."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Branch on a transaction; its cost center becomes the document's (see utils/branch.js).
BRANCH_FIELD = {
    "fieldname": "branch",
    "label": "Branch",
    "fieldtype": "Link",
    "options": "Branch",
    "reqd": 1,
    "insert_after": "company",
}


def add_custom_fields(custom_fields):
    """Create Custom Fields, given as {doctype: [field, ...]}, or update them to match if they exist."""
    create_custom_fields(custom_fields, update=True)
