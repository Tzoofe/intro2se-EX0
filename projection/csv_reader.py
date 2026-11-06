import csv
import math

from projection.plane import Plane, InvalidPlaneError


class PlaneRow:
    """The result of one CSV data row: a valid Plane, or an error message (FR14, FR22).
    row_number counts data rows from 1 (the header is row 0)."""

    def __init__(self, row_number, plane=None, error=None):
        self.row_number = row_number
        self.plane = plane
        self.error = error

    @property
    def is_valid(self):
        return self.plane is not None


class PlaneCsvReader:
    """Reads a CSV of planes (FR8 to FR15): a header row, then one plane per row:
    N, x1, y1, z1, ..., xN, yN, zN with N = 3 (a, b, c) or N = 4 (a1, b, a2, c)."""

    @staticmethod
    def read(path):
        # utf-8-sig drops the BOM that Excel adds to exported CSV files.
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        results = []
        for row_number, cells in enumerate(rows[1:], start=1):
            cells = [cell.strip() for cell in cells]
            while cells and cells[-1] == "":
                cells.pop()
            if not cells:
                continue  # blank line, not a data row
            results.append(PlaneCsvReader._parse_row(row_number, cells))

        if not results:
            raise ValueError(f"{path}: no data rows")
        return results

    @staticmethod
    def _parse_row(row_number, cells):
        try:
            values = [PlaneCsvReader._to_number(cell) for cell in cells]
        except ValueError as e:
            return PlaneRow(row_number, error=str(e))

        n = values[0]
        if n not in (3, 4):
            return PlaneRow(row_number, error=f"number of points must be 3 or 4, got {cells[0]}")

        coords = values[1:]
        if len(coords) != 3 * n:
            return PlaneRow(row_number, error=f"expected {3 * int(n)} coordinates for {int(n)} points, got {len(coords)}")

        points = [coords[i:i + 3] for i in range(0, len(coords), 3)]
        try:
            if n == 3:
                plane = Plane.from_triangle(*points)
            else:
                plane = Plane.from_trapezoid(*points)
        except InvalidPlaneError as e:
            return PlaneRow(row_number, error=str(e))
        return PlaneRow(row_number, plane=plane)

    @staticmethod
    def _to_number(cell):
        if cell == "":
            raise ValueError("missing value")
        try:
            value = float(cell)
        except ValueError:
            raise ValueError(f"not a number: '{cell}'")
        if not math.isfinite(value):
            raise ValueError(f"not a finite number: '{cell}'")
        return value


if __name__ == "__main__":
    for result in PlaneCsvReader.read("Ex0.csv"):
        if result.is_valid:
            print(f"row {result.row_number}: valid")
        else:
            print(f"row {result.row_number}: {result.error}")
