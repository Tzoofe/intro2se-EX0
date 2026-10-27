import numpy as np
import nrrd
import matplotlib.pyplot as plt
import time


def checkM(M, p):
    """returns M at point p (nearest voxel)"""
    ix, iy, iz = np.rint(p).astype(int)
    if 0 <= ix < M.shape[0] and 0 <= iy < M.shape[1] and 0 <= iz < M.shape[2]:
        return M[ix, iy, iz]
    return 0

def project(M, a, b, c):
    a, b, c = (np.asarray(pt, dtype=float) for pt in (a, b, c))
    DistAB = np.linalg.norm(b - a)
    DistBC = np.linalg.norm(c - b)
    Vab = (b - a) / DistAB
    Vac = (c - a) / DistAB

    height = int(np.ceil(DistAB))
    width = int(np.ceil(DistBC)) + 1
    E = np.zeros((width, height), dtype=M.dtype)
    
    a1 = a.copy()
    a2 = a.copy()

    for y in range(height):
        a1 = a1 + Vab
        a2 = a2 + Vac
        #p = a1.copy()

        Dist12 = np.linalg.norm(a2 - a1)
        dp = (a2 - a1) / Dist12 if Dist12 > 0 else np.zeros(3)

        x1 = np.arange(int(np.floor(Dist12)) + 1)

        points = a1 + x1[:, None] * dp

        idx = np.rint(points).astype(int)
        ix, iy, iz = idx[:, 0], idx[:, 1], idx[:, 2]

        x = np.rint(DistBC / 2 - Dist12 / 2 + x1).astype(int)

        mask = ((ix >= 0) & (ix < M.shape[0])&
                (iy >= 0) & (iy < M.shape[1])&
                (iz >= 0) & (iz < M.shape[2])&
                (x >= 0) & (x < width))
        E[x[mask], y] = M[ix[mask], iy[mask], iz[mask]]

        # for x1 in range(int(np.floor(Dist12)) + 1):
        #     v = checkM(M, p)
        #     x = int(round(DistBC / 2 - Dist12 / 2 + x1))
        #     if 0 <= x < width:
        #         E[x, y] = v
        #     p = p + dp

        
    return E


if __name__ == "__main__":
    M, header = nrrd.read("MRHead_1.nrrd")

    a = (128, 20, 100)
    b = (20, 230, 100)
    c = (236, 230, 100)
    
    start = time.perf_counter()
    E = project(M, a, b, c)
    end = time.perf_counter()

    elapsed = end - start 
    print(f"time elapsed: {elapsed:.3f} seconds")
    print(f"fps: {1 / elapsed:.1f}")


    print(E.shape)

    plt.imshow(E.T, cmap="grey")
    plt.show()