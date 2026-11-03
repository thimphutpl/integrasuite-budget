frappe.provide("integrasuite_budget");

// Stop ERPNext from adding buttons to a form, by label or by whole dropdown group.
// ERPNext adds most of its buttons in its controller refresh, which runs after our
// refresh handlers, so we skip them at add time instead of removing them later.
integrasuite_budget.hide_buttons = function (doctype, { labels = [], groups = [] }) {
    frappe.ui.form.on(doctype, {
        setup(frm) {
            const add_custom_button = frm.add_custom_button.bind(frm);

            frm.add_custom_button = function (label, fn, group) {
                if (labels.includes(label) || (group && groups.includes(group))) return;
                return add_custom_button(label, fn, group);
            };
        },
    });
};
