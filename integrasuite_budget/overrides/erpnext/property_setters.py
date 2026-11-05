import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# ERPNext fields we hide, as (doctype, fieldname). Hiding a Tab Break hides the whole tab.
HIDDEN_FIELDS = [
    ("Purchase Order", "address_and_contact_tab"),
    ("Purchase Receipt", "address_and_contact_tab"),
    ("Purchase Invoice", "address_and_contact_tab"),
    ("Purchase Order", "project"),
    ("Purchase Receipt", "project"),
    ("Purchase Invoice", "project"),
    ("Item", "allow_negative_stock"),
    ("Stock Settings", "allow_negative_stock"),
    ("Buying Settings", "allow_negative_rates_for_items"),
]


def hide_fields():
    """Hide the fields above with Property Setters.

    ERPNext's DocType JSON is reloaded on every migrate, so the change lives in a
    Property Setter instead, which is applied on top of it.
    """
    for doctype, fieldname in HIDDEN_FIELDS:
        filters = {"doc_type": doctype, "field_name": fieldname, "property": "hidden"}
        if frappe.db.get_value("Property Setter", filters, "value") == "1":
            continue

        make_property_setter(doctype, fieldname, "hidden", 1, "Check")


# The header Cost Center is filled from the Branch (see js/branch.js), so users cannot edit it.
# MR's header Cost Center is our own Custom Field and is made read-only there instead.
READ_ONLY_FIELDS = [
    ("Purchase Order", "cost_center"),
    ("Purchase Receipt", "cost_center"),
    ("Purchase Invoice", "cost_center"),
]


def make_fields_read_only():
    """Make the fields above read-only with Property Setters, like hide_fields."""
    for doctype, fieldname in READ_ONLY_FIELDS:
        filters = {"doc_type": doctype, "field_name": fieldname, "property": "read_only"}
        if frappe.db.get_value("Property Setter", filters, "value") == "1":
            continue

        make_property_setter(doctype, fieldname, "read_only", 1, "Check")


# Fields we make mandatory, as (doctype, fieldname).
REQUIRED_FIELDS = [
    ("Purchase Order", "set_warehouse"),
    ("Purchase Receipt", "set_warehouse"),
]

# Fields mandatory only under a condition, as (doctype, fieldname, condition).
# PI's Set Warehouse is only shown when Update Stock is ticked, so it can't always be required.
CONDITIONALLY_REQUIRED_FIELDS = [
    ("Purchase Invoice", "set_warehouse", "eval:doc.update_stock"),
]


def make_fields_required():
    """Make the fields above mandatory with Property Setters, like hide_fields."""
    for doctype, fieldname in REQUIRED_FIELDS:
        filters = {"doc_type": doctype, "field_name": fieldname, "property": "reqd"}
        if frappe.db.get_value("Property Setter", filters, "value") == "1":
            continue

        make_property_setter(doctype, fieldname, "reqd", 1, "Check")

    for doctype, fieldname, condition in CONDITIONALLY_REQUIRED_FIELDS:
        filters = {"doc_type": doctype, "field_name": fieldname, "property": "mandatory_depends_on"}
        if frappe.db.get_value("Property Setter", filters, "value") == condition:
            continue

        make_property_setter(doctype, fieldname, "mandatory_depends_on", condition, "Code")
