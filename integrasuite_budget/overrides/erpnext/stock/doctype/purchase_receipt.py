import frappe
from frappe import _

from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    make_purchase_invoice as erpnext_make_purchase_invoice,
)
from integrasuite_budget.overrides.erpnext.accounts.doctype.purchase_invoice import (
    set_bill_no_from_purchase_receipt,
    set_ld_from_purchase_receipt,
)


def validate_actual_receipt_date(doc, method=None):
    """doc_events validate: Actual Receipt Date is mandatory except on returns.

    The field's mandatory_depends_on only works in the browser, so it is enforced here too.
    """
    if not doc.is_return and not doc.get("actual_receipt_date"):
        frappe.throw(_("Actual Receipt Date is mandatory"), frappe.MandatoryError)


@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None, args=None):
    """ERPNext's PR -> PI mapping, plus Supplier Invoice No and Liquidated Damages for a late receipt.

    Replaces erpnext...purchase_receipt.make_purchase_invoice via override_whitelisted_methods.
    """
    invoice = erpnext_make_purchase_invoice(source_name, target_doc, args)

    set_bill_no_from_purchase_receipt(invoice)

    set_ld_from_purchase_receipt(frappe.get_doc("Purchase Receipt", source_name), invoice)

    if invoice.get("ld_days"):
        # Outstanding amount and the payment schedule both net off the write off amount
        invoice.run_method("calculate_taxes_and_totals")
        invoice.set("payment_schedule", [])
        invoice.set_payment_schedule()

    return invoice
