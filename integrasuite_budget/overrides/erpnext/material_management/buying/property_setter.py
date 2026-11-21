"""Buying (MR -> PO -> PR -> PI) changes to ERPNext's standard fields, applied after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.property_setter import (
    hide_company_fields,
    hide_fields,
    make_fields_read_only,
    make_fields_required,
    make_fields_required_when,
    set_field_properties,
)

# Fields we hide, as (doctype, fieldname). Hiding a Tab Break hides the whole tab.
HIDDEN_FIELDS = [
    ("Purchase Order", "address_and_contact_tab"),
    ("Purchase Receipt", "address_and_contact_tab"),
    ("Purchase Invoice", "address_and_contact_tab"),
    ("Purchase Order", "project"),
    ("Purchase Receipt", "project"),
    ("Purchase Invoice", "project"),
    ("Purchase Invoice", "tax_category"),
    ("Purchase Invoice", "shipping_rule"),
    ("Purchase Invoice", "incoterm"),
    ("Buying Settings", "allow_negative_rates_for_items"),
]

# Single-company site: ERPNext hides Company itself (erpnext.hide_company), but only after the
# form is drawn, so it blinked and Branch (inserted after it) jumped. Hiding it in the meta
# avoids that; hide_company_fields also gives it the default company as its default, which Frappe
# requires for a hidden mandatory field. If a second company is added, remove these AND delete
# their Property Setters (also Stock Entry's in stock/property_setter.py).
COMPANY_HIDDEN_DOCTYPES = ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"]

# The header Cost Center is filled from the Branch (see utils/branch.js), so users cannot edit it.
# MR's header Cost Center is our own Custom Field and is made read-only there instead.
READ_ONLY_FIELDS = [
    ("Purchase Order", "cost_center"),
    ("Purchase Receipt", "cost_center"),
    ("Purchase Invoice", "cost_center"),
]

# Fields we make mandatory, as (doctype, fieldname).
REQUIRED_FIELDS = [
    # Header Required By; ERPNext only requires it per item, and copies the header date to new rows
    ("Material Request", "schedule_date"),
    ("Purchase Order", "set_warehouse"),
    ("Purchase Receipt", "set_warehouse"),
    # Copied to the Purchase Invoice's Supplier Invoice No (bill_no), see supplier_invoice_no.py
    ("Purchase Receipt", "supplier_delivery_note"),
]

# Fields mandatory only under a condition, as (doctype, fieldname, condition).
# PI's Set Warehouse is only shown when Update Stock is ticked, so it can't always be required.
CONDITIONALLY_REQUIRED_FIELDS = [
    ("Purchase Invoice", "set_warehouse", "eval:doc.update_stock"),
]

# Other field properties, as (doctype, fieldname, property, value, property_type).
FIELD_PROPERTIES = [
    # Liquidated Damages reuse ERPNext's Write Off section (see liquidated_damages.py)
    ("Purchase Invoice", "write_off", "label", "Write Off / Liquidity Damages", "Data"),
    ("Purchase Invoice", "write_off", "collapsible", "1", "Check"),
    ("Purchase Invoice", "write_off_amount", "label", "Write Off / LD Amount", "Data"),
    ("Purchase Invoice", "write_off_cost_center", "fetch_from", "branch.cost_center", "Small Text"),
    ("Purchase Receipt", "supplier_delivery_note", "label", "Supplier Invoice No", "Data"),
]


def apply_property_setters():
    """after_migrate: apply the buying field changes above."""
    hide_fields(HIDDEN_FIELDS)
    hide_company_fields(COMPANY_HIDDEN_DOCTYPES)
    make_fields_read_only(READ_ONLY_FIELDS)
    make_fields_required(REQUIRED_FIELDS)
    make_fields_required_when(CONDITIONALLY_REQUIRED_FIELDS)
    set_field_properties(FIELD_PROPERTIES)
