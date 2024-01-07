import datetime

import unittest

import numpy
import pint

from datum import nones

class TestNones(unittest.TestCase):

    def test_nones(self):

        Nones = nones()
        Nones.datetime64 = numpy.datetime64('NaT')
        self.assertEqual(Nones.int,-99_999)

        Nones.int = 0.
        self.assertEqual(Nones.int,0)

        with self.assertRaises(AttributeError):
            Nones.dtypes

    def test_todict(self):

        Nones = nones()

        Nones.int = 0

        nones_dict = Nones.todict()

        nones_dict['none_float'] = -99999.999

        self.assertEqual(nones_dict["none_int"],0)
        self.assertEqual(nones_dict["none_float"],-99999.999)
        self.assertEqual(nones_dict["none_str"],"")
        self.assertEqual(numpy.isnan(nones_dict["none_datetime64"]),True)

        nones_dict = Nones.todict("int","str")

        self.assertEqual(len(nones_dict),2)

if __name__ == "__main__":

    unittest.main()
