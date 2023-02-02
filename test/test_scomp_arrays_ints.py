import datetime

import unittest

import numpy

if __name__ == "__main__":
    
    from borepy.scomp.array import ints

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
        numpy.testing.assert_array_equal(q.view(numpy.ndarray),b)

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

    def test_ceil(self):

        x = ints([11,2,None],null=-22_222)

        y = x.ceil(1)
        z = x.ceil(2)
        w = x.ceil(3)

        yy = numpy.array([20,10,-22_222])
        zz = numpy.array([100,100,-22_222])
        ww = numpy.array([1000,1000,-22_222])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)
        numpy.testing.assert_array_equal(z.view(numpy.ndarray),zz)
        numpy.testing.assert_array_equal(w.view(numpy.ndarray),ww)

    def test_floor(self):

        x = ints([11,2,None])

        y = x.floor(1)
        z = x.floor(2)
        w = x.floor(3)

        yy = numpy.array([10,0,-99_999])
        zz = numpy.array([0,0,-99_999])
        ww = numpy.array([0,0,-99_999])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)
        numpy.testing.assert_array_equal(z.view(numpy.ndarray),zz)
        numpy.testing.assert_array_equal(w.view(numpy.ndarray),ww)

    def test_static_arange(self):

        x = ints._arange(0,10,step=5)

        xx = numpy.array([0,5,10])

        numpy.testing.assert_array_equal(x.view(numpy.ndarray),xx)

        y = ints._arange(0,10,size=3)

        yy = numpy.array([0,5,10])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)
        
    def test_static_repeat(self):

        x = ints._repeat([1,2,3,4,5,None],size=7)
        
        y = numpy.array([1,2,3,4,5,-99_999,1])

        numpy.testing.assert_array_equal(x.view(numpy.ndarray),y)

    def test_astype_float(self):

        x = ints([1,2,3,4,None,-222,99],null=-222)

        y = x.astype(float)

        yy = numpy.array([1,2,3,4,numpy.nan,numpy.nan,99])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)

    def test_astype_str(self):

        x = ints._repeat([1,2,3,4,5,None],size=7)

        y = x.astype("str")
        
        yy = numpy.array(["1","2","3","4","5","-99999","1"])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)

    def test_property_issorted(self):

        x = ints._repeat([1,2,3,4,5,None],size=7)

        self.assertEqual(x.issorted,False)

        y = ints._repeat([1,2,3,4,5,None],size=6)

        self.assertEqual(y.issorted,True)

    def test_comparison_operators(self):

        x = ints([1,2,3,4,None,-222,99],null=-222)

        y = x==1

        yy = numpy.array([True,False,False,False,False,False,False])

        z = x!=1

        zz = numpy.array([False,True,True,True,True,True,True])

        numpy.testing.assert_array_equal(y,yy)
        numpy.testing.assert_array_equal(z,zz)

    def test_numpy_sum(self):

        x = ints([1,2,3,4,None,-222,9],null=-222)

        self.assertEqual(numpy.sum(x),19)
        self.assertEqual(x.min(),1)
        self.assertEqual(x.max(),9)

    def test_numpy_argmin(self):

        x = ints([1,2,3,-222,None],null=-222)

        self.assertEqual(x[:2].null,-222)
        self.assertEqual(x.argmin(),0)

    def test_numpy_argmax(self):

        x = ints([1,2,3,-222,None],null=-222)
        
        self.assertEqual(x.argmax(),2)

if __name__ == "__main__":

    unittest.main()
