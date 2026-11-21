"""Generic Property Setter helpers, used by each module's property_setter.py.

ERPNext's DocType JSON is reloaded on every migrate, so changes to its fields live in Property
Setters instead, which are applied on top of it. Every helper skips a property that already has
the wanted value, so running them again on each migrate changes nothing.
"""

import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def set_field_property(doctype, fieldname, prop, value, property_type):
    """Set one field property with a Property Setter, unless it already has that value."""
    filters = {"doc_type": doctype, "field_name": fieldname, "property": prop}
    if frappe.db.get_value("Property Setter", filters, "value") == str(value):
        return

    make_property_setter(doctype, fieldname, prop, value, property_type)


def hide_fields(fields):
    """Hide fields, given as (doctype, fieldname). Hiding a Tab Break hides the whole tab."""
    for doctype, fieldname in fields:
        set_field_property(doctype, fieldname, "hidden", 1, "Check")


def hide_company_fields(doctypes):
    """Hide the mandatory Company field on these doctypes (single-company site).

    Frappe refuses a field that is hidden and mandatory without a default whenever the doctype is
    validated again (adding a Workflow, Customize Form, a new Custom Field), so the site's default
    company is set as the field's default first. Until a default company exists (a fresh site
    before the setup wizard) nothing is hidden; the next migrate applies it.
    """
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        return

    for doctype in doctypes:
        set_field_property(doctype, "company", "default", company, "Text")
        set_field_property(doctype, "company", "hidden", 1, "Check")


def make_fields_read_only(fields):
    """Make fields read-only, given as (doctype, fieldname)."""
    for doctype, fieldname in fields:
        set_field_property(doctype, fieldname, "read_only", 1, "Check")


def make_fields_required(fields):
    """Make fields mandatory, given as (doctype, fieldname)."""
    for doctype, fieldname in fields:
        set_field_property(doctype, fieldname, "reqd", 1, "Check")


def make_fields_required_when(fields):
    """Make fields mandatory under a condition, given as (doctype, fieldname, condition)."""
    for doctype, fieldname, condition in fields:
        set_field_property(doctype, fieldname, "mandatory_depends_on", condition, "Code")


def set_field_properties(properties):
    """Set other properties, given as (doctype, fieldname, property, value, property_type)."""
    for doctype, fieldname, prop, value, property_type in properties:
        set_field_property(doctype, fieldname, prop, value, property_type)


def move_fields_before(doctype, fieldnames, before):
    """Move standard fields, in the given order, to just before the field `before`.

    Standard fields can't be moved with insert_after, so this stores the whole order in a
    `field_order` Property Setter, the same thing Customize Form does. It is rebuilt from ERPNext's
    current order on every migrate, so fields added by an ERPNext upgrade are kept.
    """
    standard_order = [df.fieldname for df in frappe.get_doc("DocType", doctype).fields]
    if before not in standard_order or not all(f in standard_order for f in fieldnames):
        # ERPNext renamed something; leave the layout alone rather than guess.
        return

    order = [f for f in standard_order if f not in fieldnames]
    index = order.index(before)
    order[index:index] = fieldnames
    value = json.dumps(order)

    filters = {"doc_type": doctype, "property": "field_order", "doctype_or_field": "DocType"}
    if frappe.db.get_value("Property Setter", filters, "value") == value:
        return

    make_property_setter(doctype, None, "field_order", value, "Data", for_doctype=True)
