from django.test import TestCase, Client 
import api.views as views
from datasets.models import Dataset, Document
from models.models import ArtmModel, Topic

from django.contrib.auth.models import User
import json

class ApiTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        # Create 2 users, 2 datasets, 2 models and 20 documents
        # user0 -> dataset0 (public) -> doc00 .. doc09 (id=1..10)
        # user1 -> dataset1 (private) -> doc10 .. doc19 (id=11.20)
        for i in range(2):
            user = User()
            user.username = "user" + str(i)
            user.save()
            dataset = Dataset()
            dataset.owner = user
            dataset.text_id = "dataset" + str(i)
            dataset.is_public = (i == 0)
            dataset.save()
            
            for j in range(10):
                document = Document()
                document.dataset = dataset
                document.index_id = j
                document.title = "doc" + str(i) + str(j)
                document.text = "text" + str(i) + str(j)
                document.snippet = "snippet" + str(i) + str(j)
                document.url = "url" + str(i) + str(j)
                document.save()
                
        # On second dataset create a model with one topic.

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_get_document_by_id(self): 
        c = Client()    
        response = c.get('/api/documents/get?ids=2')
        self.assertEqual(response.status_code, 200)
        
        response_obj = json.loads(response.content.decode("utf-8") )
        self.assertEqual(len(response_obj), 1)
        self.assertEqual(response_obj[0]["id"], 2)
        self.assertEqual(response_obj[0]["title"], "doc01")
        self.assertEqual(response_obj[0]["url"], "url01")
        self.assertEqual(response_obj[0]["snippet"], "snippet01")
        
    def test_get_documents_by_ids(self): 
        c = Client()    
        ids = [2,5,8,9,3,1]
        ids_str = ','.join([str(id) for id in ids])
        response = c.get('/api/documents/get?ids=' + ids_str)
        self.assertEqual(response.status_code, 200)
        
        response_obj = json.loads(response.content.decode("utf-8") )
        self.assertEqual(len(response_obj), len(ids))
        
        # In response documents are sorted by ids
        ids.sort()
        for i in range(len(ids)):
            self.assertEqual(response_obj[i]["id"], ids[i])

    def test_get_documents_by_dataset_id(self): 
        c = Client()     
        response = c.get('/api/documents/get?dataset_id=1')
        self.assertEqual(response.status_code, 200)
        
        response_obj = json.loads(response.content.decode("utf-8") )
        self.assertEqual(len(response_obj), 10)
        for i in range(10):
            self.assertEqual(response_obj[i]["id"], i+1)   
    
    def test_get_documents_by_dataset_id_with_offset(self): 
        c = Client()     
        offset = 3
        count = 4
        response = c.get('/api/documents/get?dataset_id=1&offset=%d&count=%d' %
                         (offset, count))
        self.assertEqual(response.status_code, 200)
        
        response_obj = json.loads(response.content.decode("utf-8") )
        self.assertEqual(len(response_obj), count)
        for i in range(count):
            self.assertEqual(response_obj[i]["id"], i+1+offset)   

        