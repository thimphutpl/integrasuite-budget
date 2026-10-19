
import frappe
from frappe import _
from frappe.query_builder import DocType


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_party_type(
    doctype: str,
    txt: str,
    searchfield: str,
    start: int,
    page_len: int,
    filters: dict,
):
    PartyType = DocType("Party Type")

    query = (
        frappe.qb.from_(PartyType)
        .select(PartyType.name)
        .orderby(PartyType.name)
    )

    if filters and filters.get("account"):
        account_type = frappe.db.get_value(
            "Account", filters.get("account"), "account_type"
        )

        if account_type:
            if account_type in [
                "Receivable",
                "Payable",
                "Expense Account",
                "Tax",
            ]:
                query = query.where(
                    (PartyType.account_type == account_type)
                    | (PartyType.name == "Supplier")
                    | (PartyType.name == "Customer")
                    | (PartyType.name == "Employee")
                )
            else:
                query = query.where(
                    PartyType.account_type == account_type
                )

    if frappe.local.lang == "en":
        query = query.where(
            getattr(PartyType, searchfield).like(f"%{txt}%")
        )
        query = query.limit(page_len).offset(start)
        return query.run() or []

    results = query.run()
    search_text = txt.lower()

    results = [
        row for row in results
        if search_text in frappe._(row[0]).lower()
    ]

    return results[start : start + page_len]
