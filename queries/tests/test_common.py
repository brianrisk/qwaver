from django.test import TestCase

from queries.common.string_formatting import sanitize_name


class ViewTests(TestCase):

    def test_format_column(self):
        assert sanitize_name("Tt_ ()@#$%^&29") == "tt__29"
