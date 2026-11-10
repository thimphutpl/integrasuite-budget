import json

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
    ("Stock Entry", "project"),
    # Single-company site: ERPNext hides Company itself (erpnext.hide_company), but only after the
    # form is drawn, so it blinked and Branch (inserted after it) jumped. Hiding it in the meta
    # avoids that. If a second company is added, remove these AND delete their Property Setters.
    ("Material Request", "company"),
    ("Purchase Order", "company"),
    ("Purchase Receipt", "company"),
    ("Purchase Invoice", "company"),
    ("Stock Entry", "company"),
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
    ("Stock Entry", "cost_center"),
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
    # Copied to the Purchase Invoice's Supplier Invoice No (bill_no), see accounts/doctype/purchase_invoice.py
    ("Purchase Receipt", "supplier_delivery_note"),
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


# Other field properties, as (doctype, fieldname, property, value, property_type).
FIELD_PROPERTIES = [
    # Liquidated Damages reuse ERPNext's Write Off section (see accounts/doctype/purchase_invoice.py)
    ("Purchase Invoice", "write_off", "label", "Write Off / Liquidity Damages", "Data"),
    ("Purchase Invoice", "write_off", "collapsible", "1", "Check"),
    ("Purchase Invoice", "write_off_amount", "label", "Write Off / LD Amount", "Data"),
    ("Purchase Invoice", "write_off_cost_center", "fetch_from", "branch.cost_center", "Small Text"),
    ("Purchase Receipt", "supplier_delivery_note", "label", "Supplier Invoice No", "Data"),
    # Stock Entry's Accounting Dimensions is a tab; it becomes a collapsible section like on PO,
    # and move_stock_entry_accounting_dimensions() puts it on the Details tab.
    ("Stock Entry", "accounting_dimensions_section", "fieldtype", "Section Break", "Select"),
    ("Stock Entry", "accounting_dimensions_section", "collapsible", "1", "Check"),
]


def set_field_properties():
    """Apply the properties above with Property Setters, like hide_fields."""
    for doctype, fieldname, prop, value, property_type in FIELD_PROPERTIES:
        filters = {"doc_type": doctype, "field_name": fieldname, "property": prop}
        if frappe.db.get_value("Property Setter", filters, "value") == value:
            continue

        make_property_setter(doctype, fieldname, prop, value, property_type)


# Stock Entry: the Accounting Dimensions fields, moved to just before this field on the Details tab
# (after Posting Date/Time, before Inspection Required).
# Cost Center goes before the column break so it sits in the left column (Project is hidden).
SE_ACCOUNTING_DIMENSION_FIELDS = ["accounting_dimensions_section", "project", "cost_center", "dimension_col_break"]
SE_ACCOUNTING_DIMENSIONS_BEFORE = "reference_section"


def move_stock_entry_accounting_dimensions():
    """Move Stock Entry's Accounting Dimensions onto the Details tab with a `field_order` Property Setter.

    Standard fields can't be moved with insert_after, so this stores the whole order, the same
    thing Customize Form does. It is rebuilt from ERPNext's current order on every migrate, so
    fields added by an ERPNext upgrade are kept.
    """
    doctype = "Stock Entry"
    standard_order = [df.fieldname for df in frappe.get_doc("DocType", doctype).fields]
    if SE_ACCOUNTING_DIMENSIONS_BEFORE not in standard_order or not all(
        f in standard_order for f in SE_ACCOUNTING_DIMENSION_FIELDS
    ):
        # ERPNext renamed something; leave the layout alone rather than guess.
        return

    order = [f for f in standard_order if f not in SE_ACCOUNTING_DIMENSION_FIELDS]
    index = order.index(SE_ACCOUNTING_DIMENSIONS_BEFORE)
    order[index:index] = SE_ACCOUNTING_DIMENSION_FIELDS
    value = json.dumps(order)

    filters = {"doc_type": doctype, "property": "field_order", "doctype_or_field": "DocType"}
    if frappe.db.get_value("Property Setter", filters, "value") == value:
        return

    make_property_setter(doctype, None, "field_order", value, "Data", for_doctype=True)
