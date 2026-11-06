import numpy as np
import pytest

from projection.plane import Plane, InvalidPlaneError


def test_valid_triangle_has_a1_equal_a2():
    plane = Plane.from_triangle((0, 0, 0), (10, 0, 0), (0, 10, 0))
    assert plane.is_triangle
    assert np.array_equal(plane.a1, plane.a2)


def test_valid_trapezoid():
    plane = Plane.from_trapezoid((0, 0, 0), (0, 10, 0), (5, 0, 0), (5, 10, 0))
    assert not plane.is_triangle


def test_tolerance_within_eps_is_valid():
    Plane.from_trapezoid((0, 0, 0), (0, 10, 0), (5, 0, 0), (5, 10.0005, 0))


@pytest.mark.parametrize("points, reason", [
    ([(0, 0, 0), (10, 0, 0), (0, 20, 0)], "not isosceles"),
    ([(0, 0, 0), (0, 0, 0), (0, 0, 0)], "degenerate"),
    ([(0, 0, 0), (10, 0, 0), (-10, 0, 0)], "collinear"),
    ([(0, 0, 0), (10, 0, 0), (0, 10.002, 0)], "not isosceles"),
])
def test_invalid_triangles(points, reason):
    with pytest.raises(InvalidPlaneError, match=reason):
        Plane.from_triangle(*points)


@pytest.mark.parametrize("points, reason", [
    ([(0, 0, 0), (0, 10, 0), (5, 0, 0), (5, 12, 0)], "not isosceles"),
    ([(0, 0, 0), (6, 8, 0), (20, 0, 0), (14, 8, 0)], "top base longer"),
    ([(0, 0, 0), (0, 10, 0), (5, 0, 0), (5, 8, 6)], "not on the same plane"),
    ([(0, 0, 0), (0, 0, 0), (5, 0, 0), (5, 0, 0)], "degenerate"),
    ([(0, 0, 0), (0, 10, 0), (0, 5, 0), (0, 15, 0)], "collinear"),
])
def test_invalid_trapezoids(points, reason):
    with pytest.raises(InvalidPlaneError, match=reason):
        Plane.from_trapezoid(*points)


def test_sample_csv_rows():
    """The sample plane list (Ex0.csv): rows 1, 2, 4 valid, row 3 not isosceles (DD2: order a1, b, a2, c)."""
    Plane.from_triangle((200, 200, 0), (0, 200, 400), (400, 200, 400))
    Plane.from_trapezoid((200, 0, 0), (200, 0, 500), (200, 400, 0), (200, 400, 500))
    with pytest.raises(InvalidPlaneError):
        Plane.from_triangle((200, 200, -30), (-50, 200, 400), (400, 250, 400))
    Plane.from_trapezoid((200, 50, 0), (200, 0, 500), (200, 350, 0), (200, 400, 500))


def test_row4_invalid_in_alternative_order():
    """Row 4 read as (a1, a2, b, c) is not isosceles, which supports DD2."""
    with pytest.raises(InvalidPlaneError):
        Plane.from_trapezoid((200, 50, 0), (200, 350, 0), (200, 0, 500), (200, 400, 500))


def test_largest_plane_is_valid():
    Plane.from_trapezoid((0, 0, 0), (2048, 0, 0), (0, 2048, 0), (2048, 2048, 0))


@pytest.mark.parametrize("make, points", [
    (Plane.from_triangle, [(0, 0, 0), (1e7, 0, 0), (0, 1e7, 0)]),
    (Plane.from_trapezoid, [(0, 0, 0), (2049, 0, 0), (0, 10, 0), (2049, 10, 0)]),
    (Plane.from_trapezoid, [(0, 0, 0), (10, 0, 0), (0, 2049, 0), (10, 2049, 0)]),
])
def test_too_large(make, points):
    """FR42: a plane longer than MAX_SIDE would not fit in memory; it is invalid instead."""
    with pytest.raises(InvalidPlaneError, match="too large"):
        make(*points)
