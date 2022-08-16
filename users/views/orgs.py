from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView, DeleteView
)

from queries.common.access import user_can_access_org
from queries.models import Organization
from users.models import UserOrganization


class OrganizationListView(ListView):
    model = Organization
    template_name = 'queries/organization_list.html'
    context_object_name = 'orgs'

    def get_queryset(self):
        # TODO: is there a better way to do this with only one query instead of two?
        user_orgs = UserOrganization.objects.filter(user=self.request.user).values_list('organization', flat=True)
        orgs = Organization.objects.filter(pk__in=user_orgs)
        return orgs


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    fields = ['name']

    def get_context_data(self, **kwargs):
        # get the default context data
        context = super(OrganizationCreateView, self).get_context_data(**kwargs)
        # if the user has no selected organization, indicate we're in the set-up flow
        user = self.request.user
        if user.profile.selected_organization is None:
            context['is_setup'] = True
        return context

    def get_success_url(self):
        user = self.request.user
        # adding UserOrganization for user creating this org
        # so that the user hase access to it immediately
        user_org = UserOrganization.objects.create(user=user, organization=self.object)
        user_org.save()
        # checking if in setup flow
        is_setup = user.profile.selected_organization is None
        # making this the selected org for the user
        user.profile.selected_organization = self.object
        user.profile.save()
        if is_setup:
            return reverse('queries-home')
        return reverse('organization-list')


class OrganizationEditView(LoginRequiredMixin, UpdateView):
    model = Organization
    fields = ['name']

    def get_object(self, queryset=None):
        obj = super().get_object()
        user_can_access_org(self.request.user, obj)
        return obj

    def get_success_url(self):
        return reverse('organization-detail', args=[self.object.id])


# todo cannot delete org if the org is currently selected in user's profile
#  or anyone's profile for that matter!
#  for now I'm removing delete functionality until this is figured out
class OrganizationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Organization

    def get_object(self, queryset=None):
        obj = super().get_object()
        user_can_access_org(self.request.user, obj)
        return obj

    def test_func(self):
        return True

    def get_success_url(self):
        org = self.object
        UserOrganization.objects.filter(organization=org).delete()
        return reverse('organization-list')
