// Supplier Invoice No (bill_no) comes from the linked Purchase Receipt's Supplier Invoice No
// (supplier_delivery_note). When set there it is read-only here; otherwise the user enters it.
// Keep in sync with get_supplier_invoice_no_from_receipts in supplier_invoice_no.py,
// which also enforces it on save.

// Wrapped so its declarations don't clash with other scripts loaded into the form.
(function () {
    async function sync_bill_no_from_purchase_receipt(frm) {
        if (frm.doc.docstatus !== 0) return;

        const receipts = [...new Set((frm.doc.items || []).map((d) => d.purchase_receipt).filter(Boolean))];
        let supplier_invoice_no = "";
        if (receipts.length) {
            const rows = await frappe.db.get_list("Purchase Receipt", {
                filters: { name: ["in", receipts], supplier_delivery_note: ["is", "set"] },
                fields: ["supplier_delivery_note"],
                limit: receipts.length,
            });
            supplier_invoice_no = [...new Set(rows.map((r) => (r.supplier_delivery_note || "").trim()).filter(Boolean))].join(", ");
        }

        frm.set_df_property("bill_no", "read_only", supplier_invoice_no ? 1 : 0);
        if (supplier_invoice_no && frm.doc.bill_no !== supplier_invoice_no) {
            frm.set_value("bill_no", supplier_invoice_no);
        }
    }

    frappe.ui.form.on("Purchase Invoice", {
        refresh: sync_bill_no_from_purchase_receipt,
        items_remove: sync_bill_no_from_purchase_receipt,
    });

    frappe.ui.form.on("Purchase Invoice Item", {
        purchase_receipt: (frm) => sync_bill_no_from_purchase_receipt(frm),
    });
})();
