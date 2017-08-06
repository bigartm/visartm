import numpy as np


# Euclidean (L1) distance.
def euclidean(p, q):
    return np.linalg.norm(p - q)


# Cosine distance.
def cosine(p, q):
    return 1.0 - (np.dot(p, q) / (np.linalg.norm(p) * np.linalg.norm(q)))


# Manhattan (L1) distance.
def manhattan(p, q):
    return np.sum(np.abs(p - q))


# Hellinger distance.
def hellinger(p, q):
    _SQRT2 = np.sqrt(2)
    return euclidean(np.sqrt(p), np.sqrt(q)) / _SQRT2


# Jensen-Shannon Divergence.
def jsd(P, Q):
    from scipy.stats import entropy
    return entropy(0.5 * (P + Q)) - 0.5 * (entropy(P) + entropy(Q))


# Jaccard distance.
def jaccard(P, Q):
    N = len(P)
    eps = 1.0 / N
    P = P > eps
    Q = Q > eps
    union = (P | Q).sum()
    intersection = (P & Q).sum()
    return 1.0 - (1.0 * intersection) / union


# Chebyshev distance.
def chebyshev(p, q):
    return np.max(np.abs(p - q))


metrics_list = [
    "euclidean",
    "cosine",
    "manhattan",
    "hellinger",
    "jsd",
    "jaccard",
    "chebyshev"]

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
