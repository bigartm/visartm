from base import get_arrangement_permutation
from metrics import get_metric_by_name
import numpy as np

# Phi : matrix [N_words, N_topics]
# metrics: "euclidean", "cosine", "manhattan", "hellinger", "jsd", "jaccard"
def arrange_topics(phi, metric="hellinger"):
	metric = get_metric_by_name(metric)
	phi_t = phi.transpose()
	N = phi.shape[1]
	topic_distances = np.zeros((N, N))		
	for i in range(N):
		for j in range(N):
			topic_distances[i][j] = metric(phi_t[i], phi_t[j])
	return get_arrangement_permutation(topic_distances, mode="hamilton")
	
