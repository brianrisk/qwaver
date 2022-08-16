from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView, DeleteView
)

from queries.models import Database
from queries.common.access import get_org_databases, user_can_access_database


class DatabaseListView(LoginRequiredMixin, ListView):
    model = Database
    template_name = 'queries/database_list.html'
    context_object_name = 'databases'

    def get_queryset(self):
        # https://stackoverflow.com/questions/9410647/how-to-filter-model-results-for-multiple-values-for-a-many-to-many-field-in-djan
        queries = Database.objects.filter(pk__in=get_org_databases(self))
        return queries


class DatabaseCreateView(LoginRequiredMixin, CreateView):
    model = Database
    fields = ['title', 'host', 'port', 'database', 'user', 'password']

    def get_context_data(self, **kwargs):
        # get the default context data
        context = super(DatabaseCreateView, self).get_context_data(**kwargs)
        # if the user organization has no database, indicate we're in the set-up flow
        if len(get_org_databases(self)) == 0:
            context['is_setup'] = True
        return context

    def get_success_url(self):
        return reverse('database-list')

    def form_valid(self, form):
        user = self.request.user
        if user.profile.selected_organization is None:
            messages.error(self.request, f'You need to first create an organization before you can create a database')
            return redirect('profile')
        else:
            form.instance.organization = user.profile.selected_organization
        # TODO: run "SELECT 1;" on database and set is_valid accordingly.
        #  Maybe only creating a connection is necessary?
        return super().form_valid(form)


class DatabaseEditView(LoginRequiredMixin, UpdateView):
    model = Database
    fields = ['title', 'host', 'port', 'database', 'user', 'password']

    def test_func(self):
        user_can_access_database(self.request.user, self.get_object())
        return True

    def get_success_url(self):
        return reverse('database-detail', args=[self.object.id])


class DatabaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Database

    def get_success_url(self):
        return reverse('database-list')

    def test_func(self):
        user_can_access_database(self.request.user, self.get_object())
        return True
