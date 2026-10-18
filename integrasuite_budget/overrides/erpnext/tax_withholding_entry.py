
from erpnext.accounts.doctype.tax_withholding_entry.tax_withholding_entry import (
    TaxWithholdingEntry,
    JournalTaxWithholding,
)
import frappe
from frappe import _
from frappe.utils import flt
import erpnext

class CustomTaxWithholdingEntry(TaxWithholdingEntry):
    """Custom Tax Withholding Entry controller."""

    pass


ALLOWED_VOUCHER_TYPES = (
    "Debit Note",
    "Credit Note",
    "Journal Entry",
    "Bank Entry",
    "Cash Entry",
    "Credit Card Entry",
    "Contra Entry",
    "Excise Entry",
    "Write Off Entry",
    "Opening Entry",
    "Depreciation Entry",
    "Asset Disposal",
    "Periodic Accounting Entry",
    "Exchange Rate Revaluation",
    "Exchange Gain Or Loss",
    "Deferred Revenue",
    "Deferred Expense",
)


def custom_should_apply_tds(self):
    return (
        self.doc.apply_tds
        and self.doc.voucher_type in ALLOWED_VOUCHER_TYPES
    )

def custom_create_base_entry(self, source_entry, category, tax_rate, default_obj):
    entry = {}

    if default_obj:
        entry.update(default_obj)

    cost_center = (
        self.doc.get("cost_center")
        or erpnext.get_default_cost_center(self.doc.company)
    )

    entry.update(
        {
            "taxable_doctype": source_entry.taxable_doctype,
            "taxable_name": source_entry.taxable_name,
            "taxable_date": source_entry.taxable_date,
            "tax_withholding_category": category.name,
            "tax_rate": tax_rate,
            "party_type": self.party_type,
            "party": self.party,
            "company": self.doc.company,
            "tax_id": category.tax_id,
            "cost_center": cost_center,
            "branch": self.doc.get("branch"),
        }
    )

    return entry


def custom_setup_direction_fields(self):

    if self.party_row.get("debit"):
        self.party_field = "debit"
        self.reverse_field = "credit"
    else:
        self.party_field = "credit"
        self.reverse_field = "debit"

    self.precision = self.doc.precision(
        self.party_field, self.party_row


    )

def custom_update_taxable_amounts(self):
    if not self.category_details:
        return

    net_amount = self._calculate_net_total()
    category = next(iter(self.category_details.values()))
    category["taxable_amount"] = net_amount


def custom_calculate_net_total(self):
    from erpnext.accounts.report.general_ledger.general_ledger import (
        get_account_type_map,
    )

    account_type_map = get_account_type_map(self.doc.company)

    # Calculate the taxable base from the ordinary counter-account rows.
    net_amount = sum(
        flt(row.get(self.reverse_field))
        - flt(row.get(self.party_field))
        for row in self.doc.get("accounts")
        if row.account != self.party_account
        and not row.get("is_tax_withholding_account")
        and account_type_map.get(row.account) not in ("Tax", "Chargeable")
    )

    # Add back the withholding amount already deducted from the counter account.
    # This prevents a second calculation from using the reduced balance.
    existing_tds_amount = sum(
        flt(row.get(self.reverse_field))
        - flt(row.get(self.party_field))
        for row in self.doc.get("accounts")
        if row.get("is_tax_withholding_account")
    )

    net_amount += existing_tds_amount

    return flt(net_amount, self.precision)



def custom_update_tax_rows(self):
    """Update TDS rows using the withholding amounts calculated for this document."""

    frappe.log_error(
    title="TDS Source Entries",
    message=frappe.as_json([
        {
            "name": row.name,
            "taxable_amount": row.get("taxable_amount"),
            "tax_rate": row.get("tax_rate"),
            "withholding_amount": row.get("withholding_amount"),
            "status": row.get("status"),
        }
        for row in self.doc.get("tax_withholding_entries")
    ], indent=2),
)


    if not self._should_apply_tds():
        self._cleanup_duplicate_tds_rows(None)
        return

    if self.has_multiple_parties:
        frappe.throw(
            _("Cannot apply TDS against multiple parties in one entry")
        )

    # Reverse previously applied TDS before recalculating.
    self._reset_existing_tds()

    # Calculate the withholding amounts using the existing controller logic.
    account_amount_map = self._calculate_account_wise_amount()

    if not account_amount_map:
        self._recalculate_totals()
        return

    for account_head, tax_amount in account_amount_map.items():
        tax_amount = flt(tax_amount, self.precision)

        if not tax_amount:
            continue

        self._create_or_update_tds_row(account_head, tax_amount)
        self._update_party_amount(tax_amount, is_reversal=False)

    self._recalculate_totals()





