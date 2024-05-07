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