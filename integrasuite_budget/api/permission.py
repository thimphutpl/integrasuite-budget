import frappe

def has_app_permission():
    user_roles = frappe.get_roles(frappe.session.user)

    if "System Manager" in user_roles:
        return True

    allowed_roles = [
        "Budget Manager",
        "Budget User",
    ]

    return any(role in user_roles for role in allowed_roles)