import vk
import os
import json


def download_wall(domain, dataset_folder):
    session = vk.Session() #'c9a2edf19ed42f0ee1ba6a768ad6de25016971d24589165769987567a92cabbb2364bf3f4c050a868969f')
    api = vk.API(session)
    posts = api.wall.get(domain = 'lurkopub_alive', offset = 13700, count=100)
    #print(len(posts))
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
                text_id = str(id) + ".txt"
                info[text_id] = dict()        
                info[text_id]["url"] = "https://vk.com/" + domain + "?w=wall" + str(post["from_id"]) + "_" + str(post["id"]) 
                info[text_id]["time"] = post["date"]
                text_file_name = os.path.join(docs_folder, text_id)
                with open(text_file_name, "w", encoding = 'utf-8') as f:
                    f.write(text)
        offset += 100
        print (offset)
        if len(posts) != 101:
            break 
        if offset == 1100:
            break
        
    with open(os.path.join(dataset_folder, "meta", "meta.json"), "wb") as f: 
        f.write(json.dumps(info).encode("UTF-8"))
    

     
if __name__ == "__main__":
    download_wall('lurkopub_alive', "D:\\visartm\\data\\datasets\\lurkopub1000")