
# Create your test here.


# Create user_a
# Create user_b
# create org_a
# create UserOrganization_a with user_a and org_a
# create database_a that is part of org_a
# create query_a that is part of database_a
# create result_a that is from query_a

# TODO: Test that user_b cannot view, edit or delete result_a -- done
# TODO: Test that user_b cannot view, edit or delete query_a -- done
# TODO: Test that user_b cannot view, edit or delete database_a -- in progress
# TODO: Test that user_b cannot view, edit or delete org_a -- done

# TODO: check that user_a can do all of the above


from django.test import TestCase, client
from django.urls import reverse

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
        Verify the unathorized user will get forbidden error message if attempting to access
        org edit page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('organization-update', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_org_view(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        org page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('organization-detail', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_org_delete(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        org delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.delete(reverse('organization-delete', kwargs={'pk': self.organization.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_details(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        query view page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('query-detail', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_edit(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        query edit page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('query-update', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_query_delete(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        query delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.delete(reverse('query-delete', kwargs={'pk': self.query.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

    def test_unauthorized_user_result_details(self):
        """
        Verify the unathorized user will get forbidden error message if attempting to access
        query delete page.
        """
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('result-detail', kwargs={'pk': self.result.pk}))
        assert "Forbidden" in response.content.decode()
        assert response.status_code == 403

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
