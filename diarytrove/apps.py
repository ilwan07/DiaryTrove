from django.apps import AppConfig


class DiarytroveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diarytrove'

    def ready(self):
        from .jobs import start_job_scheduler
        start_job_scheduler()
