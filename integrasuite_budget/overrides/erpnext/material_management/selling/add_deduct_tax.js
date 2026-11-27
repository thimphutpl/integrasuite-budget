// Add or Deduct on selling tax rows. Server side and the full story: add_deduct_tax.py.
//
// ERPNext's browser totals already honour add_deduct_tax on any doctype, except one spot in
// erpnext.taxes_and_totals.calculate_taxes: the per-item running total (used by later
// "On Previous Row Total" rows) only negates rows that have a `category`, which only buying rows
// have. Monkey-patch (no hook exists): while calculate_taxes runs, selling Deduct rows get a
// temporary category "Total", which that code treats exactly like a plain row.
//
// Loaded for several selling doctypes, so everything is registered only once.

if (!window.__integrasuite_budget_add_deduct_tax) {
	window.__integrasuite_budget_add_deduct_tax = true;

	const proto = erpnext.taxes_and_totals.prototype;
	const original_calculate_taxes = proto.calculate_taxes;

	proto.calculate_taxes = function (...args) {
		const rows = (this.frm.doc.taxes || []).filter(
			(tax) =>
				tax.doctype === "Sales Taxes and Charges" &&
				tax.add_deduct_tax === "Deduct" &&
				!tax.category
		);
		rows.forEach((tax) => (tax.category = "Total"));
		try {
			return original_calculate_taxes.apply(this, args);
		} finally {
			rows.forEach((tax) => delete tax.category);
		}
	};

	// Buying has this trigger in its controller; selling does not.
	frappe.ui.form.on("Sales Taxes and Charges", {
		add_deduct_tax(frm) {
			frm.cscript.calculate_taxes_and_totals();
		},
	});
}
