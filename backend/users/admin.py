from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User


@admin.register(User)
class MyAdmin(UserAdmin):
    # fields = ('name', 'first_name', 'email',)
    search_fields = ("email__startswith", "first_name__startswith")
    list_filter = ('email', 'first_name')
    list_display = ('username', 'first_name', 'last_name', 'email')


admin.site.unregister(Group)
