"""
Sample Test
"""

from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """ Test The calc Module"""
    def test_add_numbers(self):
        """Test that two numbers are added together"""
        result = calc.add(3, 8)

        self.assertEqual(result, 11)

    def test_subtract_numbers(self):
        """Test that values are subtracted and returned"""
        result = calc.subtract(5, 11)

        self.assertEqual(result, 6)
