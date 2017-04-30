import numpy as np
from crossmin import CrossMinimizer


N1 = 20
N2 = 200

A = np.zeros((N1,N2))
for i in range(N1*N2//20):
    i1 = np.random.randint(0, N1)
    i2 = np.random.randint(0, N2)
    A[i1][i2]=1

cm = CrossMinimizer(A)

#for row in cm.C:
#    print ([x for x in row])

for mode in ["baricenter", "median", "split10", "binopt"]:
    p = cm.solve(mode=mode)
    print(cm.cross_count(p))

#print(cm.cross_count(range(10)))
