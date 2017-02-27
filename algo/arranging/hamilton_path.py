from itertools import permutations
from random import randint, random
import time
import numpy as np
from math import exp

class HamiltonPath:
	def __init__(self, adj):
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
		self.count_priority()
		self.cut_branch = self.N
		self.atomic_iterations = 10000
	
	def path_weight(self, path = None):
		if path == None:
			path = self.path
		return sum(self.A[path[i]][path[i+1]] for i in range (0, self.N-1))
	
	def test(self):
		print ("Quality before = ", self.path_weight())
		
		t = time.time()
		self.solve_nn()
		print ("NN: Quality = %d. Time = %fs" % (self.path_weight(), time.time() - t))
		
		t = time.time()
		self.solve_branch(2)
		print ("Branch(2): Quality = %d. Time = %fs" % (self.path_weight(), time.time() - t))
		 
		t = time.time() 
		self.solve_annealing(run_time=self.N/2)
		print ("Annealing: Quality = %d. Time = %fs" % (self.path_weight(), time.time() - t)) 
#		t = time.time()
#		self.cut_branch = 3
#		self.solve_branch()
#		print ("Branch(3): Quality = %d. Time = %fs" % (self.path_weight(), time.time() - t))
		
#		t = time.time()
#		self.cut_branch = self.N
#		self.solve_branch()
#		print ("Branch(full): Quality = %d. Time = %fs" % (self.path_weight(), time.time() - t))
		
		
	def solve(self, fast=False):
		start_time =  time.time()
		print ("Quality before = ", self.path_weight()) 
		if self.N <= 10: 
			self.solve_branch() 
		elif self.N <= 13: 
			self.solve_branch(3)
		elif self.N <= 18: 
			self.solve_branch(2)
		else:
			if fast:
				self.solve_annealing(run_time=10)
			else:
				self.solve_annealing(run_time=min(30,self.N))
		print ("Quality after = ", self.path_weight())
		print ("Time:  %fs " % (time.time() - start_time) )
		return self.path
		
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
	
	def solve_annealing(self, run_time=1):
		start_time = time.time()
		cur_weight = self.path_weight()
		self.chart_time = []
		self.chart_iterations = []
		self.chart_weight = []
		self.iter_counter = 0
		
		while (time.time() - start_time < run_time):
			self.elapsed = time.time() - start_time
			quality = self.path_weight()
			#print(self.elapsed, quality)
			self.chart_time.append(self.elapsed)
			self.chart_iterations.append(self.iter_counter)
			self.chart_weight.append(quality)
			self.iter_counter += self.atomic_iterations
			
			if self.elapsed > run_time:
				break
			q = cur_weight * 0.05 * (1 - self.elapsed/run_time)
			for c in range(self.atomic_iterations):
				i = randint(0, self.N - 1)
				j = randint(0, self.N - 1)
				self.path[i], self.path[j] = self.path[j], self.path[i]
				new_weight = self.path_weight()
				if new_weight < cur_weight:
					apply = True
				else: 
					apply = (random() < exp((cur_weight - new_weight)/q))
					
				if apply:
					cur_weight = new_weight
				else: 
					self.path[i], self.path[j] = self.path[j], self.path[i]
			#print (cur_weight)
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
		start_time = time.time()
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
			
if __name__ == '__main__':
	N = 22
	dist = np.zeros((N,N))
	for i in range(0,N):
		for j in range(i+1, N):
			dist[i][j]=dist[j][i] = randint(0,100)
	 
	hp = HamiltonPath(dist) 
	hp.test()
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
		
		
