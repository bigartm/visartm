from django.shortcuts import render, redirect
from django.template import RequestContext, Context, loader
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from models.models import ArtmModel
from datasets.models import Dataset
from assessment.models import AssessmentProblem, AssessmentTask, ProblemAssessor
from research.models import Research


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
			return HttpResponse("Disabled account. <a href='accounts/login'>Try again</a>.")
	else:
		return HttpResponse("Invalid login. <a href='accounts/login'>Try again</a>.")

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
		return HttpResponse("Your passwords don't match. <br><a href='/accounts/signup'>Try again</a>")
	
	try:
		user = User.objects.create_user(username, email, password)
		user.save()
	except:
		HttpResponse("Fail.")
		
	return HttpResponse("Registration complete.<br><a href='/accounts/login'>To login page</a>.")

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
					   
	return render(request, 'accounts/account.html', Context(context)) 
	
	
	
	
	
	
	
	
	