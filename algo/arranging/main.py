import numpy as np
from hamilton_path import HamiltonPath
import matplotlib.pyplot as plt


N=12
dist = np.zeros((N, N))
for i in range(N):
    for j in range(i+1, N):
        dist[i][j] = dist[j][i] = np.random.rand() 
        
        
hp = HamiltonPath(dist)
print(hp.path_weight())
plt.imshow(dist, interpolation='nearest')
plt.show()
hp.solve_annealing(run_time=5)
#hp.solve_branch() 

plt.imshow(hp.permute_adj_matrix(), interpolation='nearest')
plt.show()

print(hp.path_weight())   