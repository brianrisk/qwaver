from django.contrib import admin

from queries.models import LoadFile
from .models import Profile, UserOrganization, Invitation

admin.site.register(Profile)
admin.site.register(UserOrganization)
admin.site.register(Invitation)
admin.site.register(LoadFile)

