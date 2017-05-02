import numpy as np
from django.conf import settings

def get_arrangement_permutation(dist, mode, model=None, clusters=None, init_perm=None):
	if mode == "hamilton":
		from algo.arranging.hamilton_path import HamiltonPath 
		hp = HamiltonPath(dist, caller=model)
		if clusters:
			hp.set_clusters(clusters, init_perm)
			hp.solve_annealing()
		else:
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
		model.NDS = neigbor_distances_sum(dist, perm)
		model.log("NDS=%f" % model.NDS)
		model.log("CANR=%f" % corrected_average_neigbour_rank(dist, perm))
		 
	return perm

def neigbor_distances_sum(dist, perm):
	N = dist.shape[0]
	ans = 0
	for i in range(N-1):
		ans += dist[perm[i]][perm[i+1]]
	return ans		
		

def rank(dist, x, y):
	idx = np.argsort(dist[y])
	for i in range(len(idx)):
		if idx[i]==x:
			return i

def corrected_average_neigbour_rank(dist, perm):
	return average_neigbour_rank(dist, perm) - 1.5
			
def average_neigbour_rank(dist, perm):
	N = dist.shape[0]
	ranks = [] 
	for i in range(1,N): 
		ranks.append(rank(dist,perm[i-1],perm[i]))
		ranks.append(rank(dist,perm[i],perm[i-1])) 
		
	return np.mean(ranks)
		
def obtuse_angle_conserving(dist, perm):
	N = dist.shape[0]
	ctr = 0
	for i in range(N):
		for j in range(i+1, N):
			for k in range(j+1, N):
				if dist[perm[i]][perm[k]]**2 > dist[perm[i]][perm[j]]**2 + dist[perm[j]][perm[k]]**2:
					ctr += 1
					
	return (6.0 * ctr) / (N * (N-1) * (N-2))
		
def triple_order_conserving(dist, perm):
	N = dist.shape[0]
	ctr = 0
	for i in range(N):
		for j in range(i+1, N):
			for k in range(j+1, N):
				if dist[perm[i]][perm[k]] > max(dist[perm[i]][perm[j]],dist[perm[j]][perm[k]]):
					ctr += 1
					
	return (6.0 * ctr) / (N * (N-1) * (N-2))
	
def distance_distance_curve(dist, perm):
	N = dist.shape[0]
	
	ans = np.zeros(N-1)
	for l in range(1,N):
		for i in range(0, N - l):
			ans[l-1] += dist[perm[i]][perm[i+l]]
		ans[l-1] /= (N - l)

	return ans	
	
def cosine_distance_curve(dist, perm):
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
	
	
	
def user_penalty(assessment_C, perm):	
	N = len(perm)
	rev = [i for i in range(N)]
	for i in range(N):
		rev[perm[i]] = i

	ans = 0
	for i in range(N):
		for j in range(i+1, N):
			ans += assessment_C[i][j] * (abs(rev[i] - rev[j]) -1)
	return ans	
	
	
	
def user_metric_correlation(assessment_C, dist):
	N = dist.shape[0]
	C = []
	D = []
	for i in range(N):
		for j in range(i+1, N):
			C.append(assessment_C[i][j])
			D.append(dist[i][j])
	
	C = np.array(C)
	D = np.array(D)
	C = C - np.mean(C)
	D = D - np.mean(D)
	return -np.dot(C,D) / np.sqrt(np.dot(C,C) * np.dot(D,D))
	