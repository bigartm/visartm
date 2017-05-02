import numpy as np 
import time
import os


def lin_fun(x):
    first_symbol = True
    ans = ""
    
    if type(x) == dict:
        rng = x.keys()
    else:
        rng = range(len(x))
        
    for i in rng:
        if x[i] == 0:
            continue
        
        if x[i] > 0:
            if not first_symbol:
                ans += " + "
            if x[i]!=1:
                ans += "%d " % x[i]
        elif x[i] < 0:
            if first_symbol:
                ans += "- "
            else:
                ans += " - "
            if x[i]!=-1:
                ans += "%d " % -x[i]
        first_symbol = False
        ans += "x_%d" % i 
    return ans
    
# minimizes c*x, where x is in {0,1}^N;
# under constraints Ax <= b
# returns optimal x
# A is matrix M*N or list of M dicts int->int
def minimize_binary_lp(A, b, c, use_pulp=False): 
    import pulp
    M = len(b)
    N = len(c) 
    
    if use_pulp:
        # Create problem
        prob = pulp.LpProblem("Problem", pulp.LpMinimize)     
        
        # Create variables
        names = [str(i) for i in range(N)]            
        x = pulp.LpVariable.dicts("x",names,0,1,pulp.LpInteger)
        
        # Objective function
        prob += pulp.lpSum([c[i]*x[str(i)] for i in range(N)]),""
             
        # Constraints
        if type(A) == np.ndarray:
            for i in range(M):
                prob.constraints["C%d" % i] = pulp.LpAffineExpression([(x[str(j)], A[i][j]) for j in range(N) if A[i][j]!=0]) <= b[i]
        else:
            for i in range(M):
                prob.constraints["C%d" % i] = pulp.LpAffineExpression([(x[str(j)], A[i][j]) for j in A[i].keys()]) <= b[i]
            
        # Solution 
        prob.solve() 
        return np.array([pulp.value(x[names[i]]) for i in range(N)])
    else:
        temp_path = os.path.join(os.getcwd(), str(int(10*time.time())))
        os.makedirs(temp_path)
        lp_path = os.path.join(temp_path, "input.lp")
        sol_path = os.path.join(temp_path, "sol.txt")
        exe_path = pulp.LpSolverDefault.path
        
        with open(lp_path, "w") as f:
            f.write("\\* Problem *\\\n")
            f.write("Minimize\n")
            f.write("OBJ: %s\n" % lin_fun(c))
            f.write("Subject To\n")
            for i in range(M):
                f.write("C%d: %s <= %f\n" % (i, lin_fun(A[i]), b[i]))
            f.write("Binaries\n")
            for i in range(N):
                f.write("x_%d\n" % i)
            f.write("End\n")
        
        os.system("%s %s solve solu %s" % (exe_path, lp_path, sol_path))
 
        ans = np.zeros(N)
        
        for line in open(sol_path, "r"):
            l = line.split()
            for i in range(len(l)):
                if(l[i][0]=="x"):
                    ans[int(l[i][2:])] = float(l[i+1])
                    break
        os.remove(lp_path)
        os.remove(sol_path)
        os.removedirs(temp_path)
        
        return ans
    
if __name__ == "__main__":
    A = np.array([
        [1, 4, 6, 2, 7, 8],
        [5, 2, 8,-3, 1, -3],
        [2, 5, 9, 6, -1, 6]
    ])
    
    b = np.array([1,0,-1])
    c = np.array([2,3,-1,4,-1, 0])
    ans = minimize_binary_lp(A,b,c)
    print(ans)

