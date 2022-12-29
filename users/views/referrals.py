from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView
)

from users.models import Referral


class ReferralListView(LoginRequiredMixin, ListView):
    model = Referral
    template_name = 'users/referral_list.html'

    def test_func(self):
        return self.request.user.is_superuser


class ReferralAbstract(LoginRequiredMixin):
    model = Referral
    fields = ['title', 'site', 'ref_code', 'url', 'description']

    def test_func(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        return reverse('referral-list')


class ReferralCreateView(ReferralAbstract, CreateView):
    """subclass"""


class ReferralEditView(ReferralAbstract, UpdateView):
    """subclass"""
