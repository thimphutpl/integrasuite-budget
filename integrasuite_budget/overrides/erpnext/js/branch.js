// Branch custom field (see custom_fields.py): only offer enabled branches of the
// document's company, and copy the branch's cost center into the header Cost Center.
// ERPNext's own cost_center handler then copies it to every item row.

// Wrapped so its declarations don't clash when several of these forms load the file.
(function () {
    // Item link fields that mean the document was made from an earlier step of MR -> PO -> PR -> PI.
    // Branch then comes from that document and is locked.
    const SOURCE_LINKS = {
        "Purchase Order": ["material_request"],
        "Purchase Receipt": ["purchase_order", "material_request"],
        "Purchase Invoice": ["purchase_order", "purchase_receipt"],
        "Stock Entry": ["material_request"],
    };

    async function set_cost_center_from_branch(frm) {
        if (!frm.doc.branch || !frm.fields_dict.cost_center) return;

        const { message } = await frappe.db.get_value("Branch", frm.doc.branch, "cost_center");
        if (message?.cost_center) await frm.set_value("cost_center", message.cost_center);
        sync_stock_entry_rows(frm);
    }

    // Stock Entry rows start with the company default cost center, so ERPNext's "fill empty rows"
    // never applies. Point every row at the header's (the server enforces the same on validate,
    // see stock/doctype/stock_entry.py).
    function sync_stock_entry_rows(frm) {
        if (frm.doctype !== "Stock Entry" || !frm.doc.cost_center || frm.doc.docstatus !== 0) return;

        for (const row of frm.doc.items || []) {
            if (row.cost_center !== frm.doc.cost_center) {
                frappe.model.set_value(row.doctype, row.name, "cost_center", frm.doc.cost_center);
            }
        }
    }

    function is_from_source(frm) {
        const links = SOURCE_LINKS[frm.doctype] || [];
        return (frm.doc.items || []).some((item) => links.some((link) => item[link]));
    }

    for (const doctype of ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Stock Entry"]) {
        frappe.ui.form.on(doctype, {
            setup(frm) {
                frm.set_query("branch", () => ({
                    filters: { company: frm.doc.company, disabled: 0 },
                }));
            },

            refresh(frm) {
                // A mapped document whose source had no cost center yet still gets the branch's one.
                if (frm.is_new() && frm.doc.branch && !frm.doc.cost_center) set_cost_center_from_branch(frm);
                // A Stock Entry made from an MR arrives with the header set but rows on the default.
                else if (frm.is_new()) sync_stock_entry_rows(frm);

                // Cost Center is always read-only (property_setters.py); only Branch needs locking here.
                // Never lock an empty Branch, or the mandatory field could not be filled in.
                frm.set_df_property("branch", "read_only", is_from_source(frm) && frm.doc.branch ? 1 : 0);
            },

            branch: set_cost_center_from_branch,
        });
    }
})();
