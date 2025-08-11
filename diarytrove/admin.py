from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Profile, Memory, MemoryMedia

# Change admin page headers
admin.site.site_header = _("DiaryTrove Administration")
admin.site.site_title = _("DiaryTrove Admin Portal")
admin.site.index_title = _("Welcome to the DiaryTrove Administration Interface")

# Register your models here.
class ProfileInLine(admin.TabularInline):
    model = Profile
    can_delete = False


class UserAdminCustom(UserAdmin):
    """
    Keep the default admin entries with a few additions
    """
    inlines = [ProfileInLine]
    list_display = ["username", "email", "is_staff"]


class MemoryMediaInLine(admin.TabularInline):
    model = MemoryMedia
    extra = 0


class MemoryAdmin(admin.ModelAdmin):
    """
    Manage user memories
    """
    fieldsets = [
        (_("General"), {"fields": ["owner", "title", "content"]}),
        (_("Information"), {"fields": ["date","lock_time"]}),
        (_("Additional fields"), {"fields": ["mood"]}),
    ]
    inlines = [MemoryMediaInLine]
    list_display = ["title", "owner", "date", "mood"]
    list_filter = ["owner", "date", "mood"]
    search_fields = ["title", "content"]


# Register admin stuff
admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)

# Register app models
admin.site.register(Memory, MemoryAdmin)
