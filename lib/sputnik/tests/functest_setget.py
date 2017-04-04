import sputnik

from django.test import TestCase


class SetGetTest(TestCase):
    INT_VALUE = 12345
    FLOAT_VALUE = 123.45

    def setUp(self):
        self._keys = ['a', 'a a', 'a a a', 'a - a', 'a / a', 'a/[]/a', '"a a"', 'a "a a"']

    def _set(self, key, value):
        sputnik.set(key, value)

    def _get(self, key):
        return sputnik.get(key)

    def _test_for(self, value, cast):
        for key in self._keys:
            self._set(key, value)

            self.assertEqual(cast(self._get(key)), value)

    def test_set_integer(self):
        self._test_for(self.INT_VALUE, int)

    def test_set_float(self):
        self._test_for(self.FLOAT_VALUE, float)
