import numpy as np



# Neigbor distances sum
def NDS(dist, perm):
	N = dist.shape[0]
	ans = 0
	for i in range(N-1):
		ans += dist[perm[i]][perm[i+1]]
	return ans		
		
 


			
# Average neigbour rank
def ANR(dist, perm):
	def rank(x, y):
		idx = np.argsort(dist[y])
		for i in range(len(idx)):
			if idx[i]==x:
				return i
	N = dist.shape[0]
	ranks = [] 
	for i in range(1,N): 
		ranks.append(rank(perm[i-1],perm[i]))
		ranks.append(rank(perm[i],perm[i-1])) 
		
	return np.mean(ranks)

	
# Corrected average neigbour rank
#def CANR(dist, perm):
#	return ANR(dist, perm) - 1.5
	
# Obtuse angle conserving
def OAC(dist, perm):
	N = dist.shape[0]
	ctr = 0
	for i in range(N):
		for j in range(i+1, N):
			for k in range(j+1, N):
				if dist[perm[i]][perm[k]]**2 > dist[perm[i]][perm[j]]**2 + dist[perm[j]][perm[k]]**2:
					ctr += 1
					
	return (6.0 * ctr) / (N * (N-1) * (N-2))
	
	


# Triple order conserving	
def TOC(dist, perm):
	N = dist.shape[0]
	ctr = 0
	for i in range(N):
		for j in range(i+1, N):
			for k in range(j+1, N):
				if dist[perm[i]][perm[k]] > max(dist[perm[i]][perm[j]],dist[perm[j]][perm[k]]):
					ctr += 1
					
	return (6.0 * ctr) / (N * (N-1) * (N-2))
	
	
# Obtuse angle non-conserving
def OANC(dist, perm):
	return 1 - OAC(dist, perm)
	

# Triple order non-conserving	
def TONC(dist, perm):
	return 1 - TOC(dist, perm)
	
# Distance-distance curve
def DDC(dist, perm):
	N = dist.shape[0]
	
	ans = np.zeros(N-2)
	for l in range(1,N-1):
		for i in range(0, N - l):
			ans[l-1] += dist[perm[i]][perm[i+l]]
		ans[l-1] /= (N - l)
	return ans	
	
	
'''
# Cosine-distance curve
def CDC(dist, perm):
	N = dist.shape[0]
	avg_cos = np.zeros((N,N))
	for i in range(N):
		for j in range(N):
			sum = 0
			for k in range(N):
				if k != i and k!=j:
					A = dist[i][k]
					B = dist[j][k]
					C = dist[i][j]
					sum += (A*A+B*B-C*C) / (2*A*B)  
			avg_cos[i][j] = sum / (N-2)
	
	ans = np.zeros(N-1)
	for l in range(1,N):
		for i in range(0, N - l):
			ans[l-1] += avg_cos[perm[i]][perm[i+l]]
		ans[l-1] /= (N - l)

	return ans
'''
	
# User penalty
def UP(assessment_C, perm):	
	N = len(perm)
	rev = [i for i in range(N)]
	for i in range(N):
		rev[perm[i]] = i

	ans = 0
	for i in range(N):
		for j in range(i+1, N):
			ans += assessment_C[i][j] * (abs(rev[i] - rev[j]) -1)
	return ans	
	
	
def flatten_symmetric_matrix(X):
	ans = []
	N = X.shape[0]
	for i in range(N):
		for j in range(i+1, N):
			ans.append(X[i][j])
	return np.array(ans)
	
	
# User-metric correlation
def UMC(ass, dist):
	C = flatten_symmetric_matrix(ass)
	D = flatten_symmetric_matrix(dist)
	C = C - np.mean(C)
	D = D - np.mean(D)
	return np.dot(C,D) / np.sqrt(np.dot(C,C) * np.dot(D,D))
	
	
	
def count_ranks(x):
	ranker = dict()
	j = 0
	for i in np.sort(x): 
		if not i in ranker:
			ranker[i] = j
		j+=1
	return [ranker[i] for i in x]

		
# Avarage neigbor rank (assessed)
def ANRA(C, perm):			
	def rank(x, y):
		if x==y:
			raise ValueError("Impossible.")
		return count_ranks(-C[y])[x]
			
	N = len(perm)
	ranks = [] 
	for i in range(1,N): 
		ranks.append(rank(perm[i-1],perm[i]))
		ranks.append(rank(perm[i],perm[i-1])) 
		
	return np.mean(ranks)
	
# Non-related neigbors
def NRN(C, perm):
	N = len(perm)
	ans = 0
	for i in range(N-1):
		if C[perm[i]][perm[i+1]]>0:
			ans += 1
	return 1 - (1.0 * ans) / (N-1)