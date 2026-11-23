"""Selling changes to ERPNext's standard fields, applied after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.property_setter import (
    hide_company_fields,
    hide_fields,
    make_fields_read_only,
)

# Fields we hide, as (doctype, fieldname). Hiding a Tab/Section Break hides everything in it.
HIDDEN_FIELDS = [
    ("Sales Order", "contact_info"),  # Address & Contact tab
    ("Sales Order", "utm_analytics_section"),  # More Info > UTM Analytics
    # More Info tab: only Status is kept
    ("Sales Order", "sales_team_section_break"),  # Commission
    ("Sales Order", "section_break1"),  # Sales Team
    ("Sales Order", "auto_repeat_section"),
    ("Sales Order", "printing_details"),  # Print Settings
    ("Sales Order", "additional_info_section"),
    ("Sales Order", "tax_category"),
    ("Sales Order", "shipping_rule"),
    ("Sales Order", "incoterm"),  # Named Place depends on Incoterm, so it stays hidden too
    ("Delivery Note", "address_and_contact_tab"),  # Address & Contact tab
    ("Sales Invoice", "contact_and_address_tab"),  # Address & Contact tab (named the other way round)
    ("Delivery Note", "tax_category"),
    ("Delivery Note", "shipping_rule"),
    ("Delivery Note", "incoterm"),
    ("Sales Invoice", "tax_category"),
    ("Sales Invoice", "shipping_rule"),
    ("Sales Invoice", "incoterm"),
    # Accounting Dimensions section: only Cost Center (from the Branch) is kept
    ("Sales Order", "project"),
    ("Delivery Note", "project"),
    ("Sales Invoice", "project"),
]

# Single-company site, see the Company note in buying/property_setter.py.
COMPANY_HIDDEN_DOCTYPES = ["Sales Order", "Delivery Note", "Sales Invoice"]

# The header Cost Center is filled from the Branch (see utils/branch.js), so users cannot edit it.
READ_ONLY_FIELDS = [
    ("Sales Order", "cost_center"),
    ("Delivery Note", "cost_center"),
    ("Sales Invoice", "cost_center"),
]


def apply_property_setters():
    """after_migrate: apply the selling field changes above."""
    hide_fields(HIDDEN_FIELDS)
    hide_company_fields(COMPANY_HIDDEN_DOCTYPES)
    make_fields_read_only(READ_ONLY_FIELDS)
