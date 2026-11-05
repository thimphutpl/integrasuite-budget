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
