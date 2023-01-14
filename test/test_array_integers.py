import datetime

import unittest

import numpy

if __name__ == "__main__":
    import dirsetup

from arrays import integers

class TestArray(unittest.TestCase):

    def test_init_string(self):

        x = integers(["5","None"])
        y = numpy.array([5,-99_999],dtype=int)
        z = numpy.array([False,True],dtype=bool)

        self.assertEqual(x.none,-99_999)

        numpy.testing.assert_array_equal(x,y)
        numpy.testing.assert_array_equal(x.isnone,z)

    def test_init_float(self):

        x = integers(5.)
        y = numpy.array([5],dtype=int)
        
        numpy.testing.assert_array_equal(x,y)

    def test_init_string_number(self):

        x = integers('5')
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x,y)

    def test_init_string_characters(self):

        x = integers('cavid')
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x,y)

    def test_init_datetime_datetime(self):

        x = integers(datetime.datetime.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x,y)

    def test_init_datetime_date(self):

        x = integers(datetime.date.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x,y)

    def test_init_empty_list(self):

        x = integers([])
        y = numpy.array([],dtype=int)

        numpy.testing.assert_array_equal(x,y)

    def test_slicing(self):

        x = integers([5,-99_999],none=-99_999)

        y = x[1:]
        z = numpy.array([-99_999])

        self.assertEqual(type(y),integers)

        self.assertEqual(y.none,-99_999)

        numpy.testing.assert_array_equal(y,z)

    def test_add_non_iterable(self):

        x = integers([5,None],none=-100)
        y = x+1
        q = x+None
        b = numpy.array([-100,-100])

        z = numpy.array([False,True])

        self.assertEqual(type(y),integers)

        numpy.testing.assert_array_equal(y.isnone,z)
        numpy.testing.assert_array_equal(q,b)

        self.assertEqual(type(y.isnone),numpy.ndarray)
        self.assertEqual(y.none,-100)

    def test_add_iterable(self):

        x = integers([5,None],none=-100)

        e = x+numpy.array([5,7])

        self.assertEqual(type(e),integers)

if __name__ == "__main__":

    unittest.main()
