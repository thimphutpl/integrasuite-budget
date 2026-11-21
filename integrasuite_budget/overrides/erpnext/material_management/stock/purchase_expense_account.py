"""Stock Entry Difference Account (`expense_account` on each item row) from the item's
Purchase Expense Account.

ERPNext fills the row from Item Defaults' Expense Account -> Item Group's -> Company Stock
Adjustment Account. We put the Purchase Expense Account (Item -> Item Group -> Brand, ERPNext's own
lookup) in front of that chain; without one, ERPNext's chain applies unchanged.

`get_item_details` serves both the form (item_code trigger) and validate (empty rows, which covers
API, imports and Material Request -> Stock Entry). Rows that already hold an account are left
alone, so a manually chosen Difference Account is kept.
"""

import frappe

from erpnext.controllers.buying_controller import get_purchase_expense_account
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


class CustomStockEntry(StockEntry):
    @frappe.whitelist()
    def get_item_details(self, args=None, for_update=False):
        ret = super().get_item_details(args, for_update)

        # Opening entries need an Asset/Liability difference account, and ERPNext books
        # Subcontracting Delivery to the company's Default Expense Account: keep both as they are.
        if self.is_opening == "Yes" or self.purpose == "Subcontracting Delivery":
            return ret

        item_code = (args or {}).get("item_code")
        if item_code:
            account = get_purchase_expense_account(item_code, self.company).get(
                "purchase_expense_account"
            )
            if account:
                ret["expense_account"] = account

        return ret
