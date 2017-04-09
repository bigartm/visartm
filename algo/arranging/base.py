import numpy as np
from django.conf import settings

def get_arrangement_permutation(dist, mode, model=None, clusters=None, init_perm=None):
	if mode == "hamilton":
		from algo.arranging.hamilton_path import HamiltonPath 
		hp = HamiltonPath(dist, caller=model)
		if clusters:
			hp.set_clusters(clusters, init_perm)
		hp.solve()
		perm = hp.path
	elif mode == "tsne": 
		from sklearn.manifold import TSNE
		tsne_model = TSNE(n_components=1, random_state=0, metric = "precomputed")
		tsne_result = tsne_model.fit_transform(dist).reshape(-1) 
		perm = np.argsort(tsne_result)
	elif mode == "mds":
		from sklearn.manifold import MDS
		mds = MDS(n_components=1, max_iter=3000, eps=1e-9, random_state=0,dissimilarity="precomputed", n_jobs=4)
		result = mds.fit_transform(dist).reshape(-1) 
		perm = np.argsort(result)
	elif mode == "dendro":
		from algo.arranging.dendro_arranger import DendroArranger
		da = DendroArranger(dist)
		perm = da.arrange()
	else:
		raise ValueError("Unknown mode: %s" % mode)
	
	if model:
		model.log("Quality=%f" % path_weight(dist, perm))
	return perm

def path_weight(dist, perm):
	N = dist.shape[0]
	ans = 0
	for i in range(N-1):
		ans += dist[perm[i]][perm[i+1]]
	return ans		
		

def rank(dist, x, y):
	idx = np.argsort(dist[x])
	for i in range(len(idx)):
		if idx[i]==y:
			return i
	
def average_neigbour_rank(dist, perm):
	N = dist.shape[0]
	ranks = []
	for i in range(N-1):
		x = perm[i]
		y = perm[i+1]
		ranks.append(rank(dist,x,y))
	return np.mean(ranks)
		
def obtuse_angle_conserving(dist, perm):
	N = dist.shape[0]
	ctr = 0
	for i in range(N):
		for j in range(i+1, N):
			for k in range(j+1, N):
				if dist[perm[i]][perm[k]] > max(dist[perm[i]][perm[j]],dist[perm[j]][perm[k]]):
					ctr += 1
					
	return (6.0 * ctr) / (N * (N-1) * (N-2))
	
def AD(dist, perm):
	N = dist.shape[0]
	avg_cos = np.zeros(N,N)
	for i in range(N):
		for j in range(i, N):
			sum = 0
			for k in range(N):
				A = dist[i][k]
				B = dist[j][k]
				C = dist[i][j]
				sum += (A*A+B*B-C*C) / (2*A*B)  
			avg_cos[i][j] = sum / N
	
	ans = np.zeros(N)
	for l in range(N):
		for i in range(0, N - l):
			ans[l] += avg_cos[perm[i]][perm[i+l]]
		ans[l] /= (N - l)

	return ans
	
	
	
	
	
def user_score(assessment, perm):	
	N = len(perm)
	rev = [i for i in range(N)]
	for i in range(N):
		rev[perm[i]] = i

	ans = 0
	for i in range(N):
		for j in range(i+1, N):
			ans += assessment[i][j] * abs(rev[i] - rev[j])
	return ans
