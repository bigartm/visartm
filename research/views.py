from django.shortcuts import render, redirect
from django.conf import settings
from django.http import (HttpResponseForbidden, HttpResponseNotFound,
                         HttpResponse)
from django.template import Context
import os
from threading import Thread
from datetime import datetime

from research.models import Research
from datasets.models import Dataset
from models.models import ArtmModel
from assessment.models import AssessmentProblem
import visartm.views as general_views
from django.contrib.auth.decorators import login_required, permission_required


def researches(request):
    context = {"researches": Research.objects.all().order_by("id")}
    context["datasets"] = Dataset.objects.all()
    return render(request, 'research/researches.html', Context(context))


@login_required
@permission_required("add_reserach")
def create_research(request):
    if request.method == 'POST':
        print(request.POST)
        research = Research()
        research.dataset = Dataset.objects.get(id=request.POST['dataset_id'])
        try:
            research.model = ArtmModel.objects.get(id=request.POST['model_id'])
        except BaseException:
            pass
        try:
            research.problem = AssessmentProblem.objects.get(
                id=request.POST['problem_id'])
        except BaseException:
            pass
        research.script_name = request.POST['script_name']
        research.researcher = request.user
        research.status = 1
        research.save()

        if settings.THREADING:
            t = Thread(target=Research.run, args=(research,), daemon=True)
            t.start()
        else:
            research.run()

        return redirect("/research/" + str(research.id) + "/")

    dataset = Dataset.objects.get(id=request.GET["dataset_id"])
    try:
        model = ArtmModel.objects.get(id=request.GET["model_id"])
    except BaseException:
        model = None

    models = ArtmModel.objects.filter(dataset=dataset)
    problems = AssessmentProblem.objects.filter(dataset=dataset)
    script_names = os.listdir(
        os.path.join(
            settings.BASE_DIR,
            "algo",
            "research"))
    script_names = [s for s in script_names if not s[0] == "_"]

    context = Context({"dataset": dataset,
                       "model": model,
                       "models": models,
                       "problems": problems,
                       "script_names": script_names})
    return render(request, "research/create_research.html", context)


def rerun_research(request):
    research = Research.objects.get(id=request.GET['id'])
    if research.researcher != request.user:
        return HttpResponseForbidden(
            "You are not authorized to rerun this report.")
    if research.sealed:
        return HttpResponseForbidden("Research is sealed.")

    research.start_time = datetime.now()
    research.finish_time = None
    research.status = 1
    research.save()

    if settings.THREADING:
        t = Thread(target=Research.run, args=(research,), daemon=True)
        t.start()
    else:
        research.run()
    return redirect("/research/" + str(research.id) + "/")


def show_research(request, research_id):
    research = Research.objects.get(id=research_id)
    if research.is_private and research.researcher != request.user:
        return HttpResponseForbidden(
            "You are not authorized to see this report.")

    if research.status == 3:
        error_message = research.error_message.replace("\n", "<br>")
        return general_views.message(
            request,
            ("Error during research.<br>%s<br>"
             "<a href='/research/rerun?id=%d'>Rerun</a>")
            % (error_message, research.id)
        )

    with open(research.get_report_file(), "r", encoding="utf-8") as f:
        response = HttpResponse(f.read(), content_type='text/html')
    '''
    if research.status == 1:
        response['Refresh'] = "10" '''
    return response


def get_picture(request, research_id, pic_id):
    path = os.path.join(
        settings.BASE_DIR,
        "data",
        "research",
        research_id,
        "pic",
        pic_id + ".png")
    with open(path, "rb") as f:
        return HttpResponse(f.read(), content_type="image/png")


def get_picture_eps(request, research_id, pic_id):
    path = os.path.join(
        settings.BASE_DIR,
        "data",
        "research",
        research_id,
        "pic",
        pic_id + ".eps")
    with open(path, "rb") as f:
        return HttpResponse(f.read(), content_type="application/eps")


def get_txt(request, research_id, txt_id):
    path = os.path.join(
        settings.BASE_DIR,
        "data",
        "research",
        research_id,
        "pic",
        txt_id + ".txt")
    with open(path, "r", encoding='utf-8') as f:
        response = HttpResponse(f.read(), content_type="text/plain")
        response['Content-Type'] = 'text/plain; charset=utf-8'
        return response


def view_script(request, script_name):
    path = os.path.join(
        settings.BASE_DIR,
        "algo",
        "research",
        script_name + ".py")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return HttpResponse(text, content_type='text/plain')
    else:
        return HttpResponseNotFound("No such script.")
