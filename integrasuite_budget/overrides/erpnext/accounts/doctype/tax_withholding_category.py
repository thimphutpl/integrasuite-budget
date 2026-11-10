import frappe
import erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category as tax_withholding_category


_original_get_tax_id_for_party = (
    tax_withholding_category.get_tax_id_for_party
)


def custom_get_tax_id_for_party(party_type, party):
    if party_type == "Employee":
        return None

    return _original_get_tax_id_for_party(party_type, party)


tax_withholding_category.get_tax_id_for_party = (
    custom_get_tax_id_for_party
)