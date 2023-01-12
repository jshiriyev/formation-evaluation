import datetime

import unittest

import numpy

if __name__ == "__main__":
    import dirsetup

from arrays import flatten

class TestFlatten(unittest.TestCase):

    def test_integer(self):

        x = flatten(5)
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_float_number(self):

        x = flatten(5.)
        y = numpy.array([5.],dtype=float)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('float'))

    def test_string_number(self):

        x = flatten('5')
        y = numpy.array(['5'],dtype=str)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype.type,numpy.dtype('str').type)

    def test_string_characters(self):

        x = flatten('cavid')
        y = numpy.array(['cavid'],dtype=str)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype.type,numpy.dtype('str').type)

    def test_string_datetime(self):

        x = flatten('2022-02-28')
        y = numpy.array(['2022-02-28'],dtype=str)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype.type,numpy.dtype('str').type)

    def test_datetime_datetime(self):

        time = datetime.datetime.today()

        x = flatten(time)
        y = numpy.array([time],dtype='datetime64[s]')

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('datetime64[s]'))

    def test_datetime_date(self):

        time = datetime.date.today()

        x = flatten(time)
        y = numpy.array([time],dtype='datetime64[D]')

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('datetime64[D]'))

    def test_none(self):

        x = flatten(None)
        y = numpy.array([numpy.nan],dtype=float)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('float'))

    def test_empty_list(self):

        x = flatten([])
        y = numpy.array([],dtype=float)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('float'))

    def test_flat_list(self):

        x = flatten([5,6])
        y = numpy.array([5,6],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_flat_tuple(self):

        x = flatten((5,6))
        y = numpy.array([5,6],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_flat_sets(self):

        x = flatten({5,7})
        y = numpy.array([5,7],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_flat_numpy_array(self):

        x = flatten(numpy.array([5]))
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_nested_list(self):

        x = flatten(((1,2,3),(23,4)))
        y = numpy.array([1,2,3,23,4],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

    def test_triple_nested_list(self):

        x = flatten(((1,2,3,(2,5,6)),(23,4)))
        y = numpy.array([1,2,3,2,5,6,23,4],dtype=int)

        numpy.testing.assert_array_equal(x,y)
        self.assertEqual(x.dtype,numpy.dtype('int'))

if __name__ == "__main__":

    unittest.main()
