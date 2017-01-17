import os
import artm

dataset_name = "postnauka"
layers_count = 2
work_dir = os.getcwd()
uci_patch = os.path.join(work_dir, "data", "datasets", dataset_name, "UCI")
batches_folder = os.path.join(work_dir, "temp")

batch_vectorizer = artm.BatchVectorizer(data_path = uci_patch, 
                                        data_format = "bow_uci", 
                                        batch_size = 100,
                                        collection_name = dataset_name,
                                        target_folder = os.path.join(work_dir, "temp"))

dictionary = artm.Dictionary(name="dictionary")
dictionary.gather(batches_folder)

model = artm.ARTM(num_document_passes=10, num_topics=5)
model.cache_theta=True
model.initialize(dictionary)
model.fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 10)

#model = artm.hARTM(cache_theta=True, 
#                  num_document_passes=5)
#
#layers = [0 for i in range(layers_count)]
#
#layers[0] = model.add_level(num_topics = 5)
#layers[0].initialize(dictionary=dictionary)
#print("Layer 0 initialized.")
#layers[0].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 5)   
#print("Layer 0 fitted.")
#    		
#layers[1] = model.add_level(parent_level_weight = 0.1, num_topics = 10)
#layers[1].initialize(dictionary=dictionary)
#print("Layer 1 initialized.")
#layers[1].fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 5)  
#print("Layer 1 fitted.") 
			

