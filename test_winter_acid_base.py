import csv
import pytest
from winter_acid_base import calculate_metrics, process_batch


def test_winter_single():
    result = calculate_metrics(hco3=12, pco2=26, sodium=140, chloride=100)
    assert result["expected_pco2"] == 26
    assert result["expected_pco2_low"] == 24
    assert result["expected_pco2_high"] == 28
    assert result["respiratory_interpretation"] == "Within expected compensatory range"
    assert result["anion_gap"] == 28
    assert result["delta_ratio"] == 1.33


def test_winter_boundaries():
    assert calculate_metrics(hco3=12, pco2=24)["respiratory_interpretation"] == "Within expected compensatory range"
    assert calculate_metrics(hco3=12, pco2=23.9)["respiratory_interpretation"].startswith("Lower than expected")
    assert calculate_metrics(hco3=12, pco2=28.1)["respiratory_interpretation"].startswith("Higher than expected")
    assert calculate_metrics(hco3=26, pco2=45)["respiratory_interpretation"].startswith("Not applicable")


def test_albumin_correction_and_gap_scope():
    result = calculate_metrics(hco3=12, sodium=140, chloride=100, albumin=2)
    assert result["corrected_anion_gap"] == 33
    assert result["delta_ratio"] == 1.75
    assert calculate_metrics(hco3=18, sodium=135, chloride=110)["delta_ratio"] is None


@pytest.mark.parametrize("kwargs", [
    {}, {"hco3": 0}, {"hco3": float("nan")}, {"hco3": 12, "pco2": float("inf")},
    {"hco3": 12, "sodium": 140}, {"hco3": 12, "albumin": 2},
    {"hco3": 12, "sodium": 140, "chloride": 100, "albumin": -1},
    {"hco3": 12, "extra_field": 50},
])
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate_metrics(**kwargs)


def test_winter_batch(tmp_path):
    path = tmp_path / "cases.csv"
    dest = tmp_path / "results.csv"
    path.write_text("Case_ID,hco3,pco2,sodium,chloride,albumin\n"
                    "A,12,26,140,100,\n"
                    "B,18,27,135,110,2\n", encoding="utf-8")
    process_batch(str(path), str(dest))
    with dest.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["expected_pco2"] == "26.0"
    assert rows[0]["anion_gap"] == "28.0"
    assert rows[1]["respiratory_interpretation"].startswith("Lower than expected")


def test_csv_injection_is_escaped(tmp_path):
    path, dest = tmp_path / "cases.csv", tmp_path / "output.csv"
    path.write_text("Case_ID,hco3,pco2\n=HYPERLINK(\"evil\"),12,25\n")
    process_batch(str(path), str(dest))
    with dest.open(encoding="utf-8", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["Case_ID"].startswith("'=")
