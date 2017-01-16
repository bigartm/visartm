# -*- coding: utf-8 -*-
import os
import artm
import numpy as np
import json
import random
 
curFolder = os.getcwd() 
batches_folder = "D:\\artmonline\\data\\datasets\\postnauka\\batches"  
batch_vectorizer = artm.BatchVectorizer(data_path=batches_folder)
dictionary = artm.Dictionary(name="dictionary")
dictionary.load_text(os.path.join(batches_folder, "dict.txt"))
 

scores_list = [artm.TopTokensScore(name='TopTokens', num_tokens=10, class_id = "word")] 
                                   
#%%
topic_num = 10
model = artm.ARTM(scores = scores_list,
                  num_topics = topic_num,
                  topic_names=["topic0_" + str(t) for t in range(topic_num)],
                  theta_columns_naming = "id")
                  
model.regularizers.add(artm.DecorrelatorPhiRegularizer())
model.cache_theta = True

model.initialize(dictionary = dictionary)
#%%
model.fit_offline(batch_vectorizer = batch_vectorizer, 
                  num_collection_passes = 10)     
#%%
                  
topic_names = []

for topic_name in model.topic_names:
    topic_names.append(' '.join([w for w in model.score_tracker["TopTokens"].last_tokens[topic_name]]))

for i in range (0, topic_num):
    print (i,  topic_names[i])
#%%
phi = model.get_phi().values

from PhiMetrics import dist_l1, dist_l2, dist_cov

dist = dist_l2(phi)
#%%

from Hamilton import HamiltonPath
import matplotlib.pyplot as plt

hp = HamiltonPath(dist)


print ("Before, quality = ", hp.path_weight())
for i in range(0, topic_num):
    print (i, topic_names[i])

plt.imshow(dist, interpolation='nearest')
plt.show()

 
hp.cut_branch=2
hp.solve_branch()
best_permutation = hp.get_path()
inv_perm = hp.get_inverse_permutation()
print ("Quality = ", hp.path_weight())
for i in range(0, topic_num):
    print (i, topic_names[best_permutation[i]])
    
plt.imshow(hp.permute_adj_matrix(), interpolation='nearest')
plt.show()
 


   