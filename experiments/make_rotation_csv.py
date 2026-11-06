"""Writes experiments/rotation.csv: a rectangle (4-point plane) rotating 180 degrees
about the volume's first axis, through the center of a 256x256x130 volume.

Run from the project root: python -m experiments.make_rotation_csv"""
import csv
import math

SIZE = (256, 256, 130)
FRAMES = 60
OUT = "experiments/rotation.csv"


def main():
    cy, cz = (SIZE[1] - 1) / 2, (SIZE[2] - 1) / 2
    half = SIZE[1] / 2  # half-width of the rectangle
    top, bottom = 0, SIZE[0] - 1

    with open(OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Number of Points (3 or 4)", "x1", "y1", "z1", "x2", "y2", "z2",
                         "x3", "y3", "z3", "x4", "y4", "z4"])
        for i in range(FRAMES):
            angle = math.pi * i / FRAMES
            dy, dz = half * math.cos(angle), half * math.sin(angle)
            left = (cy - dy, cz - dz)
            right = (cy + dy, cz + dz)
            # order (a1, b, a2, c): legs a1->b and a2->c run along the first axis
            a1 = (top, *left)
            b = (bottom, *left)
            a2 = (top, *right)
            c = (bottom, *right)
            writer.writerow([4] + [round(v, 3) for p in (a1, b, a2, c) for v in p])
    print(f"wrote {FRAMES} planes to {OUT}")


if __name__ == "__main__":
    main()
