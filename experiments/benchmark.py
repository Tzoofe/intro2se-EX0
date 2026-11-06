"""Measures projection speed (NFR1 to NFR3): projection step only, average of 50 runs.
Compares Projector (vectorized) with RowLoopProjector (one Python loop per row), and
NearestSampler with TrilinearSampler (speed, and how different the images are).

Run from the project root: python -m experiments.benchmark"""
import os
import platform
import time

import numpy as np

from projection.plane import Plane
from projection.projector import Projector, RowLoopProjector
from projection.normalizer import Normalizer
from projection.sampler import NearestSampler, TrilinearSampler
from projection.volume import NrrdReader

RUNS = 50
DATASETS = ["MRHead_1", "onion", "biscuit_cake", "swiss_roll"]


def fps(projector, data, plane):
    projector.project(data, plane)  # warm-up
    start = time.perf_counter()
    for _ in range(RUNS):
        projector.project(data, plane)
    return RUNS / (time.perf_counter() - start)


def compare(name, data, planes):
    fast = Projector(NearestSampler())
    loop = RowLoopProjector(NearestSampler())
    for plane_name, plane in planes:
        h, w = Projector.output_size(plane)
        f_loop = fps(loop, data, plane)
        f_fast = fps(fast, data, plane)
        print(f"| {name} | {plane_name} | {h}x{w} | {f_loop:.0f} | {f_fast:.0f} | {f_fast / f_loop:.1f}x |")


def compare_samplers(name, volume, plane):
    nearest = Projector(NearestSampler())
    trilinear = Projector(TrilinearSampler())
    normalizer = Normalizer(volume.min_value, volume.max_value)
    E_n, mask_n = nearest.project(volume.data, plane)
    E_t, mask_t = trilinear.project(volume.data, plane)
    both = mask_n & mask_t
    diff = np.abs(normalizer.normalize(E_n, both).astype(int) - normalizer.normalize(E_t, both).astype(int))
    f_n = fps(nearest, volume.data, plane)
    f_t = fps(trilinear, volume.data, plane)
    print(f"| {name} | {f_n:.0f} | {f_t:.0f} | {diff[both].mean():.2f} | {diff[both].max()} |")


def main():
    print(f"Machine: {platform.machine()}, {platform.system()} {platform.release()}, "
          f"Python {platform.python_version()}, NumPy {np.__version__}\n")
    print("| Volume | Plane | Output HxW | Row loop fps | Vectorized fps | Speed-up |")
    print("|---|---|---|---|---|---|")

    data = np.random.default_rng(0).integers(0, 256, (500, 500, 500), dtype=np.uint8)
    compare("synthetic 500³ uint8", data, [
        ("triangle, axis-aligned", Plane.from_triangle((250, 0, 250), (0, 499, 250), (500, 499, 250))),
        ("triangle, oblique", Plane.from_triangle((250, 0, 0), (0, 499, 499), (500, 499, 499))),
        ("rectangle, axis-aligned", Plane.from_trapezoid((0, 0, 250), (499, 0, 250), (0, 499, 250), (499, 499, 250))),
        ("rectangle, oblique 45°", Plane.from_trapezoid((0, 0, 0), (499, 0, 0), (0, 353, 353), (499, 353, 353))),
    ])

    head_planes = [
        ("triangle, axis-aligned", Plane.from_triangle((127.5, 0, 65), (0, 255, 65), (255, 255, 65))),
        ("rectangle, oblique 45°", Plane.from_trapezoid((0, 37.5, 19.5), (255, 37.5, 19.5), (0, 218.5, 110.5), (255, 218.5, 110.5))),
    ]
    for name in DATASETS:
        path = f"data/{name}.nrrd"
        if not os.path.exists(path):
            print(f"| {name} | missing {path} | | | | |")
            continue
        compare(name, NrrdReader.read(path).data, head_planes)

    print("\nNearest vs trilinear, oblique 45° rectangle; difference in 8-bit gray levels (0 to 255):\n")
    print("| Volume | Nearest fps | Trilinear fps | Mean difference | Max difference |")
    print("|---|---|---|---|---|")
    for name in DATASETS:
        path = f"data/{name}.nrrd"
        if os.path.exists(path):
            compare_samplers(name, NrrdReader.read(path), head_planes[1][1])


if __name__ == "__main__":
    main()
