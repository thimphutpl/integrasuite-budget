integrasuite_budget.hide_buttons("Purchase Invoice", {
    groups: [__("Get Items From")],
});

frappe.ui.form.on("Purchase Invoice", {
    // Liquidated Damages: 0.1% of grand total per day late, capped at 100 days (10%).
    // Keep in sync with LD_RATE_PER_DAY / LD_MAX_DAYS in accounts/doctype/purchase_invoice.py.
    // Setting write_off_amount triggers ERPNext's outstanding amount recalculation.
    ld_days: async function (frm) {
        const days = cint(frm.doc.ld_days);
        const amount = days > 0 ? flt(((Math.min(days, 100) * 0.1) / 100) * flt(frm.doc.grand_total), 2) : 0;

        if (amount && !frm.doc.write_off_account && frm.doc.company) {
            const { message } = await frappe.db.get_value("Company", frm.doc.company, "write_off_account");
            if (message?.write_off_account) {
                await frm.set_value("write_off_account", message.write_off_account);
            }
        }
        frm.set_value("write_off_amount", amount);
    },
});

// Supplier Invoice No (bill_no) comes from the linked Purchase Receipt's Supplier Invoice No
// (supplier_delivery_note). When set there it is read-only here; otherwise the user enters it.
// Keep in sync with get_supplier_invoice_no_from_receipts in accounts/doctype/purchase_invoice.py,
// which also enforces it on save.
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
