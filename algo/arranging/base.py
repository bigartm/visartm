from django.conf import settings
import numpy as np

def get_arrangement_permutation(dist, mode, model=None, clusters=None, init_perm=None):
	if mode == "none":
		return [i for i in range(dist.shape[0])] 
	if mode == "hamilton":
		from .hamilton_path import HamiltonPath 
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
		mds = MDS(n_components=1, max_iter=3000, eps=1e-9, random_state=0, dissimilarity="precomputed", n_jobs=4)
		result = mds.fit_transform(dist).reshape(-1) 
		perm = np.argsort(result)
	elif mode == "dendro":
		from algo.arranging.dendro_arranger import DendroArranger
		da = DendroArranger(dist)
		perm = da.arrange()
	else:
		raise ValueError("Unknown mode: %s" % mode)
	
	if model:
		model.NDS = NDS(dist, perm)
		model.log("NDS=%f" % model.NDS)
		model.log("ANR=%f" % ANR(dist, perm))
		 
	return perm

