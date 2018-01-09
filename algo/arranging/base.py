from django.conf import settings
from algo.arranging.metrics import get_metric_by_name
import numpy as np
import time


def get_arrangement_permutation(dist, mode, model=None):
    """Returns best permutation of topics for topics spectrum.

    Args:
        dist: Matrix [N_topics, N_topics] of distances between topics.
        mode: What algorith to use.
            String, one of:
                "none" - returns identity permutation;
                "hamilton" - solves TSP problem. If possible, uses LKH
                    algorithm. Otherwise uses simulated annealing.
                "hamilton_annealing" - solves TSP problem by simulated
                    annealing.
                "hamilton_exact" - solves TSP problem exactly by
                    branch-and-bound algoithm. It is exponentially complex,
                    used only for testing.
                "tsne" - builds tSNE embedding from topic space to R^1 (line),
                    returns order of topics' projections.
                "mds" - like tsne, but uses MDS embedding.
                "dendro" - builds dendrogram (greedy algorithm).
        model: ArtmModel object, for which spectrum is built. Needed only for
                logging and stroing performance data.
    Returns:
        Permutation - a list of length N_topics, with unique integers between 0
        and N_topics-1. This permutations should be applied to topics as
        columns of phi to obtain a spectrum.
    """
    start_time = time.time()

    if mode == "none":
        return [i for i in range(dist.shape[0])]
    if mode == "hamilton":
        from .hamilton_path import HamiltonPath
        hp = HamiltonPath(dist, caller=model)
        hp.solve()
        perm = hp.path
    elif mode == "hamilton_annealing":
        from .hamilton_path import HamiltonPath
        hp = HamiltonPath(dist, caller=model)
        hp.solve_annealing()
        perm = hp.path
    elif mode == "hamilton_exact":
        from .hamilton_path import HamiltonPath
        hp = HamiltonPath(dist, caller=model)
        hp.solve_branch()
        perm = hp.path
    elif mode == "tsne":
        from sklearn.manifold import TSNE
        tsne_model = TSNE(n_components=1, random_state=0, metric="precomputed")
        tsne_result = tsne_model.fit_transform(dist).reshape(-1)
        perm = np.argsort(tsne_result)
    elif mode == "mds":
        from sklearn.manifold import MDS
        mds = MDS(
            n_components=1,
            max_iter=3000,
            eps=1e-9,
            random_state=0,
            dissimilarity="precomputed",
            n_jobs=4)
        result = mds.fit_transform(dist).reshape(-1)
        perm = np.argsort(result)
    elif mode == "dendro":
        from algo.arranging.dendro_arranger import DendroArranger
        da = DendroArranger(dist)
        perm = da.arrange()
    else:
        raise ValueError("Unknown mode: %s" % mode)

    if model:
        from .quality import NDS, MNR
        model.NDS = NDS(dist, perm)
        model.log("NDS=%f" % model.NDS)
        model.log("MNR=%f" % MNR(dist, perm))
        model.log("Time=%f" % (time.time() - start_time))

    return list(perm)


def arrange_topics_phi(phi, metric="hellinger", mode="hamilton"):
    """Returns best permutation of topics for topics spectrum for phi matrix.

    Counts topic-topic distance matrix and calls get_arrangement_permutation()
    with "hamilton" mode by default.

    Args:
        phi: BigARTM Phi matrix, shows distributions of topics over dictionary.
            Stochastic numpy matrix of size[N_words, N_topics].
            phi[w,t] = p(w|t).
        metric: Metric to use for counting distancesstring.
            String, one of ["euclidean", "cosine", "manhattan",
            "hellinger", "jsd", "jaccard"].
        mode: What algorithm to use.
            For details see get_arrangement_permutation().
    Returns:
        Permutation - a list of length N_topics, with unique integers between 0
        and N_topics-1. This permutations should be applied to topics as
        columns of phi to obtain a spectrum.
    """
    metric = get_metric_by_name(metric)
    phi_t = phi.transpose()
    N = phi.shape[1]
    topic_distances = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            topic_distances[i][j] = metric(phi_t[i], phi_t[j])
    return get_arrangement_permutation(topic_distances, mode=mode)
