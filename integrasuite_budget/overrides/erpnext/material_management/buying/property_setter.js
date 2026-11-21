// Buying forms (MR -> PO -> PR -> PI): ERPNext buttons we don't use, see utils/hide_buttons.js.
// This one file is loaded into every buying form; hide_buttons sets each doctype up only once.

integrasuite_budget.hide_buttons("Material Request", {
    labels: [__("Request for Quotation"), __("Supplier Quotation")],
    groups: [__("Get Items From")],
});

integrasuite_budget.hide_buttons("Purchase Order", {
    labels: [__("Update Items"), __("Payment Request")],
    groups: [__("Get Items From"), __("Tools")],
});

integrasuite_budget.hide_buttons("Purchase Receipt", {
    labels: [__("Landed Cost Voucher"), __("Sample Retention Stock Entry")],
    groups: [__("Get Items From")],
});

integrasuite_budget.hide_buttons("Purchase Invoice", {
    labels: [__("Payment Request")],
    groups: [__("Get Items From")],
});
