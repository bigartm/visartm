import numpy as np
from hamilton_path import HamiltonPath
import matplotlib.pyplot as plt
import time
 

def generate_matrix(N):    
    path = np.random.choice(N,N,replace=False)
    X = np.zeros((N,3))
    for i in range(N):
        X[path[i]][0] = 10*i
        X[path[i]][1] = np.random.normal(scale=5)
        X[path[i]][2] = np.random.normal(scale=5)
         
    
    dist = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            dist[i][j] = np.linalg.norm(X[i]-X[j])
    
    best = 0
    for i in range(N-1):
        best += dist[path[i]][path[i+1]]
    
    return dist, best

N=1000
dist, best = generate_matrix(N)
print(best)
hp = HamiltonPath(dist)
hp.solve_lkh()
print(hp.path)
print(hp.path_weight())