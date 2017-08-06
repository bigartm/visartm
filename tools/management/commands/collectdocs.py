from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
import os


class Command(BaseCommand):
    def handle(self, *args, **options):
        input_path = os.path.join(settings.BASE_DIR, "templates", "docs")
        output_path = os.path.join(settings.BASE_DIR, "static", "docs")
        for file_name in os.listdir(input_path):
            in_file = os.path.join(input_path, file_name)
            out_file = os.path.join(output_path, file_name)

            if not os.path.exists(out_file) or (
                    os.path.getmtime(in_file) > os.path.getmtime(out_file)):
                with open(os.path.join(output_path, file_name), "w",
                          encoding="utf-8") as f:
                    f.write(render_to_string('docs/%s' % file_name))
                print("Collected: %s" % file_name)
