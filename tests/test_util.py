import unittest
import json
import os
import tempfile
import shutil

from ufotest.config import CONFIG
from ufotest.util import HTMLTemplateMixin
from ufotest.util import format_byte_size, get_folder_size


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


class TestFolderByteSizeFunctions(unittest.TestCase):

    def test_format_byte_size_basic(self):
        """
        If the function util.format_byte_size works heuristically how it is supposed to aka if it converts
        the byte values correctly.
        """
        # 1KB is 1024 bytes. This should also be the result of the function
        kb_bytes = 1024
        self.assertEqual(
            '1.00 KB',
            format_byte_size(kb_bytes, unit='KB')
        )
        # Also: Converting it to bytes should leave it with the original value
        self.assertEqual(
            '1024.00 B',
            format_byte_size(kb_bytes, unit='B')
        )
        # Testing for megabyte. If this works we can assume the rest also does
        mb_bytes = 1048576
        self.assertEqual(
            '1.00 MB',
            format_byte_size(mb_bytes, unit='MB')
        )

        self.assertEqual(
            '1024.00 KB',
            format_byte_size(mb_bytes, unit='KB')
        )

    def test_format_byte_size_without_unit(self):
        """
        Tests the util.format_byte_size method produces the correct string when setting the flag not to include the
        unit in the final string
        """
        value = 14234
        self.assertIn(
            'KB',
            format_byte_size(value, unit='KB')
        )

        self.assertNotIn(
            'KB',
            format_byte_size(value, unit='KB', include_unit=False)
        )
        # Actually, in that case we want the string to be just a number and as such it should castable into one
        self.assertEqual(
            value,
            float(format_byte_size(value, unit='B', include_unit=False))
        )

    def test_format_byte_size_wrong_unit(self):
        """
        If the method util.format_byte_size appropriately raises ValueError if a wrong
        """
        with self.assertRaises(ValueError):
            value = 10
            format_byte_size(value, unit='LB')

    def test_get_folder_size_basic(self):
        """
        If the function util.get_folder_size heuristically works by just checking if the return value is not zero for
        some folder
        """
        with tempfile.TemporaryDirectory() as folder_path:
            self.assertIsInstance(folder_path, str)

            # Now we create a sub folder in this temp folder and put in two files whose size we can control
            # and then in the end we are going to see if the calculated size matches the one we would expect
            test_folder_path = os.path.join(folder_path, 'test')
            os.mkdir(test_folder_path)
            self.assertTrue(os.path.exists(test_folder_path))
            self.assertTrue(os.path.isdir(test_folder_path))

            file_size = 10000
            file_path_1 = os.path.join(test_folder_path, 'file1')
            with open(file_path_1, mode='wb') as file:
                file.write(b'a' * file_size)

            file_path_2 = os.path.join(test_folder_path, 'file2')
            with open(file_path_2, mode='wb') as file:
                file.write(b'b' * file_size)

            actual_folder_size = get_folder_size(test_folder_path)
            print(actual_folder_size)
            # I am too lazy to determine the size it should have (there is also overhead and folder size and stuff).
            # But this range should be sufficiently accurate to determine if the function works at all.
            self.assertTrue(3 * file_size >= actual_folder_size >= 2 * file_size)
