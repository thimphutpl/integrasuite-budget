"""Stock Custom Fields, created or updated after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.custom_field import (
    BRANCH_FIELD,
    add_custom_fields,
)

CUSTOM_FIELDS = {
    # Stock Entry already has a header Cost Center (moved to the Details tab in property_setter.py).
    "Stock Entry": [{**BRANCH_FIELD, "insert_after": "stock_entry_type"}],
}


def apply_custom_fields():
    """after_migrate: create the stock Custom Fields above."""
    add_custom_fields(CUSTOM_FIELDS)
