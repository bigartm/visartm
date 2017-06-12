import numpy as np
#from scipy.spatial.distance import euclidean
from scipy.stats import entropy 			



def euclidean(p, q):
	return np.linalg.norm(p-q)
			
def cosine(p, q):
	return 1.0 - (np.dot(p,q) / (np.linalg.norm(p)*np.linalg.norm(q)))

def manhattan(p, q):
	return np.sum(np.abs(p-q))

 
			
def hellinger(p,q):
	_SQRT2 = np.sqrt(2)
	return euclidean(np.sqrt(p), np.sqrt(q)) / _SQRT2
	
'''
# Kullbak-Leibler divirgence
def kld(A, B):
    return np.sum([A[i] * np.log(A[i]/B[i]) for i in range(len(A))] )	
	
def jsd_bad(P, Q):
	P = np.array(P)
	Q = np.array(Q)
	M = 0.5 * (P + Q)
	return 0.5 * (kld(P, M) + kld(Q, M)) 
'''

# Jensen-Shannon Divergence
def jsd(P, Q): 
	return entropy(0.5 * (P + Q)) - 0.5 * (entropy(P) + entropy(Q))

'''
def jaccard_bad(P, Q):
	union = 0
	intersection = 0
	N = len(P)
	eps = 1.0 / N
	for i in range(N):
		if P[i] > eps:
			union +=1
			if Q[i] > eps:
				intersection += 1
		elif Q[i] > eps:
			union +=1
	if union == 0:
		print("FUCK")
		return 1.0
	return 1.0 - (1.0 * intersection) / union	
'''
# Jaccard
def jaccard(P, Q):
	N = len(P)
	eps = 1.0 / N
	P = P > eps
	Q = Q > eps
	union = (P | Q).sum()
	intersection = (P & Q).sum()
	return 1.0 - (1.0 * intersection) / union
	
def chebyshev(p, q):
	return np.max(np.abs(p-q))
	
'''	
def filter_tails(matrix, start, end):
	for row in matrix:
		s = 0
		for j in np.argsort(row)[::-1]:
			s += row[j]
			if s < start or s > end:
				row[j] = 0
	return matrix
'''

metrics_list = ["euclidean", "cosine", "manhattan", "hellinger", "jsd", "jaccard", "chebyshev"]
metrics_list = ["euclidean", "cosine", "manhattan", "hellinger", "jsd", "jaccard", "chebyshev"]

default_metric = "jaccard"

def get_metric_by_name(name):
	if name == "default":
		return get_metric_by_name(default_metric)
	elif name == "euclidean": 
		return euclidean 
	elif name == "cosine": 
		return cosine  
	elif name == "manhattan":
		return manhattan
	elif name == "cov":
		return cov
	elif name == "hellinger": 
		return hellinger
	elif name == "kld": 
		return kld
	elif name == "jsd": 
		return jsd
	elif name == "jaccard":  
		return jaccard
	elif name == "chebyshev":
		return chebyshev
	else:
		return name

