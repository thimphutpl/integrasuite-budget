import frappe
from frappe.desk.doctype.custom_sidebar.custom_sidebar import get_customization
from frappe.desk.doctype.sidebar.sidebar import unlinked_key

# ERPNext sidebar links we don't use, per module, as (link_type, link_to).
HIDDEN_SIDEBAR_ITEMS = {
    "Buying": [
        ("DocType", "Request for Quotation"),
        ("DocType", "Supplier Quotation"),
    ],
    "Selling": [
        ("DocType", "Quotation"),
    ],
}

# Whole sidebar sections we don't use, per module, by label. The section and every link in it
# are hidden: a layer hides rows one by one, so hiding only the Section Break would leave its links.
HIDDEN_SIDEBAR_SECTIONS = {
    "Selling": ["POS"],
}


def _section_items(module, label):
    """Return the Section Break row named `label` in the module's ERPNext sidebar and the links in it."""
    base = frappe.db.get_value("Sidebar", {"module": module}, "name")
    if not base:
        return []

    items, in_section = [], False
    for item in frappe.get_doc("Sidebar", base).items:
        if item.type == "Section Break":
            in_section = item.label == label
            if in_section:
                items.append({"type": "Section Break", "label": label})
        elif in_section and item.child:
            items.append({"type": item.type, "link_type": item.link_type, "link_to": item.link_to})
        elif in_section:
            in_section = False
    return items


def _hidden_items(module):
    """The rows to hide in a module's sidebar: the links above plus each hidden section's rows."""
    items = [{"type": "Link", "link_type": t, "link_to": to} for t, to in HIDDEN_SIDEBAR_ITEMS.get(module, [])]
    for label in HIDDEN_SIDEBAR_SECTIONS.get(module, []):
        items += _section_items(module, label)
    return items


def _same_item(row, item):
    if item["type"] == "Section Break":
        return row.type == "Section Break" and row.key == unlinked_key(item)
    return row.link_type == item["link_type"] and row.link_to == item["link_to"]


def hide_sidebar_items():
    """Hide the items above in each module's site sidebar layer (Custom Sidebar).

    ERPNext's own Sidebar is reset on every migrate, so the change lives in the site layer
    instead, which is laid over it. Other rows in the layer are left as they are.
    """
    for module in {*HIDDEN_SIDEBAR_ITEMS, *HIDDEN_SIDEBAR_SECTIONS}:
        layer = get_customization(module, None)
        if layer:
            layer = frappe.get_doc("Custom Sidebar", layer.name)
        else:
            layer = frappe.new_doc("Custom Sidebar")
            layer.module = module

        changed = False
        for item in _hidden_items(module):
            row = next(
                (row for row in layer.sidebar_items if not row.added and _same_item(row, item)),
                None,
            )
            if not row:
                if item["type"] == "Section Break":
                    # A Section Break links nowhere, so the layer names it by key.
                    item = {**item, "key": unlinked_key(item)}
                row = layer.append("sidebar_items", item)

            if not row.hidden:
                row.hidden = 1
                changed = True

        if changed:
            layer.save(ignore_permissions=True)
