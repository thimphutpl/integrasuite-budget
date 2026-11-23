"""Selling Custom Fields, created or updated after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.custom_field import (
    BRANCH_FIELD,
    add_custom_fields,
)

# Company is at the very top of these forms, so Branch goes under Customer instead. Its fieldname is
# the same on all three, so ERPNext copies it along SO -> DN -> SI (and to returns).
SELLING_BRANCH_FIELD = {**BRANCH_FIELD, "insert_after": "customer"}

CUSTOM_FIELDS = {
    "Sales Order": [SELLING_BRANCH_FIELD],
    "Delivery Note": [SELLING_BRANCH_FIELD],
    "Sales Invoice": [SELLING_BRANCH_FIELD],
}


def apply_custom_fields():
    """after_migrate: create the selling Custom Fields above."""
    add_custom_fields(CUSTOM_FIELDS)
