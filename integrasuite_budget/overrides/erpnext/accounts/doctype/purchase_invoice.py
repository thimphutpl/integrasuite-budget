import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt

from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.accounts.utils import get_account_currency

# Liquidated Damages (LD): 0.1% of the Purchase Receipt grand total per day of delay,
# capped at 100 days (10%). Keep in sync with accounts/js/purchase_invoice.js.
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


def get_supplier_invoice_no_from_receipts(invoice):
    """Supplier Invoice No from the Purchase Receipts the invoice's items come from.

    PR's supplier_delivery_note is relabelled "Supplier Invoice No" (see property_setters.py).
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
    """doc_events validate: Supplier Invoice No comes from the linked Purchase Receipt(s).

    When the PR has one it is fixed (read-only in js/purchase_invoice.js); otherwise the user's
    value is kept.
    """
    supplier_invoice_no = get_supplier_invoice_no_from_receipts(doc)
    if supplier_invoice_no:
        doc.bill_no = supplier_invoice_no
