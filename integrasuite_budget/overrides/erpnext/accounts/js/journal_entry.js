$.extend(erpnext.journal_entry, {
    update_account_dimensions: async function (frm) {
        let cost_center = "";

        if (frm.doc.branch) {
            const response = await frappe.db.get_value(
                "Branch",
                frm.doc.branch,
                "cost_center"
            );

            cost_center = response.message?.cost_center || "";
        }

        for (const row of frm.doc.accounts || []) {
            await frappe.model.set_value(
                row.doctype,
                row.name,
                "branch",
                frm.doc.branch || ""
            );

            await frappe.model.set_value(
                row.doctype,
                row.name,
                "cost_center",
                cost_center
            );
        }

        frm.refresh_field("accounts");
    }
});

frappe.ui.form.on("Journal Entry", {
    setup(frm) {
        // Filter parent Branch by company and enabled status
        frm.set_query("branch", () => ({
            filters: {
                company: frm.doc.company,
                disabled: 0
            }
        }));

        // Filter child-row Branch by its Cost Center
        frm.set_query("branch", "accounts", (doc, cdt, cdn) => {
            const row = locals[cdt][cdn];

            return {
                filters: {
                    company: frm.doc.company,
                    cost_center: row.cost_center || "",
                    disabled: 0
                }
            };
        });
    },

    branch(frm) {
        return erpnext.journal_entry.update_account_dimensions(frm);
    },
    apply_tds: function (frm) {
        // Remove TDS account rows
        erpnext.journal_entry.remove_tax_withholding(frm);
      
    },
    tax_withholding_category: function (frm) {
        if (!frm.doc.tax_withholding_category) {
            erpnext.journal_entry.remove_tax_withholding(frm);
            return;
        }
    }
});

// erpnext.journal_entry.remove_tax_withholding = function (frm) {
// 	let tds_amount = 0;

// 	// Get TDS amount BEFORE clearing the table
// 	(frm.doc.tax_withholding_entries || []).forEach(function (row) {
// 		tds_amount += flt(row.withholding_amount);
// 	});

// 	// Remove TDS account rows
// 	frm.doc.accounts = (frm.doc.accounts || []).filter(function (row) {
// 		return !cint(row.is_tax_withholding_account);
// 	});

// 	// Find party account
// 	let party_row = (frm.doc.accounts || []).find(function (row) {
// 		return row.party_type && row.party;
// 	});

// 	if (party_row && tds_amount) {
// 		if (party_row.party_type === "Supplier") {
// 			// Supplier remains at gross amount
// 			// Example:
// 			// Supplier Dr 1000
// 			// Cash     Cr 980
// 			// TDS      Cr 20
// 			//
// 			// After removing TDS:
// 			// Supplier Dr 1000
// 			// Cash     Cr 1000

// 			let cash_row = (frm.doc.accounts || []).find(function (row) {
// 				return row.account && !row.party_type;
// 			});

// 			if (cash_row) {
// 				frappe.model.set_value(
// 					cash_row.doctype,
// 					cash_row.name,
// 					"credit",
// 					flt(cash_row.credit) + tds_amount
// 				);

// 				frappe.model.set_value(
// 					cash_row.doctype,
// 					cash_row.name,
// 					"credit_in_account_currency",
// 					flt(cash_row.credit_in_account_currency) + tds_amount
// 				);
// 			}
// 		}

// 		if (party_row.party_type === "Customer") {
//             let payment_row = (frm.doc.accounts || []).find(function (row) {
//                 return row.account && !row.party_type;
//             });

//             if (payment_row) {
//                 // Customer:
//                 // Debtors Cr 1000
//                 // Cash    Dr 950
//                 // TCS     Dr 50
//                 //
//                 // After removing TCS:
//                 // Debtors Cr 1000
//                 // Cash    Dr 1000

//                 frappe.model.set_value(
//                     payment_row.doctype,
//                     payment_row.name,
//                     "debit",
//                     flt(payment_row.debit) + tds_amount
//                 );

//                 frappe.model.set_value(
//                     payment_row.doctype,
//                     payment_row.name,
//                     "debit_in_account_currency",
//                     flt(payment_row.debit_in_account_currency) + tds_amount
//                 );
//             }
//         }
// 	}

// 	frm.set_value("tax_withholding_category", "");
// 	frm.set_value("tax_withholding_group", "");
// 	frm.set_value("ignore_tax_withholding_threshold", 0);
// 	frm.set_value("override_tax_withholding_entries", 0);
//     frm.cscript.update_totals(frm.doc);
// 	frm.refresh_field("accounts");
// 	frm.refresh_field("tax_withholding_entries");
// };

erpnext.journal_entry.remove_tax_withholding = function (frm) {
    const accounts = frm.doc.accounts || [];

    // Capture TDS rows BEFORE removing them.
    const tds_rows = accounts.filter(
        row => cint(row.is_tax_withholding_account)
    );

    // Get the TDS amount from account rows first.
    let tds_amount = tds_rows.reduce(function (total, row) {
        return total + Math.abs(
            flt(row.credit) - flt(row.debit)
        );
    }, 0);

    // Fallback to withholding entries if no TDS account row exists.
    if (!tds_amount) {
        tds_amount = (frm.doc.tax_withholding_entries || []).reduce(
            function (total, row) {
                return total + flt(row.withholding_amount);
            },
            0
        );
    }

    // Identify the party row before modifying the accounts.
    const party_row = accounts.find(
        row => row.party_type && row.party
    );

    // Remove TDS account rows.
    frm.doc.accounts = accounts.filter(
        row => !cint(row.is_tax_withholding_account)
    );

    // Restore the amount to the counter-account.
    if (party_row && tds_amount) {
        let counter_row;

        if (party_row.party_type === "Supplier") {
            // Supplier: Party Dr 1000, Cash Cr 980, TDS Cr 20.
            // After removing TDS, Cash Cr must become 1000.
            counter_row = frm.doc.accounts.find(
                row =>
                    row.account &&
                    !row.party_type &&
                    flt(row.credit) > 0
            );

            if (counter_row) {
                frappe.model.set_value(
                    counter_row.doctype,
                    counter_row.name,
                    "credit",
                    flt(counter_row.credit) + tds_amount
                );

                frappe.model.set_value(
                    counter_row.doctype,
                    counter_row.name,
                    "credit_in_account_currency",
                    flt(counter_row.credit_in_account_currency) +
                        tds_amount
                );
            }
        } else if (party_row.party_type === "Customer") {
            // Customer: Party Cr 1000, Cash Dr 950, TCS Dr 50.
            // After removing TCS, Cash Dr must become 1000.
            counter_row = frm.doc.accounts.find(
                row =>
                    row.account &&
                    !row.party_type &&
                    flt(row.debit) > 0
            );

            if (counter_row) {
                frappe.model.set_value(
                    counter_row.doctype,
                    counter_row.name,
                    "debit",
                    flt(counter_row.debit) + tds_amount
                );

                frappe.model.set_value(
                    counter_row.doctype,
                    counter_row.name,
                    "debit_in_account_currency",
                    flt(counter_row.debit_in_account_currency) +
                        tds_amount
                );
            }
        }
    }

    // Clear withholding details.
    frm.doc.tax_withholding_entries = [];

    frm.set_value("tax_withholding_category", "");
    frm.set_value("tax_withholding_group", "");
    frm.set_value("ignore_tax_withholding_threshold", 0);
    frm.set_value("override_tax_withholding_entries", 0);

    frm.refresh_field("accounts");
    frm.refresh_field("tax_withholding_entries");

    frm.cscript.update_totals(frm.doc);
};
