import csv
import io
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView

from queries.views.result import *
from queries.common.access import get_org_databases, get_most_recent_database
from queries.common.string_formatting import sanitize_name, is_int, is_float, is_date
from queries.models import LoadFile, Query


class LoadFileCreateView(LoginRequiredMixin, CreateView):
    model = LoadFile
    fields = ['table_name', 'database', 'source_file']
    template_name = 'queries/load_file_form.html'
    success_url = '/'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['database'].queryset = get_org_databases(self)
        form.fields['database'].initial = get_most_recent_database(self)
        return form

    def form_valid(self, form):
        user = self.request.user
        # setting this user as creator
        form.instance.creator = user
        source_file = self.request.FILES['source_file']
        file_name = os.path.basename(source_file.name)
        decoded_file = source_file.read().decode('utf-8')
        file_string = io.StringIO(decoded_file)
        data = list(csv.reader(file_string, delimiter=","))
        # TODO error if data has less than two rows
        # TODO throw exception if there are more than 1000 rows
        table_name = sanitize_name(form.instance.table_name)
        create_table(data, table_name, form.instance.database, user, self.request, file_name)
        return super().form_valid(form)


def create_table(data, table_name, database, user, request, file_name):
    columns_raw = data[0]
    # sanitize column names
    column_names = []
    for column in columns_raw:
        column_names.append(sanitize_name(column))
    # basing our data types on the values in the first row
    first_row = data[1]
    # the SQL data type for a given column
    data_types = []
    # if a given column data type requires quotes around the value
    use_quotes = []
    for value in first_row:
        if is_int(value):
            data_types.append('INTEGER')
            use_quotes.append(False)
        elif is_float(value):
            data_types.append('DECIMAL(20,10)')
            use_quotes.append(False)
        elif is_date(value):
            data_types.append('DATE')
            use_quotes.append(True)
        else:
            data_types.append('VARCHAR(255)')
            use_quotes.append(True)

    # Generate SQL Table command
    sql_table_command = f'CREATE TABLE IF NOT EXISTS {table_name} ('
    for i, column_name in enumerate(column_names):
        sql_table_command += f'{column_name} {data_types[i]}, '
    # removing the trailing comma and space, adding closing chars
    sql_table_command = sql_table_command[:-2] + ');'
    create_query = Query(
        title=f"create table {table_name}",
        description=f"creating table to load {file_name}",
        database=database,
        query=sql_table_command,
        author=user
    )
    create_query.save()
    create_query_result = get_result(request, create_query)

    # Generate SQL Insert command
    sql_insert_command = f"INSERT INTO {table_name} VALUES ("
    for column_name in column_names:
        sql_insert_command += f"{column_name}, "
    sql_insert_command = sql_insert_command[:-2] + ')\n'
    for row in data[1:]:
        sql_insert_command += '('
        for i, is_quoted in enumerate(use_quotes):
            if is_quoted:
                sql_insert_command += f"'{row[i]}', "
            else:
                sql_insert_command += f'{row[i]}, '
        sql_insert_command = sql_insert_command[:-2] + '), \n'
    sql_insert_command = sql_insert_command[:-3] + ';'
