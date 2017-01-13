from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
 
def start_page(request):
    return render(request, 'index.html')

def settings_page(request):
	template = loader.get_template('settings.html')
	themes = ["dark", "light"]
	context = Context({'themes': themes, 
						'user':request.user})
	return HttpResponse(template.render(context))  
	