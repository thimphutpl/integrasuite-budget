import frappe
from frappe import _


def custom_validate_account_party_type(self):
    if self.is_cancelled:
        return

    if self.party_type and self.party:
        account_type = frappe.get_cached_value(
            "Account",
            self.account,
            "account_type",
        )

        allowed_account_types = [
            "Receivable",
            "Payable",
            "Equity",
            "Expense Account",
            "Current Asset",
        ]

        if account_type and account_type not in allowed_account_types:
            frappe.throw(
                _(
                    "Party Type and Party can only be set for "
                    "Receivable / Payable / Equity / Expense / Current Asset "
                    "account<br><br>{0}"
                ).format(self.account)
            )