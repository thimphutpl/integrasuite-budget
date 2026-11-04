import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# ERPNext fields we hide, as (doctype, fieldname). Hiding a Tab Break hides the whole tab.
HIDDEN_FIELDS = [
    ("Purchase Order", "address_and_contact_tab"),
    ("Purchase Receipt", "address_and_contact_tab"),
    ("Purchase Invoice", "address_and_contact_tab"),
    ("Item", "allow_negative_stock"),
    ("Stock Settings", "allow_negative_stock"),
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
