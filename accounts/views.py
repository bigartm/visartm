from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from models.models import ArtmModel
from datasets.models import Dataset
from assessment.models import AssessmentProblem, AssessmentTask, ProblemAssessor
from research.models import Research
from django.conf import settings
import visartm.views as general_views

def login_view(request):
	if request.method == 'GET':
		return render(request, 'accounts/login.html')

	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
			
	if user is not None:
		if user.is_active: 
			login(request, user)
			try:
				return redirect(request.GET["next"])
			except:
				return redirect("/") 
		else:
			return general_views.message(request, "Disabled account. <a href='/accounts/login'>Try again</a>.")
	else:
		return general_views.message(request, "Invalid login. <a href='/accounts/login'>Try again</a>.")

def logout_view(request):
	logout(request)
	return redirect("/") 
	
def signup(request):
	if request.method == 'GET':
		return render(request, 'accounts/signup.html')
		
	username = request.POST['username']
	password = request.POST['password']
	password_repeat = request.POST['password_repeat']
	email = request.POST['email']
	
	if password != password_repeat:
		return general_views.message(request, "Your passwords don't match. <br><a href='/accounts/signup'>Try again</a>")
	
	try:
		user = User.objects.create_user(username, email, password)
		
		# Granting permissions
		if settings.DEBUG == True:
			user.user_permissions.add(Permission.objects.get(codename='add_dataset'))
			user.user_permissions.add(Permission.objects.get(codename='add_model'))	
		user.save()
	except:
		HttpResponse("Fail.")
		
	return general_views.message(request, "Registration complete.<br><a href='/accounts/login'>To login page</a>.")

def account_view(request, user_name):
	account = User.objects.get(username = user_name)
	context = {"account": account}
	 
	if account == request.user:
		assessment_problems = []
		for entry in ProblemAssessor.objects.filter(assessor=account):
			assessment_problems.append({
				"problem": entry.problem,
				"tasks": AssessmentTask.objects.filter(assessor=account, problem=entry.problem, status=1),
				"supervise": (entry.problem.dataset.owner == account)
		})		
		context["public_datasets"] = Dataset.objects.filter(owner = account, is_public = True)
		context["private_datasets"] = Dataset.objects.filter(owner = account, is_public = False)
		context["assessment_problems"] = assessment_problems
		context["models"] = ArtmModel.objects.filter(author = account)
		context["researches"] = Research.objects.filter(researcher = account).order_by("id")
		
		
		print(account.user_permissions)
		permissions = []
		permissions.append({"name": "Create dataset", "codename":"add_dataset", "value": account.has_perm("add_dataset")})
		permissions.append({"name": "Create models and other", "codename":"add_artmmodel", "value": account.has_perm("add_artmmodel")})
		
		
		
		context["permissions"] = permissions				   
	return render(request, 'accounts/account.html', Context(context)) 
	

def sendmail(request):
	from django.core.mail import send_mail

	send_mail(
		'VisARTM',
		'Hello, %s. For some reason you have requested the test message. So, here it is.' % request.user.username,
		settings.EMAIL_HOST_USER,
		[request.user.email],
		fail_silently=False
	)
	
	return HttpResponse("Sent.")
		
	
	
	