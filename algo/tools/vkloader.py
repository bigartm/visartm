import os
import json


def download_wall(domain, dataset_folder, cut=1000000):
	import vk
	session = vk.Session()
	api = vk.API(session)
	info = dict() 
	docs_folder = os.path.join(dataset_folder, "documents")
	os.makedirs(docs_folder, exist_ok=True)
	os.makedirs(os.path.join(dataset_folder, "meta"), exist_ok=True)
	
	
	id = 0
	offset = 0 
	while True:
		posts = api.wall.get(domain=domain, offset = offset, count=100)
		for i in range(1, len(posts)):
			post = posts[i]
			text = post["text"].replace("<br>","\n")
			if len(text)>50:
				id += 1
				text_id = "%06d.txt" % id
				info[text_id] = dict()		
				info[text_id]["url"] = "https://vk.com/" + domain + "?w=wall" + str(post["from_id"]) + "_" + str(post["id"]) 
				info[text_id]["time"] = post["date"]
				text_file_name = os.path.join(docs_folder, text_id)
				with open(text_file_name, "w", encoding = 'utf-8') as f:
					f.write(text)
			if id == cut:
				break
		offset += 100
		print (offset)
		if len(posts) != 101:
			break 
		if id == cut:
			break
		
	with open(os.path.join(dataset_folder, "meta", "meta.json"), "wb") as f: 
		f.write(json.dumps(info).encode("UTF-8"))
	

	 
if __name__ == "__main__":
	download_wall('miptstream', "D:\\visartm\\data\\datasets\\miptstream", cut=50)