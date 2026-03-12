import os
import sys
import django
from django.core.management import call_command

# Path to your project
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "appwork.settings")

# Setup Django
django.setup()

# Run migrations
try:
    print("🔄 Running makemigrations...")
    call_command("makemigrations")

    print("🚀 Running migrate...")
    call_command("migrate")

    print("✅ Migration completed successfully!")
except Exception as e:
    print("❌ Error running migrations:", str(e))
