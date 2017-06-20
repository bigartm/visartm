#!/usr/bin/env python
import os
import sys
import shutil

if __name__ == "__main__":
	# Creating settings.py from settings_default.py
	base_dir = os.path.dirname(os.path.abspath(__file__))
	settings_file = os.path.join(base_dir, "visartm", "settings.py")
	settings_default_file = os.path.join(base_dir, "visartm", "settings_default.py")
	if not os.path.exists(settings_file):
		shutil.copyfile(settings_default_file, settings_file)
		
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "visartm.settings")
	try:
		from django.core.management import execute_from_command_line
	except ImportError:   
		try:
			import django
		except ImportError:
			raise ImportError("Couldn't import Django.")
		raise
	execute_from_command_line(sys.argv)
