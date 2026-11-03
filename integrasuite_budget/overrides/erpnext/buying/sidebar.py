import frappe
from frappe.desk.doctype.custom_sidebar.custom_sidebar import get_customization

# ERPNext sidebar links we don't use, per module, as (link_type, link_to).
HIDDEN_SIDEBAR_ITEMS = {
    "Buying": [
        ("DocType", "Request for Quotation"),
        ("DocType", "Supplier Quotation"),
    ],
}


def hide_sidebar_items():
    """Hide the items above in each module's site sidebar layer (Custom Sidebar).

    ERPNext's own Sidebar is reset on every migrate, so the change lives in the site layer
    instead, which is laid over it. Other rows in the layer are left as they are.
    """
    for module, links in HIDDEN_SIDEBAR_ITEMS.items():
        layer = get_customization(module, None)
        if layer:
            layer = frappe.get_doc("Custom Sidebar", layer.name)
        else:
            layer = frappe.new_doc("Custom Sidebar")
            layer.module = module

        changed = False
        for link_type, link_to in links:
            row = next(
                (
                    row
                    for row in layer.sidebar_items
                    if not row.added and row.link_type == link_type and row.link_to == link_to
                ),
                None,
            )
            if not row:
                row = layer.append(
                    "sidebar_items", {"type": "Link", "link_type": link_type, "link_to": link_to}
                )

            if not row.hidden:
                row.hidden = 1
                changed = True

        if changed:
            layer.save(ignore_permissions=True)
