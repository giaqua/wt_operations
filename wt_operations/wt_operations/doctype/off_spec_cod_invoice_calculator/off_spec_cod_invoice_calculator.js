// Copyright (c) 2026, Takamol and contributors
// For license information, please see license.txt

frappe.ui.form.on("Off-Spec COD Invoice Calculator", {
    cod: function(frm) {
        calculate_daily_off_spec(frm);
    },
    inlet_treated_vol: function(frm) {
        calculate_daily_off_spec(frm);
    },
    contractual_cod_baseline_m1ppm: function(frm) {
        calculate_daily_off_spec(frm);
    },
    refresh: function(frm) {
        calculate_daily_off_spec(frm);
    }
});

function calculate_daily_off_spec(frm) {
    let cod = flt(frm.doc.cod);
    let inlet_vol = flt(frm.doc.inlet_treated_vol);
    let baseline = flt(frm.doc.contractual_cod_baseline_m1ppm);

    if (!cod || !inlet_vol || !baseline) {
        frm.set_value('daily_off_spec', 0);
        return;
    }

    // Find matching tier from child table
    let matched_tier = null;
    (frm.doc.tier_tariff_structure || []).forEach(row => {
        if (cod >= row.cod_range_start && cod <= row.cod_range_end) {
            matched_tier = row;
        }
    });

    if (!matched_tier) {
        frappe.show_alert({
            message: __('No matching tier found for COD value: {0}', [cod]),
            indicator: 'orange'
        });
        frm.set_value('daily_off_spec', 0);
        return;
    }

    let tier_tariff = flt(matched_tier.tier_tariff) * flt(matched_tier.premium);
    let daily_off_spec = (inlet_vol * (cod / baseline) * tier_tariff) - (inlet_vol * tier_tariff);

    frm.set_value('daily_off_spec', daily_off_spec);
};
