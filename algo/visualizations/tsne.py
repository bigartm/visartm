from datasets.models import Document
import numpy as np 
import json 
import os
from sklearn.manifold import TSNE

def visual(model, params):
	print ("Buildig t-SNE visualization for model " + str(model.id) + "...") 
	tsne_matrix_path = os.path.join(model.get_visual_folder(), "tsne_matrix.npy")
	
	try:
		tsne_matrix = np.load(tsne_matrix_path)
		print ("t-SNE matrix from cache.")
	except:
		theta_t = model.get_theta().transpose()
		tsne_model = TSNE(n_components=2, n_iter = 200, verbose =10)
		print ("Fitting t-SNE...")
		tsne_matrix = tsne_model.fit_transform(theta_t)  
		print ("t-SNE fit.")
		np.save(tsne_matrix_path, tsne_matrix)
	
	answer = []
	documents = Document.objects.filter(dataset = model.dataset).order_by("index_id")
	documents_count = tsne_matrix.shape[0]
	
	border_0 = tsne_matrix[0].copy()
	border_1 = tsne_matrix[0].copy()
	
	print(border_0)
	for i in range(documents_count):
		border_0[0] = min(border_0[0], tsne_matrix[i][0])
		border_1[0] = max(border_1[0], tsne_matrix[i][0])
		border_0[1] = min(border_0[1], tsne_matrix[i][1])
		border_1[1] = max(border_1[1], tsne_matrix[i][1])
	print("min",border_0)
	print("max",border_1)
	
	
	i = 0
	for document in documents:
		answer.append({"X": (tsne_matrix[i][0] - border_0[0]) / (border_1[0] - border_0[0]), 
					   "Y": (tsne_matrix[i][1] - border_0[1]) / (border_1[1] - border_0[1]), 
					   "id": document.id})
		i += 1
		
	return "docs = " + json.dumps(answer) + ";\n"