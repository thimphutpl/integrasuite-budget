"""Buying (MR -> PO -> PR -> PI) Custom Fields, created or updated after every migrate."""

from integrasuite_budget.overrides.erpnext.material_management.utils.custom_field import (
    BRANCH_FIELD,
    add_custom_fields,
)

# PO, PR and PI already have a header Cost Center; MR gets the same field so it maps across.
MR_COST_CENTER_FIELD = {
    "fieldname": "cost_center",
    "label": "Cost Center",
    "fieldtype": "Link",
    "options": "Cost Center",
    "read_only": 1,
    "insert_after": "branch",
}

# Liquidated Damages: LD days = Actual Receipt Date - required (schedule) date, see liquidated_damages.py.
PR_ACTUAL_RECEIPT_DATE_FIELD = {
    "fieldname": "actual_receipt_date",
    "label": "Actual Receipt Date",
    "fieldtype": "Date",
    # Not on returns: they copy it from the original PR, and PRs made before this field existed
    # have none, which would block returning them.
    "reqd": 0,
    "mandatory_depends_on": "eval:!doc.is_return",
    "insert_after": "posting_time",
}

PI_LD_FIELDS = [
    {
        "fieldname": "ld_days",
        "label": "LD Days",
        "fieldtype": "Int",
        "no_copy": 1,
        "insert_after": "write_off",
    },
    {
        "fieldname": "ld_description",
        "label": "LD Description",
        "fieldtype": "Small Text",
        "no_copy": 1,
        "insert_after": "base_write_off_amount",
    },
]

CUSTOM_FIELDS = {
    "Material Request": [BRANCH_FIELD, MR_COST_CENTER_FIELD],
    "Purchase Order": [BRANCH_FIELD],
    "Purchase Receipt": [BRANCH_FIELD, PR_ACTUAL_RECEIPT_DATE_FIELD],
    "Purchase Invoice": [BRANCH_FIELD, *PI_LD_FIELDS],
}


def apply_custom_fields():
    """after_migrate: create the buying Custom Fields above."""
    add_custom_fields(CUSTOM_FIELDS)
