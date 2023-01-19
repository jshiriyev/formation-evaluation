import datetime

import unittest

import numpy

if __name__ == "__main__":
    import dirsetup

"""
assertEqual(a,b)                a==b
assertNotEqual(a,b)             a != b
assertTrue(x)                   bool(x) is True
assertFalse(x)                  bool(x) is False
assertIs(a,b)                   a is b
assertIs(a,b)                   a is b
assertIsNot(a, b)               a is not b
assertIsNone(x)                 x is None
assertIsNotNone(x)              x is not None
assertIn(a, b)                  a in b
assertNotIn(a, b)               a not in b
assertIsInstance(a, b)          isinstance(a, b)
assertNotIsInstance(a, b)       not isinstance(a, b)
"""

from arrays import integers

class TestArray(unittest.TestCase):

    def test_init_bool(self):

        x = integers(True)

        self.assertEqual(x[0],1)

        self.assertIsInstance(x,integers)

    def test_init_int(self):

        x = integers(int(5))

        self.assertIsInstance(x,integers)

    def test_init_float(self):

        x = integers(5.7)
        y = numpy.array([5],dtype=int)
        
        numpy.testing.assert_array_equal(x.tolist(),y)

        self.assertIsInstance(x,integers)

    def test_init_float_nan(self):

        x = integers(float('nan'))

        self.assertIsInstance(x,integers)

    def test_init_str_int(self):

        x = integers('5')
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_init_str_float(self):

        x = integers('5.6')

        self.assertIsInstance(x,integers)

    def test_init_str_characters(self):

        x = integers('john')
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_init_datetime_datetime(self):

        x = integers(datetime.datetime.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_init_datetime_date(self):

        x = integers(datetime.date.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_init_list_empty(self):

        x = integers([])
        y = numpy.array([],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_init_list_int_none(self):

        x = integers([5,None],null=-100)

        self.assertIsInstance(x,integers)

    def test_init_list_int_null(self):

        x = integers([-99_999,5])
        y = numpy.array([False,True],dtype=bool)

        numpy.testing.assert_array_equal(x.isvalid,y)

        self.assertIsInstance(x,integers)

    def test_init_list_str_null(self):

        x = integers(["5","None"])
        y = numpy.array([5,-99_999],dtype=int)
        z = numpy.array([False,True],dtype=bool)

        self.assertEqual(x.null,-99_999)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())
        numpy.testing.assert_array_equal(x.isnull,z)

        self.assertIsInstance(x,integers)

    def test_init_numpy_ndarray_bool(self):

        x = integers(numpy.array([True,False]))

        self.assertIsInstance(x,integers)

    def test_init_numpy_ndarray_int(self):

        x = integers(numpy.array([1,2,3],dtype='int32'))

        self.assertIsInstance(x,integers)

    def test_init_numpy_ndarray_float_nan(self):

        x = integers(numpy.array([1.5,2.7,3,numpy.nan]))

        self.assertIsInstance(x,integers)

    def test_slicing(self):

        x = integers([5,-99_999],null=-99_999)

        y = x[1:]
        z = numpy.array([-99_999])

        self.assertEqual(type(y),integers)

        self.assertEqual(y.null,-99_999)

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())

        self.assertIsInstance(x,integers)

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

        self.assertIsInstance(x,integers)

    def test_add_non_iterable_right_hand_side(self):

        x = integers([-99_999,5])

        y = numpy.array([3,7])
        z = numpy.array([5])

        numpy.testing.assert_array_equal((x+5).tolist(),(5+x).tolist())
        numpy.testing.assert_array_equal((x+y).tolist(),(y+x).tolist())
        numpy.testing.assert_array_equal((x+z).tolist(),(z+x).tolist())

        self.assertIsInstance(x,integers)

    def test_add_non_iterable_inplace(self):

        x = integers([-100,5],null=-100)
        x += 1
        y = numpy.array([-100,6])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,integers)

    def test_add_iterable(self):

        x = integers([5,None],null=-100)
        y = x+numpy.array([5,7])
        q = x+integers([None,5],null=-100)

        z = numpy.array([10,-100])
        t = numpy.array([-100,-100])

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())
        numpy.testing.assert_array_equal(q.tolist(),t.tolist())

        self.assertEqual(type(y),integers)

        self.assertIsInstance(x,integers)

if __name__ == "__main__":

    unittest.main()
