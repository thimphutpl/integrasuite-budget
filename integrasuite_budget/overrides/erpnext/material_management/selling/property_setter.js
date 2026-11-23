// Selling forms: ERPNext buttons we don't use, see utils/hide_buttons.js.

integrasuite_budget.hide_buttons("Sales Order", {
    labels: [
        __("Update Items"),
        // Create menu: only Delivery Note, Material Request and Payment are kept.
        __("Pick List"),
        __("Work Order"),
        __("Production Plan"),
        __("Sales Invoice"),
        __("Request for Raw Materials"),
        __("Purchase Order"),
        __("Project"),
        __("Payment Request"),
        __("Maintenance Visit"),
        __("Maintenance Schedule"),
        __("Subcontracting Inward Order"),
        __("Internal Purchase Order"),
        __("Inter Company Purchase Order"),
    ],
    groups: [__("Get Items From")],
});

// Delivery Notes and Sales Invoices are made from the Sales Order / Delivery Note itself (Create menu).
for (const doctype of ["Delivery Note", "Sales Invoice"]) {
    integrasuite_budget.hide_buttons(doctype, {
        groups: [__("Get Items From")],
    });
}
