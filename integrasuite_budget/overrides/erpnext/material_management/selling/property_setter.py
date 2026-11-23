"""Selling changes to ERPNext's standard fields, applied after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.property_setter import hide_fields

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
]


def apply_property_setters():
    """after_migrate: apply the selling field changes above."""
    hide_fields(HIDDEN_FIELDS)
