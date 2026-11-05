from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

BRANCH_FIELD = {
    "fieldname": "branch",
    "label": "Branch",
    "fieldtype": "Link",
    "options": "Branch",
    "reqd": 1,
    "insert_after": "company",
}

# PO, PR and PI already have a header Cost Center; MR gets the same field so it maps across.
MR_COST_CENTER_FIELD = {
    "fieldname": "cost_center",
    "label": "Cost Center",
    "fieldtype": "Link",
    "options": "Cost Center",
    "read_only": 1,
    "insert_after": "branch",
}

CUSTOM_FIELDS = {
    "Material Request": [BRANCH_FIELD, MR_COST_CENTER_FIELD],
    "Purchase Order": [BRANCH_FIELD],
    "Purchase Receipt": [BRANCH_FIELD],
    "Purchase Invoice": [BRANCH_FIELD],
}


def add_custom_fields():
    """Create the Custom Fields above, or update them to match if they already exist."""
    create_custom_fields(CUSTOM_FIELDS, update=True)
