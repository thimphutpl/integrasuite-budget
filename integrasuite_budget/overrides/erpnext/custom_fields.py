from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

BRANCH_FIELD = {
    "fieldname": "branch",
    "label": "Branch",
    "fieldtype": "Link",
    "options": "Branch",
    "reqd": 1,
    "insert_after": "company",
}

CUSTOM_FIELDS = {
    "Material Request": [BRANCH_FIELD],
    "Purchase Order": [BRANCH_FIELD],
    "Purchase Receipt": [BRANCH_FIELD],
    "Purchase Invoice": [BRANCH_FIELD],
}


def add_custom_fields():
    """Create the Custom Fields above, or update them to match if they already exist."""
    create_custom_fields(CUSTOM_FIELDS, update=True)
