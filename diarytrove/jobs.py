from django.apps import apps
from django.conf import settings
from django.utils import translation
from django.db.models import FileField, ImageField
from django.utils.translation import gettext as _

from .models import Profile, Memory
from .utils import send_email, check_profiles, memory_preview_image

from threading import Thread
from pathlib import Path
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
    schedule.every(6).hours.do(cleanup_private_media)
    schedule.every(30).minutes.do(send_memory_emails)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"\n/!\\ Error in job scheduler: {e}:\n{traceback.format_exc()}")
        finally:
            time.sleep(1)


def cleanup_private_media():
    """
    Deletes unreferences private media files
    """
    grace_seconds = 86400  # One day

    try:
        private_root = Path(settings.PRIVATE_MEDIA_ROOT)
    except Exception:
       print("PRIVATE_MEDIA_ROOT not configured, skipping cleanup.")
       return

    if not private_root.exists():
        print(f"Private media root {private_root} does not exist, skipping cleanup.")
        return

    # Get each referenced media
    referenced = []
    representative_storage = None

    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, (FileField, ImageField)):
                # Ensure we will use the correct storage implementation later
                if representative_storage is None:
                    representative_storage = getattr(field, "storage", None)

                # Collect referenced names from database efficiently
                qs = model.objects.exclude(**{f"{field.name}__isnull": True}).exclude(**{f"{field.name}": ""}).values_list(field.name, flat=True)
                for name in qs:
                    if not name:
                        continue
                    # Normalize to forward slashes for comparison with Path.as_posix()
                    referenced.append(str(name).lstrip("/"))

    # If we didn't discover a storage object, try to create a filesystem storage pointing to the root
    if representative_storage is None:
        try:
            from django.core.files.storage import FileSystemStorage
            representative_storage = FileSystemStorage(location=str(private_root))
        except Exception:
            representative_storage = None

    # Iterate files on disk and delete orphans older than a day
    now = time.time()
    for p in private_root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(private_root).as_posix()
        except Exception:
            # Can't relativize, skip for safety
            continue

        if rel in referenced:
            continue  # Still referenced in database

        # Check age to avoid deleting files that may be in-progress
        try:
            mtime = p.stat().st_mtime
        except Exception:
            # If we cannot read stat, skip
            print(f"Could not stat file {p}, skipping.")
            continue

        age = now - mtime
        if age < grace_seconds:
            continue  # Keep files which are too recent

        # Attempt deletion via storage API if available, else unlink
        try:
            if representative_storage is not None:
                if representative_storage.exists(rel):
                    representative_storage.delete(rel)
                else:
                    # Fallback to unlink if file exists
                    if p.exists():
                        p.unlink()
            else:
                # No storage object, use unlink
                p.unlink()
        except Exception:
            print(f"Failed to delete orphaned private media {p}")
    
    # Delete empty subfolders
    top_folders = ["memory_media"]  # Folders relative to the private media root
    for folder in top_folders:
        folder_path = private_root / folder
        if not folder_path.exists():
            continue
        # Remove empty folders recursively
        for subfolder in folder_path.rglob("*"):
            if subfolder.is_dir() and not any(subfolder.iterdir()):
                try:
                    subfolder.rmdir()  # Remove empty subdirectory
                except Exception:
                    print(f"Failed to remove empty subfolder {subfolder}")


def send_memory_emails():
    """
    Check for newly unlocked memories and send emails accordingly
    """
    # Get memories which can eventually be sent by email
    unsent_memories = Memory.objects.filter(mail_sent=False)
    memories:list[Memory] = [memory for memory in unsent_memories if memory.is_unlocked()]

    for memory in memories:
        # Check if the memory should be sent
        check_profiles(memory.owner)
        profile:Profile = memory.owner.profile
        if profile.mail_memory == 1 or (profile.mail_memory == 2 and memory.mood in memory.POSITIVE_MOODS):
            context = {"memory": memory, "content": memory.content.strip().split("\n"),
                       "mood_emoji": memory.MOODS[memory.mood-1][1]}
            # Get image data if there's one
            image = memory_preview_image(memory)
            attachments = []
            if image is not None:
                image_abs_path = settings.PRIVATE_MEDIA_ROOT / Path(image.file.name)
                image_name = image_abs_path.name
                context["image_name"] = image_name
                attachments.append(image_abs_path)

            # Send the memory by email
            with translation.override(memory.owner.profile.language):
                send_email(memory.owner, "unlocked_memory", _("A new memory was unlocked!"), context, attachments=attachments)
        memory.mail_sent = True
        memory.save()
