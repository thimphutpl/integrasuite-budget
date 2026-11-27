"""Generic Custom Field helpers and fields shared by several modules, used by each module's custom_field.py."""

import frappe
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
    """Create Custom Fields, given as {doctype: [field, ...]}, or update them to match if they exist.

    A field the doctype already has as a standard field (some ERPNext versions ship it) is used
    as is instead, since a Custom Field with the same name can't be created.
    """
    create_custom_fields(
        {doctype: _without_standard_fields(doctype, fields) for doctype, fields in custom_fields.items()},
        update=True,
    )


def _without_standard_fields(doctype, fields):
    meta = frappe.get_meta(doctype)
    result = []
    for field in fields:
        standard = meta.get_field(field["fieldname"])
        if not standard or getattr(standard, "is_custom_field", False):
            result.append(field)
        elif standard.fieldtype != field["fieldtype"]:
            frappe.throw(
                f"{doctype} already has a standard field {field['fieldname']} of type "
                f"{standard.fieldtype}, but integrasuite_budget needs it as {field['fieldtype']}"
            )
    return result
