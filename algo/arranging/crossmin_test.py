import numpy as np
import time
from crossmin import CrossMinimizer
import matplotlib.pyplot as plt


def cm_test(N1, N2):
    A = np.zeros((N1,N2))
    for i in range(N1*N2//20):
        i1 = np.random.randint(0, N1)
        i2 = np.random.randint(0, N2)
        A[i1][i2]=1
    
    cm = CrossMinimizer(A)
    
    ans = {}
    elapsed = {}
    for mode in ["baricenter", "median", "split", "split10", "binopt"]:
        start_time = time.time()
        p = cm.solve(mode=mode)
        elapsed[mode] = time.time() - start_time
        ans[mode] = cm.cross_count(p)
    return  ans, elapsed


N1_range = range(5,50)
time_chart = []
bc_chart = []
md_chart = []
sp_chart = []
sp10_chart = []

for N1 in N1_range:
    ans, elapsed = cm_test(N1,200)
    time_chart.append(elapsed["binopt"])
    bc_chart.append(ans["baricenter"]/ ans["binopt"])
    md_chart.append(ans["median"]/ ans["binopt"])
    sp_chart.append(ans["split"]/ ans["binopt"])
    sp10_chart.append(ans["split10"]/ ans["binopt"])
    print(N1)
    

fig = plt.figure()    
ax = fig.gca()
ax.plot(N1_range, time_chart)
ax.set_xlabel("N")
ax.set_ylabel("Binopt Time, s")
fig.show()


fig = plt.figure()    
ax = fig.gca()
ax.plot(N1_range, bc_chart, label = "Baricenter")
ax.plot(N1_range, md_chart, label = "Median")
ax.plot(N1_range, sp_chart, label = "Split")
ax.plot(N1_range, sp10_chart, label = "Split-10")

ax.set_xlabel("N")
ax.set_ylabel("Quality")
lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
fig.show()



       
       




