"""Selling Custom Fields, created or updated after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.custom_field import (
    BRANCH_FIELD,
    add_custom_fields,
)

CUSTOM_FIELDS = {
    # Sales Order shows Company at the very top, so Branch goes under Customer instead.
    "Sales Order": [{**BRANCH_FIELD, "insert_after": "customer"}],
}


def apply_custom_fields():
    """after_migrate: create the selling Custom Fields above."""
    add_custom_fields(CUSTOM_FIELDS)
