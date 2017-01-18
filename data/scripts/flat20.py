import artm
model = artm.ARTM(num_document_passes=10, num_topics = 20, cache_theta=True)
model.initialize(dictionary = dictionary)
model.fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 10)