import numpy as np

from projection.plane import EPS


class Projector:
    """Projects a 3D array onto a Plane as a 2D image (FR24 to FR33).
    The sampling method is injected (Strategy, NFR12); file formats are not
    known here, so any 3D array can be projected (NFR11)."""

    def __init__(self, sampler):
        self.sampler = sampler

    def project(self, data, plane):
        """Returns (E, mask): E[y, x] is the image with data's dtype, and mask[y, x]
        is True where the pixel was sampled from inside the volume (used for FR37)."""
        a1, b, a2, c = plane.a1, plane.b, plane.a2, plane.c
        dist_ab = np.linalg.norm(b - a1)
        dist_bc = np.linalg.norm(c - b)
        v1 = (b - a1) / dist_ab
        v2 = (c - a2) / dist_ab

        height = int(np.floor(dist_ab)) + 1
        width = int(np.ceil(dist_bc)) + 1
        E = np.zeros((height, width), dtype=data.dtype)
        mask = np.zeros((height, width), dtype=bool)

        for y in range(height):
            p1 = a1 + y * v1
            p2 = a2 + y * v2
            d12 = np.linalg.norm(p2 - p1)

            if d12 >= EPS:
                dp = (p2 - p1) / d12
                x1 = np.arange(int(np.floor(d12)) + 1)
            else:
                dp = np.zeros(3)
                x1 = np.zeros(1, dtype=int)

            points = p1 + x1[:, None] * dp
            values, inside = self.sampler.sample(data, points)

            x = np.rint(dist_bc / 2 - d12 / 2 + x1).astype(np.intp)
            in_image = (x >= 0) & (x < width)
            E[y, x[in_image]] = values[in_image]
            mask[y, x[in_image]] = inside[in_image]

        return E, mask


if __name__ == "__main__":
    import time

    from projection.plane import Plane
    from projection.sampler import NearestSampler
    from projection.volume import NrrdReader

    volume = NrrdReader.read("MRHead_1.nrrd")
    plane = Plane.from_triangle((128, 20, 65), (20, 230, 65), (236, 230, 65))
    projector = Projector(NearestSampler())

    runs = 50
    start = time.perf_counter()
    for _ in range(runs):
        E, mask = projector.project(volume.data, plane)
    avg = (time.perf_counter() - start) / runs
    print(f"E: {E.shape} {E.dtype}, avg {avg * 1000:.2f} ms, {1 / avg:.1f} fps")
