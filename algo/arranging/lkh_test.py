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

def solve(dist, mode):
    start_time= time.time()
    hp = HamiltonPath(dist)
    print(mode+"...")
    if mode == "LKH":
        hp.solve_lkh()
    elif mode == "annealing":
        hp.solve_annealing()
    return hp.path_weight(), time.time() - start_time

N_range = [50,100,150,200,300,400,500,600,700,800,900,1000]
q_lkh = []
#q_ann = []
t_lkh = []
#t_ann = []

for N in N_range:
    print(N)
    dist, best = generate_matrix(N)
    weight_lkh, time_lkh = solve(dist, "LKH")
    #weight_ann, time_ann = solve(dist, "annealing")
    q_lkh.append(best / weight_lkh)
    #q_ann.append(best / weight_ann)
    t_lkh.append(time_lkh)
    #t_ann.append(time_ann)
    
plt.plot(N_range, t_lkh, label="LKH")
#plt.plot(N_range, q_ann, label="Annealing")
plt.legend()

    
    