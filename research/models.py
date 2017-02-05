from django.db import models
from datetime import datetime
import traceback
import os
from django.conf import settings
import matplotlib.pyplot as plt 

from datasets.models import Dataset
from models.models import ArtmModel
from assessment.models import AssessmentProblem
from django.contrib.auth.models import User	

class Research(models.Model):
	dataset = models.ForeignKey(Dataset, null = False)
	model = models.ForeignKey(ArtmModel, null = True)
	problem = models.ForeignKey(AssessmentProblem, null = True)
	researcher = models.ForeignKey(User, null = False) 
	script_name = models.TextField(null=False)
	start_time = models.DateTimeField(null=False, default = datetime.now)
	finish_time = models.DateTimeField(null=True)
	status = models.IntegerField(null=False, default = 0)
	error_message = models.TextField(null=True)
	
	def run(self):
		with open(self.get_report_file(), "w") as f:
			f.write("<html>\n<head></head>\n<body>")
			f.write("<h1>Research report</h1>\n")
			f.write("<p>Research id: %d<br>\n" % self.id)
			f.write("Dataset: %d<br>\n" % self.id)
			if self.model:
				f.write("Model: %s<br>\n" % str(self.model))
			if self.problem:
				f.write("Assesment problem: %s<br>\n" % str(self.problem))
			f.write("Script: %s<br>\n" % self.script_name)
			f.write("Researcher: %s<br>\n" % self.researcher.username)
			f.write("Research started: %s</p>\n" % self.start_time.strftime("%d.%m.%y %H:%M:%S"))
			f.write("<hr>\n")
			
		script_file_name = os.path.join(settings.BASE_DIR, "algo", "research", self.script_name)
		self.img_counter = 0

		
		try:
			with open(script_file_name) as f:
				code = compile(f.read(), script_file_name, "exec")		
			exec(code, {"research": self})
		except:
			self.status = 3
			self.error_message = traceback.format_exc()
			self.finish_time = datetime.now()
			self.save()
			return
		
		
		self.finish_time = datetime.now()
		self.status = 2
		self.save()
		
		with open(self.get_report_file(), "a") as f:
			f.write("<hr>\n")
			f.write("<p>Research finished: %s</p>\n" % self.finish_time.strftime("%d.%m.%y %H:%M:%S") )
			f.write("</body>\n</html>\n")
		
	
	def report_html(self, text):
		with open(self.get_report_file(), "a") as f:
			f.write(text + "\n")
	
	
	def report_text(self, text):
		with open(self.get_report_file(), "a") as f:
			f.write("<p>" + text + "</p>\n")
	
	def gca(self):
		self.figure = plt.figure()
		return self.figure.gca()
	
	def report_picture(self):
		self.img_counter += 1
		file_name = str(self.img_counter) + '.png'
		path = os.path.join(self.get_pic_folder(), file_name)
		self.figure.savefig(path)
		with open(self.get_report_file(), "a") as f:
			f.write("<div align='center'><img src='pic/%s'  /></div>\n" % file_name)	

	def report_table(self, table):
		with open(self.get_report_file(), "a") as f: 
			f.write('<table border="1" cellpadding="0" cellspacing="0">\n')
			for row in table:
				f.write("<tr>\n")
				for cell in row:
					f.write("<td>%s</td>\n" % str(cell))
				f.write("</tr>\n")
			f.write("</table>\n")
		
	def get_folder(self):
		path = os.path.join(settings.DATA_DIR, "research", str(self.id))
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path	 	
	
	def get_pic_folder(self):
		path = os.path.join(settings.DATA_DIR, "research", str(self.id), "pic")
		if not os.path.exists(path): 
			os.makedirs(path) 
		return path	 	
	
	def get_report_file(self):
		return os.path.join(self.get_folder(), "report.html")
	
	def __str__(self):
		return "Research %d (%s, %s)" % (self.id, str(self.dataset), self.script_name)
	
	def duration(self): 
		if self.finish_time:
			dt = self.finish_time - self.start_time
		else: 
			dt = datetime.now() - self.start_time
		seconds = dt.seconds
		return "{:02}:{:02}".format(seconds // 60, seconds % 60)

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from shutil import rmtree 
@receiver(pre_delete, sender=Research, dispatch_uid='research_delete_signal')
def remove_research_files(sender, instance, using, **kwargs):
	folder = instance.get_folder()
	# print("deleting folder " + folder)
	try:
		rmtree(folder)
	except:
		pass
		
from django.contrib import admin
admin.site.register(Research)

