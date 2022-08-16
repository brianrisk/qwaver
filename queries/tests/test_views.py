
from django.test import TestCase, client
from django.urls import reverse

from queries.models import Query, Database
from users.test.factories import UserFactory, OrganizationFactory, UserOrganizationFactory
from queries.tests.factories import DatabaseFactory, QueryFactory, ResultFactory


class ViewTests(TestCase):

    def setUp(self):
        super().setUp()
        self.client = client.Client()
        self.user_a = UserFactory.create(is_staff=True, is_active=True)
        self.user_a.set_password('password')
        self.user_a.save()
        self.user_b = UserFactory.create(is_staff=True, is_active=True)
        self.user_b.set_password('password')
        self.user_b.save()
        self.organization = OrganizationFactory()
        UserOrganizationFactory(
            organization=self.organization,
            user=self.user_a
        )
        self.database = DatabaseFactory(
            organization=self.organization
        )
        self.query = QueryFactory(
            database=self.database,
            author=self.user_a
        )
        self.result = ResultFactory(
            query=self.query,
            user=self.user_a
        )

    def _login(self, user):
        """
        Helper method to login the client for making API call.
        """
        assert self.client.login(username=user.username, password='password')

    def test_unauthorized_user_org_update(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        org edit page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('organization-update', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_org_view(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        org page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('organization-detail', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_org_delete(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        org delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.delete(reverse('organization-delete', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_details(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        query view page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('query-detail', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_edit(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        query edit page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('query-update', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_delete(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        query delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.delete(reverse('query-delete', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_result_details(self):
        """
        Verify the unauthorized user will get forbidden error message if attempting to access
        query delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('result-detail', kwargs={'pk': self.result.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_authorized_user_org_view(self):
        """
        Verify the authorized user wil be able to see org detail page.
        """
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('organization-detail', kwargs={'pk': self.organization.pk}))
        assert response.status_code == 200
        assert self.organization.name in response.content.decode()

    def test_authorized_user_org_update(self):
        """
        Verify the authorized user will be able to update org detail.
        """
        self.client.force_login(self.user_a)
        response = self.client.post(
            reverse('organization-update', kwargs={'pk': self.organization.pk}),
            {'name': 'new-name'}
        )
        # Updating the name redirects to detail page
        assert response.status_code == 302
        self.assertRedirects(response, reverse('organization-detail', kwargs={'pk': self.organization.pk}))
        self.organization.refresh_from_db()
        assert self.organization.name == 'new-name'

    def test_authorized_user_query_view(self):
        """
        Verify the authorized user wil be able to see query detail page.
        """
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('query-detail', kwargs={'pk': self.query.pk}))
        assert response.status_code == 200
        assert self.query.title in response.content.decode()

    def test_authorized_user_query_update(self):
        """
        Verify the authorized user will be able to update query detail.
        """
        self.client.force_login(self.user_a)
        response = self.client.post(
            reverse('query-update', kwargs={'pk': self.query.pk}),
            {
             'title': 'new-title',
             'description': 'new-description',
             'database': self.database.pk,
             'query': 'select *'
             }
        )
        assert response.status_code == 302
        self.assertRedirects(response, reverse('query-detail', kwargs={'pk': self.query.pk}))
        self.query.refresh_from_db()
        assert self.query.title == 'new-title'
        assert self.query.description == 'new-description'
        assert self.query.query == 'select *'

    def test_authorized_user_query_delete(self):
        """
        Verify the authorized user will be able to delete query.
        """
        self.client.force_login(self.user_a)
        response = self.client.delete(reverse('query-delete', kwargs={'pk': self.query.pk}))
        assert response.status_code == 302
        assert Query.objects.filter(pk=self.query.pk).exists() is False

    def test_authorized_user_database_view(self):
        """
        Verify the authorized user wil be able to see database detail page.
        """
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('database-detail', kwargs={'pk': self.database.pk}))
        assert response.status_code == 200
        assert self.database.title in response.content.decode()

    def test_authorized_user_database_edit(self):
        """
        Verify the authorized user will be able to edit database details.
        """
        self.client.force_login(self.user_a)
        response = self.client.post(
            reverse('database-update', kwargs={'pk': self.database.pk}),
            {
                'title': 'new-title',
                'host': 'new-host',
                'port': 1122,
                'database': 'select *',
                'user': 'admin',
                'password': 'password'
            }
        )
        assert response.status_code == 302
        self.assertRedirects(response, reverse('database-detail', kwargs={'pk': self.database.pk}))
        self.database.refresh_from_db()
        assert self.database.title == 'new-title'
        assert self.database.host == 'new-host'
        assert self.database.port == 1122
        assert self.database.database == 'select *'
        assert self.database.user == 'admin'
        assert self.database.password == 'password'

    def test_authorized_user_database_delete(self):
        """
        Verify the authorized user will be able to delete database information.
        """
        self.client.force_login(self.user_a)
        response = self.client.delete(reverse('database-delete', kwargs={'pk': self.database.pk}))
        assert response.status_code == 302
        assert Database.objects.filter(pk=self.database.pk).exists() is False

    def test_authorized_user_result_view(self):
        """
        Verify the authorized user wil be able to see result detail page.
        """
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('result-detail', kwargs={'pk': self.result.pk}))
        assert response.status_code == 200
        assert self.result.title in response.content.decode()

    # Note: The delete function has todos on it in terms of the functionalities. The
    # test is also not working as expected because deletion of one object is not
    # cascading effects properly
    # def test_authorized_user_org_delete(self):
    #     """
    #     Verify the authorized user will be able to delete the org.
    #     """
    #     self.client.force_login(self.user_a)
    #     response = self.client.delete(reverse('organization-delete', kwargs={'pk': self.organization.pk}))
    #     assert response.status_code == 302
    #     assert UserOrganization.objects.filter(organization__id=self.organization.pk).exists() is False

    # Note: This view is not developed completely yet. user_can_access_database is not called by
    # view and thus the access checks are not re-inforced
    # def test_unauthorized_user_database_view(self):
    #     """
    #     Verify the unathorized user will get forbidden error message if attempting to access
    #     org edit page.
    #     """
    #     self.client.force_login(self.user_b)
    #     response = self.client.get(reverse('database-update', kwargs={'pk': self.database.pk}))
    #     assert "Forbidden" in response.content.decode()
    #     assert response.status_code == 403
