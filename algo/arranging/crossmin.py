# Bipartite graph crosses minimization

import numpy as np

class CrossMinimizer:
	
	def __init__(self, A): 
		self.N1, self.N2 = A.shape
		self.A = np.zeros((self.N1, self.N2))
		for i in range(self.N1):
			for j in range(self.N2):
				self.A[i][j] = 1 if A[i][j] else 0
		
		
		A_sum = np.zeros((self.N1, self.N2))
		
		for i in range(self.N1):
			A_sum[i][0] = A[i][0]
			for j in range(1, self.N2):
				A_sum[i][j] = A_sum[i][j-1] + self.A[i][j]
		
		self.C = np.zeros((self.N1, self.N1))
		
		for x in range(self.N1):
			for y in range(self.N1):
				if x == y:
					self.C[x][y] = 0
				else:
					self.C[x][y] = sum([self.A[x][j] * A_sum[y][j-1] for j in range(1,self.N2)])
		
	def solve(self, mode="auto", model=None):
		if mode == "tryall":
			best = self.N1*self.N1*self.N2*self.N2
			for new_mode in ["baricenter", "median", "split10", "binopt"]:
				perm = self.solve(mode=new_mode, model=model)
				cc = self.cross_count(perm)
				model.log("%s %d" % (new_mode, cc))
				if cc < best:
					best = cc
					ans = perm
			return ans
		if mode == "auto":
			if self.N1 <= 50:
				return self.solve_binopt(use_pulp=False)
			else:
				return self.solve_split_repeat(10*self.N1)
		if mode == "baricenter":
			return self.solve_baricenter()
		elif mode == "median":
			return self.solve_median()
		elif mode == "split":
			return self.solve_split()
		elif mode == "split10":
			return self.solve_split_repeat(10)
		elif mode == "split10N":
			return self.solve_split_repeat(10*self.N1)
		elif mode == "binopt":
			return self.solve_binopt(use_pulp=True)
		elif mode == "binopt_fast":
			return self.solve_binopt(use_pulp=False)	
		else:
			raise ValueError("Unknown mode")
		
	def solve_baricenter(self):
		return np.argsort([np.mean([j for j in range(self.N2) if self.A[i][j]==1]) for i in range(self.N1)])
	
	def solve_median(self):
		return np.argsort([np.median([j for j in range(self.N2) if self.A[i][j]==1]) for i in range(self.N1)])
		
		
	def solve_split_repeat(self, times):
		best = self.N1*self.N1*self.N2*self.N2
		for i in range(times):
			perm = self.solve_split()
			cc = self.cross_count(perm) 
			if cc < best:
				best = cc
				ans = perm
		return ans
			
	def solve_split_rec(self, i, j):
		if i>=j:
			return
		pivot = self.ans[np.random.randint(i, j)]
		less = []
		more = []
		for k in range(i,j):
			z = self.ans[k]
			if z == pivot:
				continue
			if self.C[z][pivot] < self.C[pivot][z]:
				less.append(z)
			else:
				more.append(z)
		
		mid = i + len(less)
		for k in range(len(less)):
			self.ans[i+k] = less[k]
		self.ans[mid] = pivot
		for k in range(len(more)):
			self.ans[mid+1+k] = more[k]
		
		
		self.solve_split_rec(i, mid)
		self.solve_split_rec(mid+1, j)
		
	def solve_split(self):
		self.ans = np.array(range(self.N1))
		self.solve_split_rec(0, self.N1)
		return self.ans
	
		
	def solve_binopt(self, use_pulp=True): 
		ctr = np.zeros((self.N1, self.N1), dtype=np.int32)
		counter = 0 
		for i in range(self.N1):
			for j in range(i+1, self.N1):
				ctr[i][j] = counter 
				counter += 1
		
		N = self.N1*(self.N1-1)//2
		M = self.N1*(self.N1-1)*(self.N1-2)//3
		A = [0 for i in range(M)]
		b = np.zeros(M)
		c = np.zeros(N)
		
		for i in range(self.N1):
			for j in range(i+1, self.N1):
				c[ctr[i][j]] = self.C[i][j] - self.C[j][i]
		 
		ct_cnt = 0
		for i in range(self.N1):
			for j in range(i+1, self.N1):
				for k in range(j+1, self.N1):
					A[ct_cnt] = {ctr[i][j] : 1, ctr[j][k] : 1, ctr[i][k] : -1}
					A[ct_cnt+1] = {ctr[i][j] : -1, ctr[j][k] : -1, ctr[i][k] : 1}
					b[ct_cnt] = 1
					b[ct_cnt+1] = 0
					ct_cnt+=2
					
					
					
		try:			 
			from algo.arranging.binopt import minimize_binary_lp
		except:
			from binopt import minimize_binary_lp
			
		
		ans = minimize_binary_lp(A, b, c, use_pulp=use_pulp)
		
		X = np.zeros((self.N1, self.N1))
		for i in range(self.N1):
			for j in range(i+1, self.N1):
				if ans[ctr[i][j]]>0.5:
					X[i][j] = 1
				else:
					X[i][j] = 0
				X[j][i] = 1 - X[i][j]
		self.X = X
		
		return np.argsort([-sum(X[i]) for i in range(self.N1)])
		
				
	def cross_count(self, perm):
		if len(perm) != self.N1:
			raise ValueError("Bad permutation size")
		
		ans = 0
		for i in range(self.N1):
			for j in range(i+1, self.N1):
				ans += self.C[perm[i]][perm[j]]		
		return ans
		