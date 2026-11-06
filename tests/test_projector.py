import time

import numpy as np
import pytest

from projection.plane import Plane
from projection.projector import Projector, RowLoopProjector
from projection.sampler import NearestSampler, Sampler

rng = np.random.default_rng(0)
M = rng.integers(1, 256, (60, 70, 80), dtype=np.uint8)  # no zeros, so "sampled" is visible in E


@pytest.fixture
def projector():
    return Projector(NearestSampler())


def test_oracle_axis_aligned_rectangle(projector):
    """A rectangle in the plane z = k must give exactly the slice M[:, :, k]."""
    k, n, m = 33, 50, 60
    E, mask = projector.project(M, Plane.from_trapezoid((0, 0, k), (n, 0, k), (0, m, k), (n, m, k)))
    assert np.array_equal(E, M[:n + 1, :m + 1, k])
    assert mask.all()


def test_output_size(projector):
    plane = Plane.from_triangle((0, 30, 5), (40.5, 0, 5), (40.5, 60, 5))
    height, width = Projector.output_size(plane)
    E, mask = projector.project(M, plane)
    assert E.shape == mask.shape == (height, width)
    assert height == int(np.floor(np.hypot(40.5, 30))) + 1
    assert width == 61


def test_apex_is_sampled(projector):
    k = 10
    E, mask = projector.project(M, Plane.from_triangle((0, 30, k), (40, 0, k), (40, 60, k)))
    assert mask[0].nonzero()[0].tolist() == [30]
    assert E[0, 30] == M[0, 30, k]


def test_triangle_rows_are_centered(projector):
    E, mask = projector.project(M, Plane.from_triangle((0, 30, 10), (40, 0, 10), (40, 60, 10)))
    for row in mask:
        cols = row.nonzero()[0]
        assert abs((cols[0] + cols[-1]) / 2 - 30) <= 1


def test_plane_outside_volume_is_empty(projector):
    E, mask = projector.project(M, Plane.from_triangle((500, 500, 500), (540, 470, 500), (540, 530, 500)))
    assert not mask.any() and not E.any()


def test_partly_outside(projector):
    E, mask = projector.project(M, Plane.from_trapezoid((-10, 0, 5), (20, 0, 5), (-10, 10, 5), (20, 10, 5)))
    assert not mask[:10].any() and mask[10:].all()


def test_keeps_dtype(projector):
    data = np.ones((5, 5, 5), dtype=np.int32)
    E, _ = projector.project(data, Plane.from_triangle((0, 2, 2), (4, 0, 2), (4, 4, 2)))
    assert E.dtype == np.int32


def test_sampler_is_injected():
    class ConstantSampler(Sampler):
        def sample(self, data, points):
            return np.full(len(points), 7, dtype=data.dtype), np.ones(len(points), dtype=bool)

    E, mask = Projector(ConstantSampler()).project(M, Plane.from_triangle((0, 30, 10), (40, 0, 10), (40, 60, 10)))
    assert set(E[mask].tolist()) == {7}


def test_performance_500_cubed(projector):
    """NFR1: at least 30 fps on a 500^3 volume (average of 50 runs, projection only)."""
    data = rng.integers(0, 256, (500, 500, 500), dtype=np.uint8)
    plane = Plane.from_triangle((250, 0, 250), (0, 499, 250), (500, 499, 250))
    projector.project(data, plane)
    runs = 50
    start = time.perf_counter()
    for _ in range(runs):
        projector.project(data, plane)
    fps = runs / (time.perf_counter() - start)
    print(f"\n{fps:.0f} fps")
    assert fps >= 30


@pytest.mark.parametrize("points", [
    [(0, 30, 10), (40, 0, 10), (40, 60, 10)],
    [(10, 10, 10), (40, 50, 10), (10, 50, 40)],
    [(-20, 35, 40), (80, 0, 40), (80, 70, 40)],
    [(0, 0, 0), (0.4, 0, 0.3), (0, 0.4, 0.3)],
])
def test_matches_row_loop_triangles(points):
    plane = Plane.from_triangle(*points)
    E, mask = Projector(NearestSampler()).project(M, plane)
    E_ref, mask_ref = RowLoopProjector(NearestSampler()).project(M, plane)
    assert np.array_equal(E, E_ref) and np.array_equal(mask, mask_ref)


@pytest.mark.parametrize("points", [
    [(0, 0, 33), (50, 0, 33), (0, 60, 33), (50, 60, 33)],
    [(10, 0, 5), (0, 40, 5), (15, 0, 5), (25, 40, 5)],
    [(0, 10, 0), (50, 0, 70), (0, 50, 0), (50, 60, 70)],
])
def test_matches_row_loop_trapezoids(points):
    plane = Plane.from_trapezoid(*points)
    E, mask = Projector(NearestSampler()).project(M, plane)
    E_ref, mask_ref = RowLoopProjector(NearestSampler()).project(M, plane)
    assert np.array_equal(E, E_ref) and np.array_equal(mask, mask_ref)
