from hamilton_path import HamiltonPath
import numpy as np

N = 20
dist = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        dist[i][j] = np.abs(i - j)


hp = HamiltonPath(dist)
hp.path = [
    1,
    4,
    8,
    9,
    0,
    2,
    3,
    5,
    6,
    7,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19]
hp.clusters = [5, 15]
hp.solve()
print(hp.path)
