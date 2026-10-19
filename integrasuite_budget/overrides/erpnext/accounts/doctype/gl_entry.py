import erpnext.accounts.doctype.gl_entry.gl_entry as gl_entry_module
from erpnext.accounts.doctype.gl_entry.gl_entry import GLEntry
from integrasuite_budget.overrides.erpnext.accounts.functions.party import custom_validate_account_party_type



class CustomGLEntry(GLEntry):
    def validate(self):
        # Replace the function reference used by the GL Entry module.
        gl_entry_module.validate_account_party_type = (
            custom_validate_account_party_type
        )

        return super().validate()