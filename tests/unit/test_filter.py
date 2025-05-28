""" Test suite for Filter class """
import unittest

from re import error as RegexException

from ...models.filter import Filter

class TestFilter(unittest.TestCase):
    """ Test class """

    def test_success_on_valid_regex(self):
        """
        Test the init should pass on a valid regex
        """
        filter_obj = Filter("kytos[./](.*)", False, "Test description")
        self.assertTrue(filter_obj.search("kytos/mef_eline.test"))
        self.assertFalse(filter_obj.search("kronos/core.work"))

    def test_failure_on_invalid_regex(self):
        """
        Test that the init function should throw a re.error (RegexException)
        """
        with self.assertRaises(RegexException):
            Filter("kytos[./&^%][", False, "Invalid test")

    def test_as_dict_returns_all_fields(self):
        """
        Test that as_dict should return each field in the Filter object
        """
        filter_obj = Filter("kytos[./](.*)", False, "Test description")
        self.assertEqual(len(vars(filter_obj)), len(filter_obj.as_dict()))
