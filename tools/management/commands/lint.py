from django.core.management.base import BaseCommand
from django.conf import settings
import os

FOLDERS_TO_CHECK = [
    'accounts',
    'api',
    'assessment',
    'datasets',
    'tools',
    'visartm',
    'visual'
]
ALLOW_FIX = settings.DEBUG


class Command(BaseCommand):
    def handle(self, *args, **options):
        def find_errors(file):
            findings = os.popen("pycodestyle %s" % (file)).read().split("\n")
            if len(findings) <= 1:
                return []
            else:
                ret = []
                file_name_len = len(file)
                for finding in findings[:-1]:
                    ret.append(finding[file_name_len + 1:])
                return ret

        OK = True
        files_to_check = []
        for folder in FOLDERS_TO_CHECK:
            app_path = os.path.join(settings.BASE_DIR, folder)
            for (root, dirs, files) in os.walk(app_path):
                if ("__" in root or "migrations" in root):
                    continue
                for file in files:
                    if (".py" in file) and not ("__" in file):
                        files_to_check.append(os.path.join(root, file))

        for file in files_to_check:
            errors = find_errors(file)
            if (len(errors) > 0 and ALLOW_FIX):
                os.popen("autopep8 -i -a -a %s" % (file)).read()
                errors = find_errors(file)
            if (len(errors) > 0):
                print(file)
                OK = False
                for error in errors:
                    print("  " + error)
