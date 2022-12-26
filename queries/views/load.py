import csv
import io
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView

from queries.common.access import get_org_databases, get_most_recent_database
from queries.common.string_formatting import sanitize_name, is_int, is_float, is_date
from queries.forms import UploadFileForm
from queries.models import LoadFile


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
        source_file = self.request.FILES['source_file']
        decoded_file = source_file.read().decode('utf-8')
        file_string = io.StringIO(decoded_file)
        data = list(csv.reader(file_string, delimiter=","))
        # TODO error if data has less than two rows
        table_name = sanitize_name(form.instance.table_name)
        create_table(data, table_name)
        form.instance.creator = self.request.user
        return super().form_valid(form)


def create_table(data, table_name):
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
            use_quotes.append(False)

    # Generate SQL Table command
    sql_table_command = f'CREATE TABLE IF NOT EXISTS {table_name} ('
    for i, column_name in enumerate(column_names):
        sql_table_command += f'{column_name} {data_types[i]}, '
    sql_table_command = sql_table_command[:-2] + ');'
    print(sql_table_command)

    # # Generate SQL Insert command
    # sql_insert_command = f"INSERT INTO {table_name} VALUES "
    # for row in csv_reader:
    #     sql_insert_command += '('
    #     for value in row:
    #         sql_insert_command += '"{}", '.format(value)
    #     sql_insert_command = sql_insert_command[:-2] + '), '
    # sql_insert_command = sql_insert_command[:-2] + ';'
    # print(sql_insert_command)


# drawn from: https://docs.djangoproject.com/en/4.1/topics/http/file-uploads/
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/')
    else:
        form = UploadFileForm()
    return render(request, 'queries/load_file_form.html', {'form': form})


def handle_uploaded_file(f):
    decoded_file = f.read().decode('utf-8')
    file_string = io.StringIO(decoded_file)
    data = list(csv.reader(file_string, delimiter=","))
    print(data[0])
    # for row in data:
    #     print(row)