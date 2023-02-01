import datetime

import unittest

import numpy

if __name__ == "__main__":
    
    from borepy.scomp.arrays import ints

class TestIntArray(unittest.TestCase):

    def test_init_bool(self):

        x = ints(True)

        self.assertEqual(x[0],1)

        self.assertIsInstance(x,ints)

    def test_init_int(self):

        x = ints(int(5))

        self.assertIsInstance(x,ints)

    def test_init_float(self):

        x = ints(5.7)
        y = numpy.array([5],dtype=int)
        
        numpy.testing.assert_array_equal(x.tolist(),y)

        self.assertIsInstance(x,ints)

    def test_init_float_nan(self):

        x = ints(float('nan'))

        self.assertIsInstance(x,ints)

    def test_init_str_int(self):

        x = ints('5')
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_init_str_float(self):

        x = ints('5.6')

        self.assertIsInstance(x,ints)

    def test_init_str_characters(self):

        x = ints('john')
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_init_datetime_datetime(self):

        x = ints(datetime.datetime.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_init_datetime_date(self):

        x = ints(datetime.date.today())
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_init_list_empty(self):

        x = ints([])
        y = numpy.array([],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_init_list_int_none(self):

        x = ints([5,None],null=-100)

        self.assertIsInstance(x,ints)

    def test_init_list_int_null(self):

        x = ints([-99_999,5])
        y = numpy.array([False,True],dtype=bool)

        numpy.testing.assert_array_equal(x.isvalid,y)

        self.assertIsInstance(x,ints)

    def test_init_list_str_null(self):

        x = ints(["5","None"])
        y = numpy.array([5,-99_999],dtype=int)
        z = numpy.array([False,True],dtype=bool)

        self.assertEqual(x.null,-99_999)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())
        numpy.testing.assert_array_equal(x.isnull,z)

        self.assertIsInstance(x,ints)

    def test_init_numpy_ndarray_bool(self):

        x = ints(numpy.array([True,False]))

        self.assertIsInstance(x,ints)

    def test_init_numpy_ndarray_int(self):

        x = ints(numpy.array([1,2,3],dtype='int32'))

        self.assertIsInstance(x,ints)

    def test_init_numpy_ndarray_float_nan(self):

        x = ints(numpy.array([1.5,2.7,3,numpy.nan]))

        self.assertIsInstance(x,ints)

    def test_slicing(self):

        x = ints([5,-99_999],null=-99_999)

        y = x[1:]
        z = numpy.array([-99_999])

        self.assertEqual(type(y),ints)

        self.assertEqual(y.null,-99_999)

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())

        self.assertIsInstance(x,ints)

    def test_add_non_iterable(self):

        x = ints([5,None],null=-100)
        y = x+1
        q = x+None
        b = numpy.array([-100,-100])

        z = numpy.array([False,True])

        self.assertEqual(type(y),ints)

        numpy.testing.assert_array_equal(y.isnull,z)
        numpy.testing.assert_array_equal(q.tolist(),b.tolist())

        self.assertEqual(type(y.isnull),numpy.ndarray)
        self.assertEqual(y.null,-100)

        self.assertIsInstance(x,ints)

    def test_add_non_iterable_right_hand_side(self):

        x = ints([-99_999,5])

        y = numpy.array([3,7])
        z = numpy.array([5])

        numpy.testing.assert_array_equal((x+5).tolist(),(5+x).tolist())
        numpy.testing.assert_array_equal((x+y).tolist(),(y+x).tolist())
        numpy.testing.assert_array_equal((x+z).tolist(),(z+x).tolist())

        self.assertIsInstance(x,ints)

    def test_add_non_iterable_inplace(self):

        x = ints([-100,5],null=-100)
        x += 1
        y = numpy.array([-100,6])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,ints)

    def test_add_iterable(self):

        x = ints([5,None],null=-100)
        y = x+numpy.array([5,7])
        q = x+ints([None,5],null=-100)

        z = numpy.array([10,-100])
        t = numpy.array([-100,-100])

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())
        numpy.testing.assert_array_equal(q.tolist(),t.tolist())

        self.assertEqual(type(y),ints)

        self.assertIsInstance(x,ints)

if __name__ == "__main__":

    unittest.main()
