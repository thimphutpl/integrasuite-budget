"""Liquidated Damages (LD): a penalty on the Purchase Invoice for a late Purchase Receipt.

LD days = PR Actual Receipt Date - required (schedule) date. The LD amount is posted through
ERPNext's Write Off section of the Purchase Invoice.
Fields: buying/custom_field.py and buying/property_setter.py. Browser side: liquidated_damages.js.
"""

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt

from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.accounts.utils import get_account_currency
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    make_purchase_invoice as erpnext_make_purchase_invoice,
)
from integrasuite_budget.overrides.erpnext.material_management.buying.supplier_invoice_no import (
    set_bill_no_from_purchase_receipt,
)

# 0.1% of the Purchase Receipt grand total per day of delay, capped at 100 days (10%).
# Keep in sync with liquidated_damages.js.
LD_RATE_PER_DAY = 0.1
LD_MAX_DAYS = 100


class CustomPurchaseInvoice(PurchaseInvoice):
    def make_write_off_gl_entry(self, gl_entries):
        """For LD, post the supplier entry net of LD instead of a separate supplier debit.

        ERPNext calls this after make_supplier_gl_entry, so the supplier credit already exists.
        Plain write-offs (ld_days = 0), or LD with no matching supplier entry, keep ERPNext's
        standard two-entry posting.
        """
        if (
            cint(self.get("ld_days")) > 0
            and self.write_off_account
            and flt(self.write_off_amount)
            and self.reduce_supplier_gl_entry_by_write_off(gl_entries)
        ):
            gl_entries.append(self.get_write_off_account_gl_entry())
            return

        super().make_write_off_gl_entry(gl_entries)

    def get_write_off_account_gl_entry(self):
        # Same as the write off account credit ERPNext builds in make_write_off_gl_entry
        write_off_account_currency = get_account_currency(self.write_off_account)
        return self.get_gl_dict(
            {
                "account": self.write_off_account,
                "against": self.supplier,
                "credit": flt(self.base_write_off_amount),
                "credit_in_account_currency": self.base_write_off_amount
                if write_off_account_currency == self.company_currency
                else self.write_off_amount,
                "credit_in_transaction_currency": self.write_off_amount,
                "cost_center": self.cost_center or self.write_off_cost_center,
            },
            item=self,
        )

    def reduce_supplier_gl_entry_by_write_off(self, gl_entries):
        """Reduce the main supplier credit entry by the write off amount. Returns True if reduced."""
        # Same against_voucher rule as ERPNext's add_supplier_gl_entry
        against_voucher = self.name
        if self.is_return and self.return_against and not self.get("update_outstanding_for_self"):
            against_voucher = self.return_against

        for gle in gl_entries:
            if (
                gle.account == self.credit_to
                and gle.party == self.supplier
                and gle.against_voucher == against_voucher
                and not gle.get("_skip_merge")
                and flt(gle.credit) >= flt(self.base_write_off_amount)
            ):
                gle.credit = flt(gle.credit) - flt(self.base_write_off_amount)
                gle.credit_in_account_currency = flt(gle.credit_in_account_currency) - (
                    flt(self.base_write_off_amount)
                    if self.party_account_currency == self.company_currency
                    else flt(self.write_off_amount)
                )
                gle.credit_in_transaction_currency = flt(gle.credit_in_transaction_currency) - flt(
                    self.write_off_amount
                )
                return True
        return False


def get_ld_required_dates(purchase_receipt):
    """Required (schedule) dates of all PR items, taken from the linked PO when available."""
    dates = set()
    for d in purchase_receipt.items:
        if d.get("purchase_order_item"):
            dates.add(frappe.db.get_value("Purchase Order Item", d.purchase_order_item, "schedule_date"))
        elif d.get("purchase_order"):
            dates.add(frappe.db.get_value("Purchase Order", d.purchase_order, "schedule_date"))
        elif d.get("schedule_date"):
            dates.add(d.schedule_date)
    dates.discard(None)
    return dates


def calculate_ld_amount(ld_days, grand_total):
    return flt(min(ld_days, LD_MAX_DAYS) * LD_RATE_PER_DAY / 100 * flt(grand_total), 2)


def set_ld_from_purchase_receipt(purchase_receipt, invoice):
    """Set LD Days and LD (write off) amount on a Purchase Invoice created from a late Purchase Receipt."""
    required_dates = get_ld_required_dates(purchase_receipt)
    if len(required_dates) > 1:
        frappe.throw(
            _("Multiple delivery dates in Items Table. Same delivery date required to calculate LD days")
        )

    if not (required_dates and purchase_receipt.get("actual_receipt_date")):
        return

    ld_days = date_diff(purchase_receipt.actual_receipt_date, required_dates.pop())
    if ld_days <= 0:
        return

    write_off_account, cost_center = frappe.get_cached_value(
        "Company", invoice.company, ["write_off_account", "cost_center"]
    )
    if not write_off_account:
        frappe.throw(
            _("Please set Write Off Account in Company {0} to apply Liquidated Damages").format(
                frappe.bold(invoice.company)
            )
        )

    invoice.ld_days = ld_days
    invoice.write_off_amount = calculate_ld_amount(ld_days, purchase_receipt.grand_total)
    invoice.write_off_account = write_off_account
    invoice.write_off_cost_center = invoice.get("write_off_cost_center") or cost_center


def validate_actual_receipt_date(doc, method=None):
    """doc_events validate (Purchase Receipt): Actual Receipt Date is mandatory except on returns.

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
