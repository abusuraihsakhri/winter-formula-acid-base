/* Browser-side calculation; same parameters and clinical limits as winter_acid_base.py. */
(function (root) {
  "use strict";
  function number(name, value, upper) {
    const n = Number(value);
    if (value === "" || value === null || value === undefined ||
        !Number.isFinite(n) || n <= 0 || n > upper) {
      throw new Error(name + " must be a finite number above 0 and at most " + upper + ".");
    }
    return n;
  }
  function optional(value) {
    return value === "" || value === null || value === undefined;
  }
  function round2(value) {
    return value === null ? null : Math.round((value + Number.EPSILON) * 100) / 100;
  }
  function calculateMetrics(inputs) {
    const hco3 = number("HCO3", inputs.hco3, 60);
    const pco2 = optional(inputs.pco2) ? null : number("PaCO2", inputs.pco2, 150);
    const hasNa = !optional(inputs.sodium);
    const hasCl = !optional(inputs.chloride);
    if (hasNa !== hasCl) throw new Error("Sodium and chloride must be entered together.");
    if (!optional(inputs.albumin) && !hasNa) {
      throw new Error("Albumin correction requires sodium and chloride.");
    }
    const expected = 1.5 * hco3 + 8;
    const low = expected - 2, high = expected + 2;
    let interpretation;
    if (hco3 >= 24) interpretation = "Not applicable: metabolic acidosis not established";
    else if (pco2 === null) interpretation = "Observed PaCO2 not provided";
    else if (pco2 < low) interpretation = "Lower than expected: additional respiratory alkalosis possible";
    else if (pco2 > high) interpretation = "Higher than expected: additional respiratory acidosis possible";
    else interpretation = "Within expected compensatory range";
    let ag = null, adjusted = null, ratio = null;
    if (hasNa) {
      const na = number("Sodium", inputs.sodium, 250);
      const cl = number("Chloride", inputs.chloride, 220);
      const albumin = optional(inputs.albumin) ? 4 : number("Albumin", inputs.albumin, 8);
      ag = na - cl - hco3;
      adjusted = ag + 2.5 * (4 - albumin);
      if (hco3 < 24 && adjusted > 12) ratio = (adjusted - 12) / (24 - hco3);
    }
    return {
      expected_pco2: round2(expected),
      expected_pco2_low: round2(low),
      expected_pco2_high: round2(high),
      respiratory_interpretation: interpretation,
      anion_gap: round2(ag),
      corrected_anion_gap: round2(adjusted),
      delta_ratio: round2(ratio)
    };
  }
  root.calculateMetrics = calculateMetrics;
})(typeof window !== "undefined" ? window : globalThis);
