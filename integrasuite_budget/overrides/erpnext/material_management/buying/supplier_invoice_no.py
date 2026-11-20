"""Supplier Invoice No: entered once on the Purchase Receipt, carried to the Purchase Invoice.

PR's supplier_delivery_note is relabelled "Supplier Invoice No" and made mandatory
(buying/property_setter.py). Browser side: supplier_invoice_no.js.
"""

import frappe


def get_supplier_invoice_no_from_receipts(invoice):
    """Supplier Invoice No from the Purchase Receipts the invoice's items come from.

    Several receipts with different numbers are joined with ", ". Returns "" if none is set.
    """
    receipts = list(dict.fromkeys(d.purchase_receipt for d in invoice.get("items") if d.purchase_receipt))
    if not receipts:
        return ""

    numbers = frappe.get_all(
        "Purchase Receipt",
        filters={"name": ["in", receipts], "supplier_delivery_note": ["is", "set"]},
        pluck="supplier_delivery_note",
    )
    return ", ".join(dict.fromkeys(n.strip() for n in numbers if n and n.strip()))


def set_bill_no_from_purchase_receipt(doc, method=None):
    """doc_events validate (Purchase Invoice): Supplier Invoice No comes from the linked Purchase Receipt(s).

    When the PR has one it is fixed (read-only in supplier_invoice_no.js); otherwise the user's
    value is kept.
    """
    supplier_invoice_no = get_supplier_invoice_no_from_receipts(doc)
    if supplier_invoice_no:
        doc.bill_no = supplier_invoice_no
