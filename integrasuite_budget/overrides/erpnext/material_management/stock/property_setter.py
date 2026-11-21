"""Stock changes to ERPNext's standard fields, applied after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.property_setter import (
    hide_company_fields,
    hide_fields,
    make_fields_read_only,
    move_fields_before,
    set_field_properties,
)

# Fields we hide, as (doctype, fieldname).
HIDDEN_FIELDS = [
    ("Stock Entry", "project"),
    ("Item", "allow_negative_stock"),
    ("Stock Settings", "allow_negative_stock"),
]

# Single-company site, see the Company note in buying/property_setter.py.
COMPANY_HIDDEN_DOCTYPES = ["Stock Entry"]

# The header Cost Center is filled from the Branch (see utils/branch.js), so users cannot edit it.
READ_ONLY_FIELDS = [
    ("Stock Entry", "cost_center"),
]

# Other field properties, as (doctype, fieldname, property, value, property_type).
FIELD_PROPERTIES = [
    # Stock Entry's Accounting Dimensions is a tab; it becomes a collapsible section like on PO,
    # and SE_ACCOUNTING_DIMENSION_FIELDS below puts it on the Details tab.
    ("Stock Entry", "accounting_dimensions_section", "fieldtype", "Section Break", "Select"),
    ("Stock Entry", "accounting_dimensions_section", "collapsible", "1", "Check"),
]

# Stock Entry: the Accounting Dimensions fields, moved to just before this field on the Details tab
# (after Posting Date/Time, before Inspection Required).
# Cost Center goes before the column break so it sits in the left column (Project is hidden).
SE_ACCOUNTING_DIMENSION_FIELDS = ["accounting_dimensions_section", "project", "cost_center", "dimension_col_break"]
SE_ACCOUNTING_DIMENSIONS_BEFORE = "reference_section"


def apply_property_setters():
    """after_migrate: apply the stock field changes above."""
    hide_fields(HIDDEN_FIELDS)
    hide_company_fields(COMPANY_HIDDEN_DOCTYPES)
    make_fields_read_only(READ_ONLY_FIELDS)
    set_field_properties(FIELD_PROPERTIES)
    move_fields_before("Stock Entry", SE_ACCOUNTING_DIMENSION_FIELDS, SE_ACCOUNTING_DIMENSIONS_BEFORE)
