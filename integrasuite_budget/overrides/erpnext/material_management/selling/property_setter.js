// Selling forms: ERPNext buttons we don't use, see utils/hide_buttons.js.

integrasuite_budget.hide_buttons("Sales Order", {
    labels: [__("Update Items")],
    groups: [__("Get Items From")],
});

// Delivery Notes and Sales Invoices are made from the Sales Order / Delivery Note itself (Create menu).
for (const doctype of ["Delivery Note", "Sales Invoice"]) {
    integrasuite_budget.hide_buttons(doctype, {
        groups: [__("Get Items From")],
    });
}
