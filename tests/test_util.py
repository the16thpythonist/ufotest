import unittest
import json

from ufotest.config import CONFIG
from ufotest.util import HTMLTemplateMixin


class HelloWorldParagraph(HTMLTemplateMixin):

    HTML_TEMPLATE = "<p>{{ this.text }}</p>"

    def __init__(self):
        HTMLTemplateMixin.__init__(self)
        self.text = 'Hello World'

    def to_dict(self):
        return {
            **HTMLTemplateMixin.to_dict(self),
            'text': self.text
        }


class TestHTMLTemplateMixin(unittest.TestCase):

    def test_construction_basically_works(self):
        """
        If a new instance of a subclass of the mixin can be instantiated without errors
        """
        class Local(HTMLTemplateMixin):

            HTML_TEMPLATE = ""

        local = Local()
        self.assertIsInstance(local, Local)

    def test_to_html_basically_works(self):
        """
        If the html template rendering with the "to_html" method works in basic use case
        """
        class Local(HTMLTemplateMixin):

            HTML_TEMPLATE = "<p>{{ this.text }}</p>"

            def __init__(self):
                HTMLTemplateMixin.__init__(self)
                self.text = 'Hello World'

        local = Local()
        html = local.to_html()
        expected_html = f"<p>{local.text}</p>"
        self.assertEqual(expected_html, html)

    def test_html_from_dict_works(self):
        """
        If the rendering of the html template works if the object instance was converted to a dict.
        """
        class Local(HTMLTemplateMixin):

            HTML_TEMPLATE = "<p>{{ this.text }}</p>"

            def __init__(self):
                HTMLTemplateMixin.__init__(self)
                self.text = 'Hello World'

            def to_dict(self):
                return {
                    **HTMLTemplateMixin.to_dict(self),
                    'text': self.text
                }

        local = Local()
        local_dict = local.to_dict()
        html = Local.html_from_dict(local_dict)
        expected_html = f"<p>{local.text}</p>"
        self.assertEqual(expected_html, html)

    def test_rendering_html_from_loaded_json_string(self):
        """
        If an instance which has been exported to a JSON string and loaded into a dict can be rendered as html. This
        should not be different from just the dict version but just for completeness
        """
        local = HelloWorldParagraph()
        local_dict = local.to_dict()
        json_string = json.dumps(local_dict)
        del local, local_dict

        loaded_dict = json.loads(json_string)
        html = HTMLTemplateMixin.html_from_dict(loaded_dict)
        expected_html = "<p>Hello World</p>"
        self.assertEqual(expected_html, html)
