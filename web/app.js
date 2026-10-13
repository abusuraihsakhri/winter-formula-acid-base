"use strict";
const form = document.getElementById("calculator-form");
const error = document.getElementById("error");
const results = document.getElementById("results");
const empty = document.getElementById("empty-result");
const names = ["hco3", "pco2", "sodium", "chloride", "albumin"];

function showResult() {
  error.textContent = "";
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  const inputs = Object.fromEntries(names.map(name => [name, document.getElementById(name).value.trim()]));
  try {
    const result = calculateMetrics(inputs);
    const display = value => value === null ? "—" : String(value);
    document.getElementById("expected").textContent = display(result.expected_pco2);
    document.getElementById("interval").textContent =
      display(result.expected_pco2_low) + "–" + display(result.expected_pco2_high);
    document.getElementById("interpretation").textContent = result.respiratory_interpretation;
    document.getElementById("anion-gap").textContent = display(result.anion_gap);
    document.getElementById("corrected-gap").textContent = display(result.corrected_anion_gap);
    document.getElementById("delta-ratio").textContent = display(result.delta_ratio);
    results.hidden = false;
    empty.hidden = true;
  } catch (err) {
    results.hidden = true;
    empty.hidden = false;
    error.textContent = err instanceof Error ? err.message : "Calculation failed.";
  }
}
form.addEventListener("submit", event => {
  event.preventDefault();
  showResult();
});
form.addEventListener("reset", () => {
  error.textContent = "";
  results.hidden = true;
  empty.hidden = false;
});
document.getElementById("example").addEventListener("click", () => {
  Object.entries({ hco3: 12, pco2: 26, sodium: 140, chloride: 100, albumin: 4 })
    .forEach(([id, value]) => { document.getElementById(id).value = value; });
  showResult();
});
