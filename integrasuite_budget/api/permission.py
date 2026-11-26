import frappe


def has_app_permission():
    app_name = "integrasuite_budget"

    settings = frappe.get_all(
        "App Setting",
        fields=["name", "app_name", "hide"]
    )

    for setting in settings:
        apps = (setting.app_name or "").split()

        if app_name in apps:
            return not bool(setting.hide)

    return True