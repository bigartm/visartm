from itertools import permutations
import random
import time
import numpy as np
import os
from math import exp
from django.conf import settings

import ctypes
from ctypes import c_int, c_double, POINTER, CDLL

 


class HamiltonPath:
	def __init__(self, adj, caller=None):
		self.A = adj
		if adj.shape[0] != adj.shape[1]:
			raise ValueError("Adjacency matrix should be square")
		self.N = adj.shape[0]		
		for i in range (0, self.N):
			if abs(self.A[i][i]) > 1e-6:
				raise ValueError ("Diagonal elements should be 0 ,but A[%d][%d]=%f" % (i,i,self.A[i][i]))
			self.A[i][i] = 0
			for j in range (i+1, self.N):
				if (self.A[i][j]!=self.A[j][i]):
					raise ValueError("Adjacency matrix should be symmetric")
		self.path = [i for i in range (0,self.N)]
		self.cut_branch = self.N
		self.atomic_iterations = 10000
		self.caller = caller
		self.clusters = [self.N]
		self.DEBUG = False		# If True, will be used python implementation of annealing, which is 100 times slower, but yields graphs
		
		
	def log(self, message):
		if self.caller:
			self.caller.log(message)
	
	def path_weight(self):
		ans = 0
		for i in range(self.N-1):
			ans += self.A[self.path[i]][self.path[i+1]]
		return ans
	
	# Set restriction on possible permutations.
	# Allowed only those permutations, which have same clusters as _path_
	# Cluster is substring of permutation, length of clusters given in _clusters_
	def set_clusters(self, clusters, path):
		self.log("Custom path: " + str(path))
		self.log("Custom clusters:" + str(clusters))
		
		if len(path) != self.N:
			raise ValueError("Invalid initial path")
		
		if np.sum(clusters) != self.N:
			raise ValueError("Invalid clusters lengthes")
		
		
		self.path = path
		self.clusters = clusters
		
		 
	 
		
	def solve_stupid_brute_force(self):
		ans = self.path_weight()		
		for i in permutations(range(self.N)):
			w = self.path_weight(i)
			if (w < ans):
				ans = w
				self.path = i

	def solve_branch_rec(self, last, count):
		if count == self.N:
			if self.cur_weight < self.best_weight:
				self.best_weight = self.cur_weight
				self.path = list(self.cur_path)
			return
		
		if self.cur_weight >= self.best_weight:
			return
		
		go_ctr = 0
		for i in self.priority[last]:
			if self.used[i] == 0:
				self.used[i] = 1
				self.cur_path[count] = i
				self.cur_weight += self.A[last][i]
				self.solve_branch_rec(i, count + 1)
				self.cur_weight -= self.A[last][i]
				self.cur_path[count] = -1				
				self.used[i] = 0
				go_ctr += 1
				if (go_ctr == self.cut_branch):
					break
   
    
   
	def count_priority(self):
		self.priority = []		
		for i in range(0, self.N):
			p = []
			used = [0 for j in range (0, self.N)]
			used[i] = 1
			for j in range(0, self.N-1):
				k_best = -1				
				for k in range(0, self.N):
					if used[k] == 0:
						if k_best == -1 or self.A[i][k] < self.A[i][k_best]:
							k_best  = k
				p.append(k_best)
				used[k_best] = 1
			self.priority.append(p)
			
	def solve_branch(self, cut=1000000):
		if (self.N>40):
			raise ValueError("N is too big.")
		start_time = time.time()
		self.count_priority()
		self.cut_branch = cut
		self.best_weight = self.path_weight()
		self.used = [0 for i in range(0,self.N)]
		self.cur_path = [-1 for i in range(0,self.N)]
		for i in range (0, self.N):
			self.used[i] = 1 
			self.cur_path[0] = i
			self.cur_weight = 0
			self.solve_branch_rec(i, 1)
			self.used[i] = 0
		self.elapsed = time.time() - start_time
			
	def solve_nn(self):
		start_time = time.time()
		self.best_weight = self.path_weight()
		self.cur_path = [0 for i in range(0,self.N)]	  
				
		for i in range(0, self.N):
			self.cur_path[0] = i   
			self.used = [0 for j in range(0,self.N)]
			self.used[i] = 1
			for j in range(1, self.N):
				last = self.cur_path[j-1]
				k_best = -1				
				for k in range(0, self.N):
					if self.used[k] == 0:
						if k_best == -1 or self.A[last][k] < self.A[last][k_best]:
							k_best  = k
				self.cur_path[j] = k_best
				self.used[k_best] = 1
			
			if (self.path_weight(self.cur_path) < self.best_weight):
				self.path = self.cur_path
				self.best_weight = self.path_weight(self.cur_path)
		
		self.elapsed = time.time() - start_time
			
	def get_path(self):
		return self.path
		
	def get_inverse_permutation(self):
		ret = [0 for i in range(self.N)]
		for i in range(self.N):
			ret[self.path[i]] = i
		return ret
		
	def permute_adj_matrix(self):
		ret = np.zeros((self.N, self.N))
		for i in range(0, self.N):
			for j in range(0, self.N):
				ret[i][j] = self.A[self.path[i]][self.path[j]]
		return ret
		
	def solve(self):	
		if self.solve_lkh():
			return self.path
		return self.solve_annealing()
		
	def solve_lkh(self):
		try:
			lkh_path = os.path.join(settings.BASE_DIR, "algo", "lkh")
		except:
			lkh_path = "D:\\visartm\\algo\\lkh"
		
		try:
			temp_folder = self.caller.get_folder()
		except:
			temp_folder = lkh_path
		
		exe_path = os.path.join(lkh_path, "lkh.exe")
		tsp_path = os.path.join(temp_folder, "hamilton.tsp")
		par_path = os.path.join(temp_folder, "hamilton.par")
		out_path = os.path.join(temp_folder, "hamilton.out")
		
		if not os.path.exists(exe_path):
			self.log("LKH algorithm isn't installed.")
			return False
		
		with open(tsp_path, "w") as f:
			f.write("TYPE : TSP\n")
			f.write("DIMENSION : %d\n" % (self.N+1))
			f.write("EDGE_WEIGHT_TYPE : EXPLICIT\n")
			f.write("EDGE_WEIGHT_FORMAT : FULL_MATRIX\n")
			f.write("EDGE_WEIGHT_SECTION\n")
			for i in range(self.N):
				for j in range(self.N):
					f.write("%d " % int(100000*self.A[i][j]))
				f.write("0\n")
			for j in range(self.N+1):
				f.write("0 ")
			f.write("\nEOF")	
		
		with open(par_path, "w") as f:
			f.write("PROBLEM_FILE = %s\n" % tsp_path)
			f.write("OUTPUT_TOUR_FILE = %s\n" % out_path)
			f.write("PRECISION = 1\n")
			f.write("TRACE_LEVEL = 0\n")
			
			
		self.log("Invoking LKH...")
		start_time = time.time()
			
		os.system("%s %s < %s" % (exe_path, par_path, par_path))
		self.log("LKH done.  Running time %f" % (time.time() - start_time))
		
		
		fake_path = []
		line_ctr = -1
		for line in open(out_path, "r"):
			if line_ctr >=0 and line_ctr <= self.N:
				fake_path.append(int(line)-1)
				line_ctr += 1
			if "TOUR_SECTION" in line:
				line_ctr = 0
		
		sep = 0
		for i in range(self.N+1):
			if fake_path[i] == self.N:
				sep = i
		self.path = fake_path[sep+1:] + fake_path[0:sep]
		return self.path
			
	def solve_annealing_c(self, steps, Tmin, Tmax):
		try:
			c_path = os.path.join(settings.BASE_DIR, "algo", "clib")
		except:
			c_path = "D:\\visartm\\algo\\clib"
			
		source_path = os.path.join(c_path, "arrange.c")
		lib_path = os.path.join(c_path, "arrange.so")
		
		if not os.path.exists(lib_path) or \
			(os.path.getmtime(source_path) > os.path.getmtime(lib_path)):

			if os.system("gcc -shared -fPIC -o %s %s" % (lib_path, source_path)):
				raise RuntimeError("Unable to build library arrange.c")
			else:
				self.log("Library arrange.c succesfully built")
				
		arrange_lib = CDLL(lib_path)
				   
				 
		arrange_lib.simanneal.restype = c_double
		arrange_lib.simanneal.argtypes = [c_int, c_double, c_double, c_int,\
                    POINTER(c_double), POINTER(c_int), c_int, POINTER(c_int)] 
		
		
        
		ans = (c_int*self.N)() 
		for i in range(self.N):
			ans[i] = self.path[i]
			
		
			
		# Extern function call
		arrange_lib.simanneal(self.N, Tmin, Tmax, steps,\
            self.A.ctypes.data_as(POINTER(c_double)), ans,\
			len(self.clusters), np.array(self.clusters).ctypes.data_as(POINTER(c_int)))
		#del arrange_lib
		self.path = list(np.array(ans))
		
		
			
			
			
        
     
	def ew2(self, i):
		ans = 0
		if i > 0:
			ans += self.A[self.path[i-1], self.path[i]]
		if i < self.N - 1:
			ans += self.A[self.path[i], self.path[i + 1]]
		return ans
		 
			
	
	def solve_annealing(self, steps="auto"):
		T0 = np.mean(self.A)
		Tmin = 1e-5 * T0
		Tmax = 1e5 * T0
		
		if steps == "auto":
			steps = min(10000*self.N*self.N, 100000000)
			if steps < 1000000:
				steps = 1000000
		
		start_time = time.time()
		
		if not self.DEBUG:
			self.solve_annealing_c(steps, Tmin, Tmax)
		else:
			cur_weight = self.path_weight()
			self.chart_iterations = []
			self.chart_weight = []
			self.iter_counter = 0
			
			 
			Tfactor = -np.log(Tmax/Tmin)
			
			acc = 0
			imp = 0
			
			for step in range(steps):
				if step % 10000==0:
					self.elapsed = time.time() - start_time
					quality = self.path_weight() 
					self.chart_iterations.append(step)
					self.chart_weight.append(quality) 
				
						
					T = Tmax * np.exp(Tfactor*step/steps)
					#self.log("I=%d, T=%f, Q=%f, acc=%d, imp=%d" % (step, T, quality, acc, imp))
					acc = 0
					imp = 0
				 
				i = randint(0, self.N - 1)
				j = randint(0, self.N - 1)
				
				dE = - self.ew2(i) - self.ew2(j)
				self.path[i], self.path[j] = self.path[j], self.path[i]
				dE += self.ew2(i) + self.ew2(j)
				
				T = Tmax * np.exp(Tfactor*step/steps)
				if dE > 0.0 and np.exp(-dE / T) < random.random():
					#Restore
					self.path[i], self.path[j] = self.path[j], self.path[i]
				else:
				#Accept
					if dE < 0.0:
						imp += 1
					acc += 1
					cur_weight += dE
				
		run_time = time.time()-start_time
		self.log("Time=%fs" % run_time)
		self.log("Speed=%d steps per second" % int(steps/(run_time+1e-10)))
		return self.path
   
if __name__ == '__main__':
	N = 100
	dist = np.zeros((N,N))
	for i in range(0,N):
		for j in range(i+1, N):
			dist[i][j]=dist[j][i] = random.randint(0,100)
	 
	hp = HamiltonPath(dist) 
	#hp.test()
	#hp.solve()
	
			
#	hp2 = HamiltonPath(dist) 
#	hp2.solve_branch()
#	print (hp2.get_path())
#	print (hp2.path_weight())
#	print (hp2.age())
	
#	hp4 = HamiltonPath(dist) 
#	hp4.cut_branch = 2	
#	hp4.solve_branch()
#	print (hp4.get_path())
#	print (hp4.path_weight())
#	print (hp4.age())	
#	
#	hp3 = HamiltonPath(dist)
#	hp3.solve_nn()
#	print (hp3.get_path())
#	print (hp3.path_weight())
#	print (hp3.age())
#		
		
		
