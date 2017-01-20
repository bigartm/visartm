import numpy as np
from math import log




def dist_l1(phi):   
    topic_num = phi.shape[1]    
    words_count = phi.shape[0]    
    dist = np.zeros((topic_num, topic_num))
    
    for i in range (0, topic_num):
        for j in range (0, topic_num):
            dist[i][j] = sum(abs(phi[w][i] - phi[w][j]) for w in range(0, words_count))
    return dist

def dist_l2(phi):   
    topic_num = phi.shape[1]    
    words_count = phi.shape[0]    
    dist = np.zeros((topic_num, topic_num))
    
    for i in range (0, topic_num):
        for j in range (0, topic_num):
            dist[i][j] = sum((phi[w][i] - phi[w][j])**2 for w in range(0, words_count))
    return dist
    
    
def dist_cov(phi):   
    topic_num = phi.shape[1]    
    words_count = phi.shape[0]    
    dist = np.zeros((topic_num, topic_num))
    
    for i in range (0, topic_num):
        for j in range (0, topic_num):
            if i == j:
                dist[i][j] = 0
            else:
                dist[i][j] = - sum(phi[w][i] * phi[w][j] for w in range(0, words_count))
    return dist