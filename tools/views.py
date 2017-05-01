from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden

from algo.tools.vkloader import download_wall
import algo.tools.converters as conv
from django.conf import settings
from contextlib import contextmanager
from shutil import rmtree
from datetime import datetime
import os
import zipfile
import io

@contextmanager
def get_temp_folder():
	folder = os.path.join(settings.DATA_DIR, "temp", str(datetime.now().timestamp()))
	os.makedirs(folder) 
	yield folder
	rmtree(folder)

def tools_list(request):
	return render(request, 'tools/tools_list.html')
	
	
def vw2uci(request):
	if request.method == 'POST':
		with get_temp_folder() as folder:
			vw_file = os.path.join(folder, "vw") 
			docword_file = os.path.join(folder, "docword")
			vocab_file = os.path.join(folder, "vocab")			
			name = str(request.FILES['vw']).split(".")[0]
			with open(vw_file, 'wb+') as f:
				for chunk in request.FILES['vw'].chunks():
					f.write(chunk)
			
			conv.vw2uci(vw_file, docword_file, vocab_file)
			
			outfile = io.BytesIO()
			with zipfile.ZipFile(outfile, 'w') as zf:
				zf.write(docword_file, "docword.%s.txt" % name)
				zf.write(vocab_file, "vocab.%s.txt" % name)
				 
			zipped_file = outfile.getvalue()
			response = HttpResponse(zipped_file, content_type='application/octet-stream')
			response['Content-Disposition'] = 'attachment; filename=%s.uci.zip' % name
			return response
		
	return render(request, 'tools/vw2uci.html')

class Logger:
	def log(self, s):
		print(s)
	
def uci2vw(request):
	if request.method == 'POST': 		
		with get_temp_folder() as folder:
			docword_file = os.path.join(folder, "docword")
			vocab_file = os.path.join(folder, "vocab")
			try:
				name = str(request.FILES['docword']).split('.')[1]
			except:
				name = "dataset"
			output_file = os.path.join(folder, name + ".txt")
			
			with open(docword_file, 'wb+') as f:
				for chunk in request.FILES['docword'].chunks():
					f.write(chunk)
			with open(vocab_file, 'wb+') as f:
				for chunk in request.FILES['vocab'].chunks():
					f.write(chunk)
			
			if settings.DEBUG:
				logger = Logger()
			else:
				logger = None
			
			conv.uci2vw(docword_file, vocab_file, output_file, logger=logger)
			
			with open(output_file) as f:
				response = HttpResponse(f.read(), content_type='application/octet-stream')
			response['Content-Disposition'] = 'attachment; filename=%s.txt' % name
			return response
 
	return render(request, 'tools/uci2vw.html')

def vkloader(request):
	if request.method == 'POST':
		domain = request.POST['domain']
		cut = int(request.POST['cut'])
		with get_temp_folder() as folder:
			download_wall(domain, folder, cut=cut)
				
			outfile = io.BytesIO()
			with zipfile.ZipFile(outfile, 'w') as zf:
				for root, dirs, files in os.walk(folder):
					rel_path = root[len(folder)+1:]
					for file in files:
						zf.write(os.path.join(root, file), os.path.join(rel_path, file)) 

			zipped_file = outfile.getvalue()
			response = HttpResponse(zipped_file, content_type='application/octet-stream')
			response['Content-Disposition'] = 'attachment; filename=%s.zip' % domain
			return response
		
	return render(request, 'tools/vkloader.html')