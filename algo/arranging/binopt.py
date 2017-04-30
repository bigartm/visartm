import numpy as np
import time
import os


def monom(idx, value):
    if (value>0):
        return "+ %d x_%d " % (value, idx)
    elif (value<0):
        return "- %d x_%d " % (-value, idx)
    else:
        return ""


def minimize_binary_lp(A,b,c): 
    import pulp
    M, N = A.shape
    if (b.shape != (M,)):
        raise ValueError("Bad b shape")

    if (c.shape != (N,)):
        raise ValueError("Bad c shape")
    
    
    # Create problem
    prob = pulp.LpProblem("Problem", pulp.LpMinimize)     
    
    # Create variables
    names = [str(i) for i in range(N)]            
    x = pulp.LpVariable.dicts("x",names,0,1,pulp.LpInteger)
    
    # Objective function
    prob += pulp.lpSum([c[i]*x[str(i)] for i in range(N)]),""
    
    # Constraints
    for i in range(M):
        prob.constraints["C%d" % i] = pulp.LpAffineExpression([(x[str(j)], A[i][j]) for j in range(N)]) <= b[i]
    
    # Solution
    prob.solve()
    return np.array([pulp.value(x[names[i]]) for i in range(N)])

if __name__ == "__main__":
    A = np.array([
        [1, 4, 6, 2, 7],
        [5, 2, 8,-3, 1],
        [2, 5, 9, 6, -1]
    ])
    
    b = np.array([1,0,-1])
    c = np.array([2,3,-1,4,-1])
    ans = minimize_binary_lp(A,b,c)
    print(ans)

