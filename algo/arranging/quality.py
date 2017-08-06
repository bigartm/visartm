import numpy as np


# Neigbor distances sum
def NDS(dist, perm):
    N = dist.shape[0]
    ans = 0
    for i in range(N - 1):
        ans += dist[perm[i]][perm[i + 1]]
    return ans


# Mean neigbour rank
def MNR(dist, perm):
    def rank(x, y):
        idx = np.argsort(dist[y])
        for i in range(len(idx)):
            if idx[i] == x:
                return i
    N = dist.shape[0]
    ranks = []
    for i in range(1, N):
        ranks.append(rank(perm[i - 1], perm[i]))
        ranks.append(rank(perm[i], perm[i - 1]))

    return np.mean(ranks)


# Distance-distance curve
def DDC(dist, perm):
    N = dist.shape[0]

    ans = np.zeros(N - 2)
    for l in range(1, N - 1):
        for i in range(0, N - l):
            ans[l - 1] += dist[perm[i]][perm[i + l]]
        ans[l - 1] /= (N - l)
    return ans


# Assessment-based metrics

def flatten_symmetric_matrix(X):
    ans = []
    N = X.shape[0]
    for i in range(N):
        for j in range(i + 1, N):
            ans.append(X[i][j])
    return np.array(ans)


# Assessment: Distancing penalty
def ADP(assessment_C, perm):
    N = len(perm)
    rev = [i for i in range(N)]
    for i in range(N):
        rev[perm[i]] = i

    ans = 0
    for i in range(N):
        for j in range(i + 1, N):
            ans += assessment_C[i][j] * (abs(rev[i] - rev[j]) - 1)
    return ans


# Assessment-metric correlation
def AMC(ass, dist):
    C = flatten_symmetric_matrix(ass)
    D = flatten_symmetric_matrix(dist)
    C = C - np.mean(C)
    D = D - np.mean(D)
    return np.dot(C, D) / np.sqrt(np.dot(C, C) * np.dot(D, D))


# Assessment: mean neigbor dissimilarity
def AMND(ass, perm):
    N = len(perm)
    sum = 0
    for i in range(N - 1):
        sum += ass[perm[i]][perm[i + 1]]
    return 1 - sum / (N - 1)

# Assessment: dissimilar neigbors part


def ADNP(ass, perm):
    N = len(perm)
    ans = 0
    for i in range(N - 1):
        if ass[perm[i]][perm[i + 1]] > 0:
            ans += 1
    return 1 - (1.0 * ans) / (N - 1)
