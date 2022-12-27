import csv

from django.db import models
from django.db.models import ManyToManyField
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse

from users.models import Organization
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


# Database connection information
class Database(models.Model):
    MYSQL = 'MySQL'
    POSTGRES = 'PostgreSQL'
    REDSHIFT = 'Redshift'
    MARIADB = 'MariaDB'
    ORACLE = 'Oracle'
    MICROSOFT_SQL_SERVER = 'Microsoft SQL Server'
    SQLITE = 'SQLite'
    CHOICES = (
        (MYSQL, MYSQL),
        (POSTGRES, POSTGRES),
        (REDSHIFT, REDSHIFT),
        (MARIADB, MARIADB),
        (ORACLE, ORACLE),
        (MICROSOFT_SQL_SERVER, MICROSOFT_SQL_SERVER),
        (SQLITE, SQLITE)
    )
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING, default=1)
    title = models.CharField(max_length=256, default="", help_text='Can be any name you want such as "Transaction events"')
    host = models.CharField(max_length=256)
    port = models.IntegerField()
    database = models.CharField(max_length=256, default="", help_text="The name of the database on your server")
    user = models.CharField(max_length=256, help_text="Ideally with read-only permissions")
    password = models.CharField(max_length=256)
    platform = models.CharField(
        max_length=64,
        choices=CHOICES, default=MYSQL
    )
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_engine(self):
        if self.platform == self.MYSQL:
            engine = create_engine(f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        elif self.platform == self.ORACLE:
            engine = create_engine(f"oracle://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        elif self.platform == self.MICROSOFT_SQL_SERVER:
            engine = create_engine(f"mssql+pymssql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        elif self.platform == self.SQLITE:
            engine = create_engine(f"sqlite://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        else:
            engine = create_engine(f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}")
        return engine

    def test_connection(self):
        engine = self.get_engine()
        try:
            engine.connect()
        except SQLAlchemyError as err:
            return False
        return True


class Query(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=256, null=True, blank=True)
    database = models.ForeignKey(Database, on_delete=models.CASCADE, null=False, blank=False)
    query = models.TextField()
    date_created = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    run_count = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(default=None, null=True)
    last_run_date = models.DateTimeField(default=None, null=True)
    # https://stackoverflow.com/questions/34003865/django-reverse-query-name-clash
    latest_result = models.ForeignKey("queries.Result", related_name='+', on_delete=models.DO_NOTHING, null=True)
    # Set when a query is first run
    is_valid = models.BooleanField(default=False)
    # A running count for how many consecutive errors have happened recently.
    # Reset to 0 if the query is successfully executed
    recent_error_count = models.IntegerField(default=0)
    version = models.ForeignKey("queries.QueryVersion", related_name='+', on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse('query-detail', kwargs={'pk': self.pk})

    def get_params(self):
        return Parameter.objects.filter(query=self)

    def update_query_text(self, new_text, user, comment=""):
        if self.query != new_text:
            self.query = new_text
            version_number = self.get_version_number() + 1
            new_version = QueryVersion(
                query=self,
                version_number=version_number,
                query_text=new_text,
                user=user,
                comment=comment,
            )
            self.version = new_version
            new_version.save()
            self.save()
            return new_version
        else:
            return None

    def get_version_number(self):
        if self.version is None:
            return 1
        else:
            return self.version.version_number

    def get_latest_version(self):
        version_number = self.get_version_number()
        try:
            query_version = QueryVersion.objects.get(query=self, version_number=version_number)
        except QueryVersion.DoesNotExist:
            query_version = QueryVersion(
                query=self,
                version_number=version_number,
                query_text=self.query,
                user=self.author
            )
        return query_version

    def increment_success(self):
        version = self.get_latest_version()
        if version is not None:
            version.success_count += 1
            version.save()

    def increment_failure(self):
        version = self.get_latest_version()
        if version is not None:
            version.failure_count += 1
            version.save()


class QueryVersion(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    version_number = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    query_text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(default="")
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)


class Parameter(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, default="")
    default = models.CharField(max_length=256, blank=True, null=True)
    # if the user inputs a value for this field, then the template plus the value is inserted
    # e.g.: template_defined = "AND campaign_id = {v}"
    # whe the user inputs "54321", what is inserted in the query is "AND campaign_id = 54321"
    template = models.CharField(max_length=256, blank=True, null=True, help_text='for example: "AND timestamp > {v}"')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('query-detail', kwargs={'pk': self.query.pk})

    @property
    def form_name(self):
        return self.name.replace(" ", "_")


class Result(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, null=True)
    dataframe = models.TextField(null=True)
    table = models.TextField(null=True)
    single = models.CharField(max_length=64, null=True)
    image_encoding = models.CharField(max_length=16, null=True)
    chart = models.TextField(null=True)
    preview = models.TextField(null=True)
    last_view_timestamp = models.DateTimeField(null=True)
    view_count = models.IntegerField(default=1)
    version_number = models.IntegerField(default=1)
    query_text = models.TextField(null=True)


# the specific value for an input field
class Value(models.Model):
    parameter_name = models.CharField(max_length=64, default="")
    value = models.CharField(max_length=256, default="")
    result = models.ForeignKey(Result, on_delete=models.CASCADE)


class UserSearch(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    search = models.CharField(max_length=64, default="")


class QueryComment(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    comment = models.TextField(null=True)


class QueryError(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    error = models.TextField(null=True)


class LoadFile(models.Model):
    table_name = models.CharField(null=False, max_length=100,
                                  help_text='Only letters, numbers and underscore.')
    # https://www.geeksforgeeks.org/filefield-django-models/
    source_file = models.FileField(upload_to='uploaded_files',
                                   help_text='CSV file containing data for your table. CSV must contain header row.')
    source_url = models.CharField(max_length=256, null=True, blank=True,
                                  help_text='(Optional) If there is a web url where this data is hosted')
    database = models.ForeignKey(Database, on_delete=models.CASCADE, null=False, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True,
                                   help_text='(Optional) A description of the table contents')
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)

