import pytest

from projection.csv_reader import PlaneCsvReader

HEADER = "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"


def write_csv(tmp_path, text, name="planes.csv", encoding="utf-8"):
    path = tmp_path / name
    path.write_text(text, encoding=encoding)
    return str(path)


def test_sample_csv():
    rows = PlaneCsvReader.read("Ex0.csv")
    assert [row.row_number for row in rows] == [1, 2, 3, 4]
    assert [row.is_valid for row in rows] == [True, True, False, True]
    assert "not isosceles" in rows[2].error


def test_excel_export_format(tmp_path):
    """Excel adds a BOM and uses CRLF line endings."""
    path = write_csv(tmp_path, "﻿" + HEADER + "3,0,0,0,10,0,0,0,10,0,,,\r\n", encoding="utf-8")
    rows = PlaneCsvReader.read(path)
    assert len(rows) == 1 and rows[0].is_valid


@pytest.mark.parametrize("line, reason", [
    ("5,1,2,3", "must be 3 or 4"),
    ("3,1,abc,3,4,5,6,7,8,9", "not a number"),
    ("3,1,,3,4,5,6,7,8,9", "missing value"),
    ("3,1,2,3", "expected 9 coordinates"),
    ("3,0,0,0,10,0,0,0,10,0,99", "expected 9 coordinates"),
    ("3,nan,0,0,10,0,0,0,10,0", "not a finite number"),
    ("3,0,0,0,10,0,0,0,20,0", "not isosceles"),
])
def test_invalid_rows(tmp_path, line, reason):
    rows = PlaneCsvReader.read(write_csv(tmp_path, HEADER + line + "\n"))
    assert not rows[0].is_valid
    assert reason in rows[0].error


def test_decimals_negatives_and_float_n(tmp_path):
    rows = PlaneCsvReader.read(write_csv(tmp_path, HEADER + "3.0,-5.5,0,0,4.5,0,0,-5.5,10,0\n"))
    assert rows[0].is_valid


def test_blank_lines_skipped_but_row_numbers_kept(tmp_path):
    text = HEADER + "3,0,0,0,10,0,0,0,10,0\n\n3,0,0,0,10,0,0,0,10,0\n"
    rows = PlaneCsvReader.read(write_csv(tmp_path, text))
    assert [row.row_number for row in rows] == [1, 3]


def test_header_only(tmp_path):
    with pytest.raises(ValueError, match="no data rows"):
        PlaneCsvReader.read(write_csv(tmp_path, HEADER))


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        PlaneCsvReader.read(str(tmp_path / "missing.csv"))


def test_binary_file(tmp_path):
    path = tmp_path / "planes.csv"
    path.write_bytes(b"PK\x03\x04\x9d\xff\x00binary")
    with pytest.raises(ValueError, match="not a text CSV"):
        PlaneCsvReader.read(str(path))
