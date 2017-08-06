import numpy as np
import time
from crossmin import CrossMinimizer
import matplotlib.pyplot as plt


def cm_test(N1, N2):
    A = np.zeros((N1, N2))
    for i in range((N1 * N2) // 100):
        i1 = np.random.randint(0, N1)
        i2 = np.random.randint(0, N2)
        A[i1][i2] = 1

    cm = CrossMinimizer(A)

    ans = {}
    elapsed = {}
    for mode in [
        "baricenter",
        "median",
        "split",
        "split10",
        "split10N",
            "binopt_fast"]:
        start_time = time.time()
        p = cm.solve(mode=mode)
        elapsed[mode] = time.time() - start_time
        ans[mode] = cm.cross_count(p)
    return ans, elapsed


N1_range = range(5, 101)
# time_chart0 = []
time_chart1 = []
time_chart2 = []
# bf_chart = []
bc_chart = []
md_chart = []
sp_chart = []
# sp10_chart = []
sp10N_chart = []


for N1 in N1_range:
    ans, elapsed = cm_test(N1, 500)
    # time_chart0.append(elapsed["binopt"])
    time_chart1.append(elapsed["binopt_fast"])
    time_chart2.append(elapsed["split10N"])

    # time_chart2.append(elapsed["opt"])

    # bf_chart.append(ans["binopt"]/ ans["binopt_fast"])
    bc_chart.append(ans["baricenter"] / ans["binopt_fast"])
    md_chart.append(ans["median"] / ans["binopt_fast"])
    sp_chart.append(ans["split"] / ans["binopt_fast"])
    # sp10_chart.append(ans["split10"]/ ans["binopt_fast"])
    sp10N_chart.append(ans["split10N"] / ans["binopt_fast"])

    print(N1)


fig = plt.figure(figsize=(8, 5))
ax = fig.gca()
# ax.plot(N1_range, time_chart0, label="Pulp Overall")
ax.plot(N1_range, time_chart1, label="CBC MILP Solver")
ax.plot(N1_range, time_chart2, label="QuickSort-10N")
ax.set_xlabel("N", fontsize=15)
ax.set_ylabel("Time, s", fontsize=15)
ax.set_title("SCC minimizing time", fontsize=15)
lgd = ax.legend(loc='best')
fig.savefig("scc-time.eps", bbox_inches='tight')
fig.show()


fig = plt.figure(figsize=(8, 5))
ax = fig.gca()
# ax.plot(N1_range, bf_chart, label = "Binopt")

ax.plot(N1_range, bc_chart, label="Baricenter")
ax.plot(N1_range, md_chart, label="Median")
ax.plot(N1_range, sp_chart, label="QuickSort")
# ax.plot(N1_range, sp10_chart, label = "Split-10")
ax.plot(N1_range, sp10N_chart, label="QuickSort-10N")

ax.set_xlabel("N", fontsize=15)
ax.set_ylabel("Error", fontsize=15)
ax.set_title("SCC minimizing quality", fontsize=15)
lgd = ax.legend(loc='best')  # , bbox_to_anchor=(1, 0.5))
fig.savefig("scc-quality.eps", bbox_inches='tight')
# fig.show()
