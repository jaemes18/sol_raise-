from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """
        Import and connect signals when the app is ready.
        This ensures that signal handlers are registered when the app starts.
        """
        import api.signals