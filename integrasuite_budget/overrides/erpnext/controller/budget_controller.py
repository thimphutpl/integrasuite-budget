
import frappe
from frappe import qb

from erpnext.controllers.budget_controller import BudgetValidation


def custom_get_budget_records(self) -> list:
    bud = qb.DocType("Budget")
    bud_acc = qb.DocType("Budget Account")

    query = (
        qb.from_(bud)
        .inner_join(bud_acc)
        .on(
            (bud_acc.parent == bud.name)
            & (bud_acc.parenttype == "Budget")
            & (bud_acc.parentfield == "accounts")
        )
        .select(
            bud.name,
            bud.budget_against,
            bud.company,
            bud_acc.account,
            bud_acc.budget_amount,
            bud.fiscal_year,
            bud.applicable_on_material_request,
            bud.action_if_annual_budget_exceeded_on_mr,
            bud.action_if_accumulated_monthly_budget_exceeded_on_mr,
            bud.applicable_on_purchase_order,
            bud.action_if_annual_budget_exceeded_on_po,
            bud.action_if_accumulated_monthly_budget_exceeded_on_po,
            bud.applicable_on_booking_actual_expenses,
            bud.action_if_annual_budget_exceeded,
            bud.action_if_accumulated_monthly_budget_exceeded,
        )
        .where(
            (bud.docstatus == 1)
            & (bud.company == self.company)
            & (bud.fiscal_year == self.fiscal_year)
        )
    )
   

    for x in self.dimensions:
        query = query.select(bud[x.get("fieldname")])

    budgets = query.run(as_dict=True)

    for x in budgets:
        x.is_tree = frappe.get_meta(x.budget_against).is_tree

    return budgets


# Override only this method
BudgetValidation.get_budget_records = custom_get_budget_records
