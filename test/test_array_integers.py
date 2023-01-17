import datetime

import unittest

import numpy

if __name__ == "__main__":
    import dirsetup

from arrays import integers

class TestArray(unittest.TestCase):

    def test_init_null_integer(self):

        x = integers([-99_999,5])

        y = numpy.array([False,True],dtype=bool)

        numpy.testing.assert_array_equal(x.isvalid,y)

    def test_init_float(self):

        x = integers(5.)
        y = numpy.array([5],dtype=int)
        
        numpy.testing.assert_array_equal(x.tolist(),y)

    def test_init_string(self):

        x = integers(["5","None"])
        y = numpy.array([5,-99_999],dtype=int)
        z = numpy.array([False,True],dtype=bool)

        self.assertEqual(x.null,-99_999)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())
        numpy.testing.assert_array_equal(x.isnull,z)

    def test_init_string_number(self):

        x = integers('5')
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_init_string_characters(self):

        x = integers('cavid')
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_init_datetime_datetime(self):

        x = integers(datetime.datetime.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_init_datetime_date(self):

        x = integers(datetime.date.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_init_empty_list(self):

        x = integers([])
        y = numpy.array([],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_slicing(self):

        x = integers([5,-99_999],null=-99_999)

        y = x[1:]
        z = numpy.array([-99_999])

        self.assertEqual(type(y),integers)

        self.assertEqual(y.null,-99_999)

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())

    def test_add_non_iterable(self):

        x = integers([5,None],null=-100)
        y = x+1
        q = x+None
        b = numpy.array([-100,-100])

        z = numpy.array([False,True])

        self.assertEqual(type(y),integers)

        numpy.testing.assert_array_equal(y.isnull,z)
        numpy.testing.assert_array_equal(q.tolist(),b.tolist())

        self.assertEqual(type(y.isnull),numpy.ndarray)
        self.assertEqual(y.null,-100)

    def test_add_non_iterable_right_hand_side(self):

        x = integers([-99_999,5])

        y = numpy.array([3,7])
        z = numpy.array([5])

        numpy.testing.assert_array_equal((x+5).tolist(),(5+x).tolist())
        numpy.testing.assert_array_equal((x+y).tolist(),(y+x).tolist())
        numpy.testing.assert_array_equal((x+z).tolist(),(z+x).tolist())

    def test_add_non_iterable_inplace(self):

        x = integers([-100,5],null=-100)
        x += 1
        y = numpy.array([-100,6])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

    def test_add_iterable(self):

        x = integers([5,None],null=-100)
        y = x+numpy.array([5,7])
        q = x+integers([None,5],null=-100)

        z = numpy.array([10,-100])
        t = numpy.array([-100,-100])

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())
        numpy.testing.assert_array_equal(q.tolist(),t.tolist())

        self.assertEqual(type(y),integers)

if __name__ == "__main__":

    unittest.main()
