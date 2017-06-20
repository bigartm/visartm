import numpy as np
from hamilton_path import HamiltonPath
import matplotlib.pyplot as plt
import time

class DefaultLogger:
    def log(self, x):
        print(x)

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

def N_profiler():
    N_range = range(50,500,50)
    time_chart = []
    for N in N_range:
        print(N)
        dist, _ = generate_matrix(N)
        hp = HamiltonPath(dist)
        t = time.time()
        hp.solve_annealing_c(5000000)
        time_chart.append(5000000/(time.time()-t))
        
    plt.plot(N_range, time_chart) 
    plt.xlabel("N")
    plt.ylabel("Steps/s")
    plt.title("Time of annealing simulation")
    plt.show() 
        
def profiler(N=50):
    steps_range = [int(1.5**i) for i in range(15,41)]
    time_chart = []
    quality_chart = []
    dist, best_q = generate_matrix(N)
    for steps in steps_range:
        print(steps)
        t = time.time()
        hp = HamiltonPath(dist)
        hp.solve_annealing_c(steps)
        time_chart.append(time.time()-t)
        quality_chart.append(hp.path_weight())
        
    k = steps_range[-1]/time_chart[-1]
    plt.plot(steps_range, time_chart)
    plt.plot([0,steps_range[-1]],[0, steps_range[-1]/k])
    plt.xlabel("Steps")
    plt.ylabel("Time, s")
    plt.title("Time of annealing simulation")
    plt.show()
    print("%.0f steps per second" % k)
    
    plt.plot(steps_range, quality_chart)
    plt.plot([steps_range[0],steps_range[-1]], [best_q, best_q])
    plt.xlabel("Steps")
    plt.ylabel("Quality")
    plt.title("Quality of annealing simulation")
    plt.show()
 
def final_test():  
     dist, best_q = generate_matrix(50)
     hp = HamiltonPath(dist, caller=DefaultLogger())
     hp.solve_annealing()
     print(best_q)
     print(hp.path_weight())
    
def steps_optimizer():
    steps_range = [int(1.4**i) for i in range(20,52)]
    
    N_range = range(1,60)
    best_steps_chart = []
    
    for N in N_range:
        print("N=%d"% N)
        dist, best_q = generate_matrix(N)
        hp = HamiltonPath(dist, caller=DefaultLogger())
        print("Best: %f" % best_q)
    
    
        hp.path = list( np.random.choice(N,N,replace=False))
        
        q = [] 
        best_steps = 1e9
        for steps in steps_range:
            hp.solve_annealing_c(steps=steps, Tmax=np.mean(dist)*1e5, Tmin=np.mean(dist)*1e-5)
            quality = hp.path_weight()
            q.append(quality)
            if (quality==best_q and steps<best_steps):
                best_steps = steps
                break 
        best_steps_chart.append(best_steps)
        #plt.plot(steps_range, q)
        #plt.plot([steps_range[0],steps_range[-1]], [best_q, best_q])
        #plt.show()
          
    plt.plot(N_range, best_steps_chart)
    plt.plot(N_range, 1e4*np.power(N_range,2))
    plt.plot()
    plt.xlabel("N")
    plt.ylabel("Optimal number of steps")
     
    
    #hp.solve_simanneal()
    #print(hp.path) 
    
    '''
    hp.solve_annealing(steps=1000000, Tmax=np.mean(dist)*1e6, Tmin=np.mean(dist)*1e-6)
    plt.plot(hp.chart_iterations, hp.chart_weight)
    plt.plot([0, hp.chart_iterations[-1]], [best_q, best_q])
    plt.show()
    print(hp.path_weight()) 
    print(hp.path) 
    
    
    hp.solve_annealing_c(steps=10000000, Tmax=np.mean(dist)*1e6, Tmin=np.mean(dist)*1e-6)
    print(hp.path_weight()) 
    print(hp.path) 
    '''
    
#steps_optimizer()
final_test()
#profiler()
#N_profiler()
