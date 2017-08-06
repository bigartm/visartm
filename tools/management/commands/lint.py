'''
Checks .py source files for complience with PEP8 styleguide.

If called with '--fix', will try to fix each file with violations using
autopep8.
'''

from django.core.management.base import BaseCommand
from django.conf import settings
import os

FOLDERS_TO_CHECK = [
    'accounts',
    'algo',
    'api',
    'assessment',
    'datasets',
    'research',
    'models',
    'tools',
    'visartm',
    'visual'
]

FOLDERS_TO_CHECK = [os.path.join('algo','assessment')]

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            dest='fix',
            default=False,
            help='Automatically fix style violations.',
        )

    def handle(self, *args, **options):
        ALLOW_FIX = options['fix']

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
                self.stdout.write(file)
                OK = False
                for error in errors:
                    self.stdout.write("  " + error)
