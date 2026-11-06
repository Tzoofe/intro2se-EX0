from abc import ABC, abstractmethod

import numpy as np


class Sampler(ABC):
    """Strategy for reading volume values at real-valued points (NFR12)."""

    @abstractmethod
    def sample(self, data, points):
        """points: array of shape (n, 3) in voxel index coordinates.
        Returns (values, inside): values has data's dtype and is 0 where the point
        is outside the volume; inside is a bool array marking points inside it."""


class NearestSampler(Sampler):
    """Nearest-neighbor sampling: the value of the voxel at round(p) (FR30, DD9)."""

    def sample(self, data, points):
        idx = np.rint(points).astype(np.intp)
        ix, iy, iz = idx[:, 0], idx[:, 1], idx[:, 2]
        sx, sy, sz = data.shape
        inside = ((ix >= 0) & (ix < sx) &
                  (iy >= 0) & (iy < sy) &
                  (iz >= 0) & (iz < sz))

        values = np.zeros(len(points), dtype=data.dtype)
        values[inside] = data[ix[inside], iy[inside], iz[inside]]
        return values, inside


class TrilinearSampler(Sampler):
    """Trilinear interpolation: a weighted average of the 8 voxels around p, rounded
    to data's type. Smoother than nearest-neighbor, and slower. A point is inside
    when 0 <= p <= size - 1 on every axis, so all 8 voxels exist."""

    def sample(self, data, points):
        upper = np.array(data.shape) - 1
        inside = np.all((points >= 0) & (points <= upper), axis=1)
        p = points[inside]

        lo = np.floor(p).astype(np.intp)
        hi = np.minimum(lo + 1, upper)  # on the last voxel, lo = hi and its weight is 1
        fx, fy, fz = (p - lo).T
        x0, y0, z0 = lo.T
        x1, y1, z1 = hi.T

        def at(x, y, z):
            return data[x, y, z].astype(np.float64)

        result = ((at(x0, y0, z0) * (1 - fz) + at(x0, y0, z1) * fz) * (1 - fy) +
                  (at(x0, y1, z0) * (1 - fz) + at(x0, y1, z1) * fz) * fy) * (1 - fx) + \
                 ((at(x1, y0, z0) * (1 - fz) + at(x1, y0, z1) * fz) * (1 - fy) +
                  (at(x1, y1, z0) * (1 - fz) + at(x1, y1, z1) * fz) * fy) * fx

        values = np.zeros(len(points), dtype=data.dtype)
        values[inside] = np.rint(result).astype(data.dtype)
        return values, inside


if __name__ == "__main__":
    data = np.arange(27, dtype=np.uint8).reshape(3, 3, 3)
    points = np.array([[0, 0, 0], [1.4, 1.6, 2.2], [2.6, 0, 0], [-1, 0, 0]])
    print(NearestSampler().sample(data, points))
    print(TrilinearSampler().sample(data, points))
