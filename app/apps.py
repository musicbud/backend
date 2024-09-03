from django.apps import AppConfig
from django.conf import settings
from neomodel import config

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL
        config.AUTO_INSTALL_LABELS = True
