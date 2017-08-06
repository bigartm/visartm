import numpy as np
from hamilton_path import HamiltonPath
import matplotlib.pyplot as plt
import time


def generate_matrix_special(N):
    path = np.random.choice(N, N, replace=False)
    X = np.zeros((N, 3))
    for i in range(N):
        X[path[i]][0] = 10 * i
        X[path[i]][1] = np.random.normal(scale=5)
        X[path[i]][2] = np.random.normal(scale=5)

    dist = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            dist[i][j] = np.linalg.norm(X[i] - X[j])

    best = 0
    for i in range(N - 1):
        best += dist[path[i]][path[i + 1]]

    return dist, best


def generate_matrix(N):
    dist = np.zeros((N, N))
    for i in range(N):
        for j in range(i + 1, N):
            dist[i][j] = dist[j][i] = np.random.uniform(0, 1)
    return dist


def solve(dist, mode):
    start_time = time.time()
    hp = HamiltonPath(dist)
    print(mode + "...")
    if mode == "LKH":
        hp.solve_lkh()
    elif mode == "annealing":
        hp.solve_annealing(steps=10000000)
    return hp.path_weight(), time.time() - start_time


N_range = range(5, 200)

q_lkh = []
t_lkh = []
t_ann = []

for N in N_range:
    print(N)
    dist = generate_matrix(N)
    weight_lkh, time_lkh = solve(dist, "LKH")
    weight_ann, time_ann = solve(dist, "annealing")
    print(weight_ann / weight_lkh)
    q_lkh.append(weight_ann / weight_lkh)
    t_lkh.append(time_lkh)
    t_ann.append(time_ann)

plt.plot(N_range, q_lkh)
plt.xlabel("N", fontsize=15)
plt.ylabel("NDS(Annealing)/NDS(LKH)", fontsize=15)
plt.savefig("lkh_vs_annealing_quality.eps", bbox_inches='tight')
plt.clf()

plt.plot(N_range, t_lkh, label="LKH")
plt.plot(N_range, t_ann, label="Annealing")
plt.xlabel("N", fontsize=15)
plt.ylabel("Time, s", fontsize=15)
plt.legend(loc='best', fontsize=15)
# plt.show()
plt.savefig("lkh_vs_annealing_time.eps", bbox_inches='tight')
