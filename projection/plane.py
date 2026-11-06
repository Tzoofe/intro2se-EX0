import numpy as np

EPS = 0.001
# Longest allowed leg or base, in voxels (FR42). The longest line inside the largest
# allowed volume (1023^3) is 1023 * sqrt(3) = 1772 voxels, so a longer plane only adds
# empty pixels, and a very long one would not fit in memory.
MAX_SIDE = 2048


class InvalidPlaneError(ValueError):
    """Raised when a set of points does not define a valid plane (FR16 to FR22)."""


def _dist(p, q):
    return np.linalg.norm(q - p)


def _dist_from_line(p, start, end):
    """Distance of point p from the line through start and end."""
    return np.linalg.norm(np.cross(end - start, p - start)) / _dist(start, end)


def _check_size(leg, base):
    if leg > MAX_SIDE or base > MAX_SIDE:
        raise InvalidPlaneError(f"plane too large: leg {leg:.1f}, base {base:.1f} voxels (max {MAX_SIDE})")


class Plane:
    """An isosceles trapezoid (a1, b, a2, c): segments a1->b and a2->c.
    A triangle (a, b, c) is stored as a1 = a2 = a (DD5).
    Use Plane.from_triangle or Plane.from_trapezoid; they validate the points."""

    def __init__(self, a1, b, a2, c):
        self.a1 = a1
        self.b = b
        self.a2 = a2
        self.c = c

    @property
    def is_triangle(self):
        return np.array_equal(self.a1, self.a2)

    @classmethod
    def from_triangle(cls, a, b, c):
        a, b, c = (np.asarray(p, dtype=float) for p in (a, b, c))

        dist_ab = _dist(a, b)
        if dist_ab <= EPS:
            raise InvalidPlaneError(f"degenerate triangle: dist(a,b) = {dist_ab:.4f}")
        if _dist_from_line(c, a, b) <= EPS:
            raise InvalidPlaneError("degenerate triangle: a, b, c are collinear")

        dist_ac = _dist(a, c)
        if abs(dist_ab - dist_ac) >= EPS:
            raise InvalidPlaneError(f"not isosceles: dist(a,b) = {dist_ab:.4f}, dist(a,c) = {dist_ac:.4f}")
        _check_size(dist_ab, _dist(b, c))

        return cls(a, b, a.copy(), c)

    @classmethod
    def from_trapezoid(cls, a1, b, a2, c):
        a1, b, a2, c = (np.asarray(p, dtype=float) for p in (a1, b, a2, c))

        dist_a1b = _dist(a1, b)
        if dist_a1b <= EPS:
            raise InvalidPlaneError(f"degenerate trapezoid: dist(a1,b) = {dist_a1b:.4f}")
        if _dist_from_line(c, a1, b) <= EPS:
            raise InvalidPlaneError("degenerate trapezoid: a1, b, c are collinear")

        dist_a2c = _dist(a2, c)
        if abs(dist_a1b - dist_a2c) >= EPS:
            raise InvalidPlaneError(f"not isosceles: dist(a1,b) = {dist_a1b:.4f}, dist(a2,c) = {dist_a2c:.4f}")

        dist_a1a2 = _dist(a1, a2)
        dist_bc = _dist(b, c)
        _check_size(dist_a1b, dist_bc)
        if dist_a1a2 > dist_bc + EPS:
            raise InvalidPlaneError(f"top base longer than bottom: dist(a1,a2) = {dist_a1a2:.4f} > dist(b,c) = {dist_bc:.4f}")

        normal = np.cross(b - a1, c - a1)
        dist_from_plane = abs(np.dot(a2 - a1, normal)) / np.linalg.norm(normal)
        if dist_from_plane >= EPS:
            raise InvalidPlaneError(f"points not on the same plane: a2 is {dist_from_plane:.4f} from plane (a1, b, c)")

        return cls(a1, b, a2, c)


if __name__ == "__main__":
    print(Plane.from_triangle((128, 20, 100), (20, 230, 100), (236, 230, 100)).is_triangle)
    print(Plane.from_trapezoid((100, 0, 50), (0, 200, 50), (150, 0, 50), (250, 200, 50)).is_triangle)
    try:
        Plane.from_triangle((0, 0, 0), (10, 0, 0), (0, 20, 0))
    except InvalidPlaneError as e:
        print("invalid:", e)
