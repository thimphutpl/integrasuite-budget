// Branch custom field (see custom_fields.py): only offer enabled branches of the
// document's company, and copy the branch's cost center into the header Cost Center.
// ERPNext's own cost_center handler then copies it to every item row.
for (const doctype of ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"]) {
    frappe.ui.form.on(doctype, {
        setup(frm) {
            frm.set_query("branch", () => ({
                filters: { company: frm.doc.company, disabled: 0 },
            }));
        },

        async branch(frm) {
            if (!frm.doc.branch || !frm.fields_dict.cost_center) return;

            const { message } = await frappe.db.get_value("Branch", frm.doc.branch, "cost_center");
            if (message?.cost_center) frm.set_value("cost_center", message.cost_center);
        },
    });
}
