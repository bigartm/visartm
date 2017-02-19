from django.shortcuts import render

def tools_list(request):
	return render(request, 'tools/tools_list.html')
	
	
def vw2uci(request):
	return render(request, 'tools/vw2uci.html')

def uci2vw(request):
	return render(request, 'tools/uci2vw.html')

def vkloader(request):
	return render(request, 'tools/vkloader.html')