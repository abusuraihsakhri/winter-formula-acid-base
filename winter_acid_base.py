#!/usr/bin/env python3
"""Winter's formula and optional anion-gap calculations.

Clinical interpretation aid, not a diagnosis or treatment recommendation.
All partial pressures are in mmHg, electrolytes in mmol/L (mEq/L for these
monovalent electrolytes), and albumin in g/dL.
"""
import argparse
import csv
import json
import math
from pathlib import Path


OUTPUT_FIELDS = (
    "expected_pco2", "expected_pco2_low", "expected_pco2_high",
    "respiratory_interpretation", "anion_gap", "corrected_anion_gap",
    "delta_ratio",
)


def _number(name, value, minimum, maximum):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(result) or not minimum < result <= maximum:
        raise ValueError(f"{name} must be finite and > {minimum} and <= {maximum}")
    return result


def calculate_metrics(*, hco3=None, pco2=None, sodium=None, chloride=None,
                      albumin=None, **extra):
    """Calculate expected PaCO2 = 1.5 * HCO3 + 8 (+/- 2).

    This compensation estimate applies to metabolic acidosis; bicarbonate
    alone does not establish the primary acid-base disorder. Optional anion
    gap uses Na - (Cl + HCO3) without potassium, corrected to albumin 4 g/dL.
    Delta ratio uses a reference AG of 12 and reference HCO3 of 24.
    """
    if extra:
        raise ValueError("Unknown parameters: " + ", ".join(sorted(extra)))
    if hco3 is None or hco3 == "":
        raise ValueError("hco3 is required")
    bicarb = _number("hco3", hco3, 0, 60)
    observed = None if pco2 is None or pco2 == "" else _number("pco2", pco2, 0, 150)

    if (sodium is None or sodium == "") != (chloride is None or chloride == ""):
        raise ValueError("sodium and chloride must be provided together")
    if albumin is not None and albumin != "" and (sodium is None or sodium == ""):
        raise ValueError("albumin requires sodium and chloride")

    expected = 1.5 * bicarb + 8
    low, high = expected - 2, expected + 2
    if bicarb >= 24:
        interpretation = "Not applicable: metabolic acidosis not established"
    elif observed is None:
        interpretation = "Observed PaCO2 not provided"
    elif observed < low:
        interpretation = "Lower than expected: additional respiratory alkalosis possible"
    elif observed > high:
        interpretation = "Higher than expected: additional respiratory acidosis possible"
    else:
        interpretation = "Within expected compensatory range"

    ag = corrected_ag = delta_ratio = None
    if sodium is not None and sodium != "":
        na = _number("sodium", sodium, 0, 250)
        cl = _number("chloride", chloride, 0, 220)
        ag = na - cl - bicarb
        alb = 4.0 if albumin is None or albumin == "" else _number("albumin", albumin, 0, 8)
        corrected_ag = ag + 2.5 * (4.0 - alb)
        if bicarb < 24 and corrected_ag > 12:
            delta_ratio = (corrected_ag - 12) / (24 - bicarb)

    def rounded(value):
        return None if value is None else round(value, 2)

    return {
        "expected_pco2": rounded(expected),
        "expected_pco2_low": rounded(low),
        "expected_pco2_high": rounded(high),
        "respiratory_interpretation": interpretation,
        "anion_gap": rounded(ag),
        "corrected_anion_gap": rounded(corrected_ag),
        "delta_ratio": rounded(delta_ratio),
    }


def process_single(args):
    result = calculate_metrics(
        hco3=args.hco3, pco2=args.pco2, sodium=args.sodium,
        chloride=args.chloride, albumin=args.albumin,
    )
    print(json.dumps(result, indent=2))


def _csv_safe(value):
    """Prevent formula execution when CSV is opened in spreadsheet software."""
    s = str(value)
    if s.lstrip().startswith(("=", "+", "-", "@")) and not _is_plain_number(s):
        return "'" + s
    return s


def _is_plain_number(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def process_batch(input_csv, output_csv):
    source = Path(input_csv)
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = list(reader.fieldnames or [])
        if not headers:
            raise ValueError("Input CSV is empty or has no headers")
        if "hco3" not in headers:
            raise ValueError("Input CSV must include hco3")
        if any(key in OUTPUT_FIELDS for key in headers):
            raise ValueError("Input CSV contains reserved output column names")
        rows = list(reader)

    output_rows = []
    for idx, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"Row {idx}: more values than header columns")
        try:
            result = calculate_metrics(**{
                key: row.get(key) for key in ("hco3", "pco2", "sodium", "chloride", "albumin")
            })
        except ValueError as exc:
            raise ValueError(f"Row {idx}: {exc}") from exc
        output_rows.append({**{key: _csv_safe(value or "") for key, value in row.items()}, **result})

    with open(output_csv, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers + list(OUTPUT_FIELDS))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Processed {len(output_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Winter's formula: metabolic acidosis compensation")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Calculate one case")
    single.add_argument("--hco3", "--v1", type=float, required=True, help="Bicarbonate, mmol/L")
    single.add_argument("--pco2", "--v2", type=float, help="Observed arterial PaCO2, mmHg")
    single.add_argument("--sodium", type=float, help="Serum sodium, mmol/L")
    single.add_argument("--chloride", type=float, help="Serum chloride, mmol/L")
    single.add_argument("--albumin", type=float, help="Albumin, g/dL")
    batch = commands.add_parser("batch", help="Calculate cases from CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            process_single(args)
        else:
            process_batch(args.input, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
