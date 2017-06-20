from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
import os 
#from polls.models import Question as Poll

class Command(BaseCommand):
	def handle(self, *args, **options):
		input_path = os.path.join(settings.BASE_DIR, "templates", "docs")
		output_path = os.path.join(settings.BASE_DIR, "static", "docs")
		for file_name in os.listdir(input_path):
			#with open(os.path.join(input_path, file_name), "r", encoding="utf-8") as f:
			#	html_text = f.read()
			with open(os.path.join(output_path, file_name), "w", encoding="utf-8") as f:
				f.write(render_to_string('docs/%s' % file_name))
			print("Done: %s" % file_name)