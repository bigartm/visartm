import numpy as np

class DendroArranger:
	def __init__(self, dist):
		self.dist = dist
		if dist.shape[0] != dist.shape[1]:
			raise ValueError("Distance matrix should be square")
		self.N = dist.shape[0]		
		for i in range (0, self.N):
			if abs(self.dist[i][i]) > 1e-6:
				raise ValueError ("Diagonal elements should be 0 ,but A[%d][%d]=%f" % (i,i,self.A[i][i]))
			self.dist[i][i] = 0
			for j in range (i+1, self.N):
				if (self.dist[i][j]!=self.dist[j][i]):
					raise ValueError("Distance matrix should be symmetric")
		
	
	def merge(self):
		if self.px == 0:
			self.pieces[self.x].reverse()
		if self.py == -1:
			self.pieces[self.y].reverse()
		self.pieces[self.x] = self.pieces[self.x] +  self.pieces[self.y]
		self.pieces[self.y] = self.pieces[-1]
		del self.pieces[-1]
	
	def try_dist(self, x, y):
		for px in [-1,0]:
			for py in [-1,0]:
				dist = self.dist[self.pieces[x][px]][self.pieces[y][py]]
				if dist < self.min_dist:
					self.min_dist = dist
					self.x = x
					self.y = y
					self.px = px
					self.py = py
					
	def arrange(self):
		self.pieces = [[i] for i in range(self.N)] 
		while(len(self.pieces) != 1):
			#print(self.pieces)
			M = len(self.pieces)
			self.min_dist = np.inf 
			for x in range(M):
				for y in range(x+1, M):
					self.try_dist(x, y)
			self.merge()
		return self.pieces[0]
	
if __name__ == "__main__":
	N = 10
	dist = np.zeros((N, N))
	target = [1,9,4,6,0,2,3,5,7,8]
	for i in range(N):
		for j in range(N):
			d = abs(i-j)
			dist[target[i]][target[j]] = d
	print(dist)			
				
	da = DendroArranger(dist)
	ans = da.arrange()
	print(ans)