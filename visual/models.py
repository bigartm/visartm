from django.db import models
from models.models import ArtmModel
from datetime import datetime
import os
from django.conf import settings
import importlib.util
import traceback

class GlobalVisualization(models.Model):
	model = models.ForeignKey(ArtmModel, null = False)
	name = models.TextField(null = False, default = 'none')
	status = models.IntegerField(null = False, default = 0)  # 0-processing; 1-ready; 2-error. 
	start_time = models.DateTimeField(null=False, default = datetime.now)
	finish_time = models.DateTimeField(null=True)
	error_message = models.TextField(null = False, default = "")
	
	def render(self):		
		print("Rendering visualization " + self.name + " for model " + str(self.model.id) + "...")
		params = self.name.split('_')
		script_file_name = os.path.join(settings.VISUAL_SCRIPTS_DIR, params[0] + ".py")
		spec = importlib.util.spec_from_file_location("algo.visualizations." + params[0], script_file_name)
		visual_module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(visual_module)
		
		try:
			result = visual_module.visual(self.model, params)
		except:
			self.error_message = traceback.format_exc()
			self.status = 2
			self.finish_time = datetime.now()
			self.save()
			return 
	
		data_file_name = os.path.join(self.model.get_visual_folder(), self.name + ".txt")
		with open(data_file_name, "w", encoding = 'utf-8') as f:
			f.write(result)
		
		print("Render OK")
		self.error_message = "OK"
		self.finish_time = datetime.now()
		self.status = 1
		self.save()
	