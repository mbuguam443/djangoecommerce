import os
import sys

# path to your project folder
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "appwork.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()