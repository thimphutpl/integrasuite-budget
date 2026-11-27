"""Add or Deduct on selling tax rows, like ERPNext already has on buying tax rows.

The field (`add_deduct_tax` on Sales Taxes and Charges) comes from selling/custom_field.py. A
"Deduct" row keeps a positive tax amount but lowers the running total and the grand total, the
same way a buying "Deduct" row does.

Most of ERPNext's tax code already reads `add_deduct_tax` on any doctype (item-wise breakup,
inclusive tax, discount on grand total, browser-side totals). Three gaps are closed here:

1. Server totals: `calculate_taxes_and_totals.get_tax_amount_if_for_valuation_or_deduction` only
   negates for purchase doctypes. There is no hook for it, so it is monkey-patched
   (`apply_patch`), called from `before_request` / `before_job` so it is applied in every worker
   (hooks.py is not imported again when Frappe serves the hooks from cache).
2. Sales Invoice GL: ERPNext always credits the tax account. A Deduct row is debited instead
   (`CustomSalesInvoice`).
3. POS Invoice: consolidation sums tax rows per account and ignores Add/Deduct, so Deduct is
   rejected there (`validate_pos_invoice`).

Browser side: add_deduct_tax.js.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.utils import get_account_currency
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

SALES_TAX_DOCTYPE = "Sales Taxes and Charges"


def is_sales_deduct(tax):
    return tax.get("doctype") == SALES_TAX_DOCTYPE and tax.get("add_deduct_tax") == "Deduct"


# --- 1. Server totals (monkey-patch, see module docstring) -----------------------------------

def _get_tax_amount_if_for_valuation_or_deduction(self, tax_amount, tax):
    tax_amount = _get_tax_amount_if_for_valuation_or_deduction.original(self, tax_amount, tax)
    if is_sales_deduct(tax):
        tax_amount *= -1.0
    return tax_amount


def apply_patch():
    """before_request / before_job: idempotent, the original is wrapped only once per process."""
    current = calculate_taxes_and_totals.get_tax_amount_if_for_valuation_or_deduction
    if current is _get_tax_amount_if_for_valuation_or_deduction:
        return
    _get_tax_amount_if_for_valuation_or_deduction.original = current
    calculate_taxes_and_totals.get_tax_amount_if_for_valuation_or_deduction = (
        _get_tax_amount_if_for_valuation_or_deduction
    )


apply_patch()


# --- 2. Sales Invoice GL ---------------------------------------------------------------------

class CustomSalesInvoice(SalesInvoice):
    def make_tax_gl_entries(self, gl_entries):
        """ERPNext's version with debit instead of credit for Deduct rows.

        Invoices without a Deduct row go through ERPNext's own method unchanged.
        """
        if not any(is_sales_deduct(tax) for tax in self.get("taxes")):
            return super().make_tax_gl_entries(gl_entries)

        enable_discount_accounting = cint(
            frappe.get_single_value("Selling Settings", "enable_discount_accounting")
        )

        for tax in self.get("taxes"):
            amount, base_amount = self.get_tax_amounts(tax, enable_discount_accounting)

            if flt(tax.base_tax_amount_after_discount_amount):
                account_currency = get_account_currency(tax.account_head)
                dr_or_cr = "debit" if is_sales_deduct(tax) else "credit"
                gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": tax.account_head,
                            "against": self.customer,
                            dr_or_cr: flt(base_amount, tax.precision("tax_amount_after_discount_amount")),
                            f"{dr_or_cr}_in_account_currency": (
                                flt(base_amount, tax.precision("base_tax_amount_after_discount_amount"))
                                if account_currency == self.company_currency
                                else flt(amount, tax.precision("tax_amount_after_discount_amount"))
                            ),
                            f"{dr_or_cr}_in_transaction_currency": flt(
                                amount, tax.precision("tax_amount_after_discount_amount")
                            ),
                            "cost_center": tax.cost_center,
                        },
                        account_currency,
                        item=tax,
                    )
                )


# --- 3. POS Invoice --------------------------------------------------------------------------

def validate_pos_invoice(doc, method=None):
    """POS Invoice validate: consolidation into a Sales Invoice would add Deduct rows as Add."""
    rows = [str(tax.idx) for tax in doc.get("taxes") if is_sales_deduct(tax)]
    if rows:
        frappe.throw(
            _("Taxes and Charges row(s) {0}: Deduct is not supported on POS Invoices.").format(
                ", ".join(rows)
            )
        )


# --- Data ------------------------------------------------------------------------------------

def set_missing_add_deduct_tax():
    """after_migrate: rows created before the field existed get "Add" (what a blank means anyway),
    so old drafts show the value instead of the form filling it in and marking them unsaved."""
    table = frappe.qb.DocType(SALES_TAX_DOCTYPE)
    (
        frappe.qb.update(table)
        .set(table.add_deduct_tax, "Add")
        .where(table.add_deduct_tax.isnull() | (table.add_deduct_tax == ""))
    ).run()
