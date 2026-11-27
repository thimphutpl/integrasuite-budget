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
// One call per doctype: hide_buttons ignores later calls for a doctype it has already set up.
integrasuite_budget.hide_buttons("Delivery Note", {
    // Create menu: Shipment and Installation Note are not used.
    labels: [__("Shipment"), __("Installation Note")],
    groups: [__("Get Items From")],
});

integrasuite_budget.hide_buttons("Sales Invoice", {
    groups: [__("Get Items From")],
});
