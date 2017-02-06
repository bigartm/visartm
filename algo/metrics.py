import numpy as np
from scipy.spatial.distance import euclidean
#from scipy.stats import entropy 			
			
def hellinger(p,q):
	_SQRT2 = np.sqrt(2)
	return euclidean(np.sqrt(p), np.sqrt(q)) / _SQRT2
	
# Kullbak-Leibler divirgence
def kld(A, B):
    return np.sum([A[i] * np.log(A[i]/B[i]) for i in range(len(A)) if (A[i]!=0 and B[i]!=0)])	
	
# Jensen-Shannon Divergence
def jsd(P, Q):
    P = np.array(P)
    Q = np.array(Q)
    M = 0.5 * (P + Q)
    return 0.5 * (kld(P, M) + kld(Q, M)) 

# Jensen-Shannon Divergence
def jaccard(P, Q):
	union = 0
	intersection = 0
	N = len(P)
	eps = 1e-9
	for i in range(N):
		if P[i] > eps:
			union +=1
			if Q[i] > eps:
				intersection += 1
		elif Q[i] > eps:
			union +=1
	return (1.0 * intersection) / union
	
	
def filter_tails(matrix, start, end):
	for row in matrix:
		s = 0
		for j in np.argsort(row)[::-1]:
			s += row[j]
			if s < start or s > end:
				row[j] = 0
	return matrix
