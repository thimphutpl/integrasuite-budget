"""Workspace report links that open an empty page.

Some of ERPNext's workspace links to Script Reports lack `is_query_report` (e.g. Buying's
Procurement Tracker, Purchase Register and the Trends reports), so the desk routes them to
`/<doctype>/view/report/<name>`, a Report Builder view that doesn't exist, instead of
`/query-report/<name>`. Workspaces are reloaded from ERPNext's JSON on migrate, so the flag is set
again after every migrate. Rows already flagged are skipped.
"""

import frappe

# Workspaces whose report links are fixed.
WORKSPACES = ["Buying", "Stock"]


def fix_report_links():
    """after_migrate: flag the WORKSPACES' links to Script/Query Reports as query reports."""
    query_reports = frappe.get_all(
        "Report", {"report_type": ["in", ["Script Report", "Query Report"]]}, pluck="name"
    )
    if not query_reports:
        return

    rows = frappe.get_all(
        "Workspace Link",
        {
            "parenttype": "Workspace",
            "parent": ["in", WORKSPACES],
            "link_type": "Report",
            "link_to": ["in", query_reports],
            "is_query_report": 0,
        },
        pluck="name",
    )
    for name in rows:
        frappe.db.set_value("Workspace Link", name, "is_query_report", 1, update_modified=False)

    if rows:
        frappe.clear_cache()
