import artm
batch_vectorizer = artm.BatchVectorizer(data_path = "{{batches_folder}}", data_format = 'batches')
dictionary = artm.Dictionary()
dictionary.load_text("{{dictionary_file}}")
model = artm.ARTM(num_document_passes=10, num_topics = 9, cache_theta=True)
model.initialize(dictionary = dictionary)
model.fit_offline(batch_vectorizer = batch_vectorizer, num_collection_passes = 10)
model.get_phi().to_pickle("{{phi_file}}")
model.get_theta().to_pickle("{{theta_file}}")