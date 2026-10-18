import frappe
from frappe.utils import cint

from erpnext.accounts.doctype.cost_center.cost_center import CostCenter


class CustomCostCenter(CostCenter):
    def after_insert(self):
        super().after_insert()
        self.create_branch()

    def create_branch(self):
        if cint(self.is_group) or cint(self.branch_created):
            return

        # Prevent duplicate Branch creation
        if frappe.db.exists("Branch", {"cost_center": self.name}):
            self.db_set("branch_created", 1)
            return

        abbr = frappe.db.get_value("Company", self.company, "abbr")

        if not abbr:
            frappe.throw(
                f"Company abbreviation is missing for {self.company}"
            )

        branch_name = (self.cost_center_name or "").strip()

        if not branch_name:
            frappe.throw("Cost Center Name is required to create a Branch.")

        branch = frappe.new_doc("Branch")
        branch.branch = branch_name
        branch.cost_center = self.name
        branch.company = self.company
        branch.company_abbr = abbr
        branch.insert()

        self.db_set("branch_created", 1)