from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'  # This should be unique across all your apps

    def ready(self):
        import app.models
        import app.db_models.parent_user
