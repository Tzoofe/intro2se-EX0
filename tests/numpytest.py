import numpy as np
steps = np.arange(5)

start = np.array([10, 20, 30])
direction = np.array([1, 0, 0.5])
points = start + steps[:, None] * direction

idx = np.rint(points).astype(int)
ix = idx[:, 0]
iy = idx[:, 1]
iz = idx[:, 2]

values = np.array([5, -2, 8, 300, 1])
mask = (values >= 0) & (values < 100)
print(mask)
print(values[mask])

grid = np.arange(20).reshape(3, 3, 3)
print(grid[[0, 1, 2], [0, 1, 2], [0, 1, 2]])

# print(points)
