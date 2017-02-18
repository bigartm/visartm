"""
WSGI config for visartm project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "visartm.settings")

application = get_wsgi_application()


import research, models, datasets
research.models.on_start()
models.models.on_start()
datasets.models.on_start()
