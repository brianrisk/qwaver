from django.contrib import admin

from queries.models import LoadFile
from .models import Profile, UserOrganization, Invitation, Referral

admin.site.register(Profile)
admin.site.register(UserOrganization)
admin.site.register(Invitation)
admin.site.register(LoadFile)
admin.site.register(Referral)

