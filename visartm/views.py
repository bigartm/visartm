from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from datetime import datetime
from django.conf import settings
import os

from datasets.models import Dataset
 
def start_page(request):
    return render(request, 'index.html', Context({
		'datasets' : Dataset.objects.filter(is_public=True),
		'no_footer' : True
	}))

def settings_page(request):  
	themes = [f.split('.')[0] for f in os.listdir(os.path.join(settings.BASE_DIR, "static", "themes")) if ".js" in f]
	context = Context({'themes': themes})
	return render(request, 'settings.html', context)  
	
def	help_page(request):
	return render(request, 'help.html')
	
def message(request, message):
	return render(request, 'message.html', Context({'message': message}))

def wait(request, message, begin, period = "5"):
	message = "<meta http-equiv='refresh' content='" + period + "'>" + message + \
		"<br>Elapsed: " + str((datetime.now() - begin).seconds) + " sec."
	return HttpResponse(message)
	