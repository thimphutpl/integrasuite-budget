// Only offer ledger (non-group) cost centers of the branch's company. Transactions can't
// post to a group cost center, and the branch's one is copied onto MR/PO/PR/PI.
frappe.ui.form.on("Branch", {
    setup(frm) {
        frm.set_query("cost_center", () => ({
            filters: { is_group: 0, ...(frm.doc.company && { company: frm.doc.company }) },
        }));
    },
});
