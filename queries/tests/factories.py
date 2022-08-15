
import factory
from django.db.models.signals import post_save
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText, FuzzyInteger

from queries.models import (
    Database,
    Parameter,
    Query,
    QueryComment,
    Result,
    UserSearch,
    Value
)
from users.models import Profile
from users.test.factories import OrganizationFactory, UserFactory


class DatabaseFactory(DjangoModelFactory):

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Sequence(lambda n: f'test-database-{n}')
    user = FuzzyText()
    port = FuzzyInteger(low=1000)
    host = FuzzyText()

    class Meta:
        model = Database


class QueryFactory(DjangoModelFactory):

    title = FuzzyText()
    description = FuzzyText()
    author = factory.SubFactory(UserFactory)
    database = factory.SubFactory(DatabaseFactory)

    class Meta:
        model = Query


class ParameterFactory(DjangoModelFactory):

    user = factory.SubFactory(UserFactory)
    query = factory.SubFactory(QueryFactory)
    name = factory.Sequence(lambda n: f'test-parameter-{n}')
    template = FuzzyText()

    class Meta:
        model = Parameter


class ResultFactory(DjangoModelFactory):

    user = factory.SubFactory(UserFactory)
    query = factory.SubFactory(QueryFactory)
    title = factory.Sequence(lambda n: f'test-title-{n}')
    dataframe = FuzzyText()
    table = FuzzyText()
    single = FuzzyText()
    image_encoding = FuzzyText()
    chart = FuzzyText()
    preview = FuzzyText()

    class Meta:
        model = Result


class QueryCommentFactory(DjangoModelFactory):

    user = factory.SubFactory(UserFactory)
    query = factory.SubFactory(QueryFactory)
    comment = factory.Sequence(lambda n: f'Comment-{n}')

    class Meta:
        model = QueryComment


class ValueFactory(DjangoModelFactory):

    result = factory.SubFactory(ResultFactory)
    parameter_name = factory.Sequence(lambda n: f'Parameter-{n}')
    value = factory.Sequence(lambda n: f'Value-{n}')

    class Meta:
        model = Value


class UserSearchFactory(DjangoModelFactory):

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    search = FuzzyText()

    class Meta:
        model = UserSearch


@factory.django.mute_signals(post_save)
class ProfileFactory(DjangoModelFactory):
    """
    Profile model factory.

    This factory is being created in queries app instead of users to avoid
    circular import error in Profile.
    """
    selected_organization = factory.SubFactory(OrganizationFactory)
    # We pass in profile=None to prevent UserFactory from creating another profile
    # (this disables the RelatedFactory)
    user = factory.SubFactory(UserFactory, profile=None)
    image = factory.django.ImageField()
    most_recent_database = factory.SubFactory(DatabaseFactory)

    class Meta:
        model = Profile
