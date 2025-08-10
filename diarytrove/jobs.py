from django.contrib.auth.models import User

from .models import Profile

from threading import Thread
import os
import time
import schedule
import traceback


def start_job_scheduler():
    """
    Start the job scheduler in a daemon thread when the django app starts
    """
    if os.environ.get("RUN_MAIN") != "true":
        return  # Prevent starting the scheduler multiple times in development
    
    job_thread = Thread(target=jobs)
    job_thread.daemon = True  # Avoid blocking shutdown
    job_thread.start()


def jobs():
    """
    Background job scheduler that runs scheduled tasks in threads
    """
    schedule.every(1).minutes.do(check_profiles)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"\n/!\\ Error in job scheduler: {e}:\n{traceback.format_exc()}")
        finally:
            time.sleep(1)


def check_profiles(user:User=None):
    """
    Make sure that each user has a profile
    """
    if user is not None:
        affected_users = [user]
    else:
        affected_users = User.objects.all()
    
    for affected_user in affected_users:
        if not hasattr(affected_user, "profile"):
            profile = Profile(user=affected_user)
            profile.save()