def custom_update_party_amount(self, amount, is_reversal=False):
    """Adjust the counter account for Journal Entry TDS/TCS."""

    amount = abs(flt(amount, self.precision))
    counter_rows = [
        row
        for row in self.doc.get("accounts")
        if row.name != self.party_row.name
        and not row.get("is_tax_withholding_account")
    ]

    frappe.log_error(
    title="Custom TDS Amount",
    message=frappe.as_json({
        "amount_received": amount,
        "is_reversal": is_reversal,
        "party_type": self.party_type,
        "party_field": self.party_field,
        "reverse_field": self.reverse_field,
        "party_account": self.party_account,
        "accounts": [
            {
                "account": row.account,
                "debit": row.debit,
                "credit": row.credit,
                "is_tax_withholding_account": row.get(
                    "is_tax_withholding_account"
                ),
            }
            for row in self.doc.get("accounts")
        ],
    }, indent=2),
)

    if not counter_rows:
        frappe.throw(_("No counter account found to adjust for TDS/TCS."))

    # This implementation assumes one counter account for this calculation.
    counter_row = counter_rows[0]

    if flt(counter_row.get("debit")):
        active_field = "debit"
    elif flt(counter_row.get("credit")):
        active_field = "credit"
    else:
        active_field = "debit" if self.party_type == "Customer" else "credit"

    account_currency_field = f"{active_field}_in_account_currency"
    exchange_rate = flt(counter_row.get("exchange_rate")) or 1

    amount_in_account_currency = flt(
        amount / exchange_rate,
        self.precision,
    )

    # Normal processing reduces the counter account.
    # Resetting an existing TDS/TCS row restores it.
    adjustment = amount if is_reversal else -amount
    adjustment_in_account_currency = (
        amount_in_account_currency if is_reversal
        else -amount_in_account_currency
    )

    counter_row.update({
        active_field: flt(
            counter_row.get(active_field) + adjustment,
            self.precision,
        ),
        account_currency_field: flt(
            counter_row.get(account_currency_field)
            + adjustment_in_account_currency,
            self.precision,
        ),
    })


    
def custom_create_or_update_tds_row(self, account_head, tax_amount):
    from erpnext.accounts.utils import get_account_currency
    from erpnext.setup.utils import get_exchange_rate as _get_exchange_rate

    account_currency = get_account_currency(account_head)
    company_currency = frappe.get_cached_value("Company", self.doc.company, "default_currency")
    exchange_rate = _get_exchange_rate(account_currency, company_currency, self.doc.posting_date)

    tax_amount = flt(tax_amount, self.precision)
    tax_amount_in_account_currency = flt(tax_amount / exchange_rate, self.precision)

    tax_row = None
    for row in self.doc.get("accounts"):
        if row.account == account_head and row.get("is_tax_withholding_account"):
            tax_row = row
            break

    if not tax_row:
        tax_row = self.doc.append(
            "accounts",
            {
                "account": account_head,
                "account_currency": account_currency,
                "exchange_rate": exchange_rate,
                "branch": self.doc.get("branch"),
                "cost_center": self.doc.get("cost_center")
                or erpnext.get_default_cost_center(self.doc.company),
                "credit": 0,
                "credit_in_account_currency": 0,
                "debit": 0,
                "debit_in_account_currency": 0,
                "is_tax_withholding_account": 1,
            },
        )

    # Supplier (TDS): Credit. Customer (TCS): Debit.
    if self.party_type == "Customer":
        tax_row.update(
            {
                "tds_account": account_head,
                "branch": self.doc.get("branch"),
                "cost_center": self.doc.get("cost_center"),
                "debit": tax_amount,
                "debit_in_account_currency": tax_amount_in_account_currency,
                "credit": 0,
                "credit_in_account_currency": 0,
            }
        )
    else:
        tax_row.update(
            {
                "tds_account": account_head,
                "branch": self.doc.get("branch"),
                "cost_center": self.doc.get("cost_center"),
                "credit": tax_amount,
                "credit_in_account_currency": tax_amount_in_account_currency,
                "debit": 0,
                "debit_in_account_currency": 0,
            }
        )

    self._cleanup_duplicate_tds_rows(tax_row)


JournalTaxWithholding._should_apply_tds = custom_should_apply_tds
JournalTaxWithholding._setup_direction_fields = custom_setup_direction_fields

JournalTaxWithholding._update_party_amount = custom_update_party_amount
JournalTaxWithholding._update_taxable_amounts = (
    custom_update_taxable_amounts
)
JournalTaxWithholding._calculate_net_total = custom_calculate_net_total
JournalTaxWithholding.update_tax_rows = custom_update_tax_rows
JournalTaxWithholding._create_or_update_tds_row = (
    custom_create_or_update_tds_row
)
JournalTaxWithholding._create_base_entry = custom_create_base_entry