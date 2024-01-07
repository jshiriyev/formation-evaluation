import datetime

import unittest

import numpy

from frames import linear

class TestIntArray(unittest.TestCase):

    def test_init_bool(self):

        x = linear.array(True,ptype=int)

        self.assertEqual(x.tolist()[0],1)

        self.assertIsInstance(x,linear.ints)

    def test_init_int(self):

        x = linear.array(int(5),ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_float(self):

        x = linear.array(5.7,ptype=int)
        y = numpy.array([5],dtype=int)
        
        numpy.testing.assert_array_equal(x.tolist(),y)

        self.assertIsInstance(x,linear.ints)

    def test_init_float_nan(self):

        x = linear.array(float('nan'),ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_str_int(self):

        x = linear.array('5',ptype=int)
        y = numpy.array([5],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_init_str_float(self):

        x = linear.array('5.6',ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_str_characters(self):

        x = linear.array('john',ptype=int)
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_init_datetime_datetime(self):

        x = linear.array(datetime.datetime.today(),ptype=int)
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_init_datetime_date(self):

        x = linear.array(datetime.date.today(),ptype=int)
        y = numpy.array([-99_999],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_init_list_empty(self):

        x = linear.array([],ptype=int)
        y = numpy.array([],dtype=int)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_init_list_int_none(self):

        x = linear.array([5,None],null=-100,ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_list_int_null(self):

        x = linear.array([-99_999,5],ptype=int)
        y = numpy.array([False,True],dtype=bool)

        numpy.testing.assert_array_equal(x.isvalid,y)

        self.assertIsInstance(x,linear.ints)

    def test_init_list_str_null(self):

        x = linear.array(["5","None"],ptype=int)
        y = numpy.array([5,-99_999],dtype=int)
        z = numpy.array([False,True],dtype=bool)

        self.assertEqual(x.null,-99_999)

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())
        numpy.testing.assert_array_equal(x.isnull,z)

        self.assertIsInstance(x,linear.ints)

    def test_init_numpy_ndarray_bool(self):

        x = linear.array(numpy.array([True,False]),ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_numpy_ndarray_int(self):

        x = linear.array(numpy.array([1,2,3],dtype='int32'),ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_init_numpy_ndarray_float_nan(self):

        x = linear.array(numpy.array([1.5,2.7,3,numpy.nan]),ptype=int)

        self.assertIsInstance(x,linear.ints)

    def test_slicing(self):

        x = linear.array([5,-99_999],null=-99_999,ptype=int)

        y = x[1:]
        z = numpy.array([-99_999])

        self.assertEqual(type(y),linear.ints)

        self.assertEqual(y.null,-99_999)

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_add_non_iterable(self):

        x = linear.array([5,None],null=-100,ptype=int)
        y = x+1
        q = x+linear.array(None,ptype=int)
        b = numpy.array([-100,-100])

        z = numpy.array([False,True])

        self.assertEqual(type(y),linear.ints)

        numpy.testing.assert_array_equal(y.isnull,z)
        numpy.testing.assert_array_equal(q.view(numpy.ndarray),b)

        self.assertEqual(type(y.isnull),numpy.ndarray)
        self.assertEqual(y.null,-100)

        self.assertIsInstance(x,linear.ints)

    def test_add_non_iterable_right_hand_side(self):

        x = linear.array([-99_999,5],ptype=int)

        y = numpy.array([3,7])
        z = numpy.array([5])

        numpy.testing.assert_array_equal((x+5).tolist(),(5+x).tolist())
        numpy.testing.assert_array_equal((x+y).tolist(),(y+x).tolist())
        numpy.testing.assert_array_equal((x+z).tolist(),(z+x).tolist())

        self.assertIsInstance(x,linear.ints)

    def test_add_non_iterable_inplace(self):

        x = linear.array([-100,5],null=-100,ptype=int)
        x += 1
        y = numpy.array([-100,6])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.ints)

    def test_add_iterable(self):

        x = linear.array([5,None],null=-100,ptype=int)
        y = x+numpy.array([5,7])
        q = x+linear.array([None,5],null=-100,ptype=int)

        z = numpy.array([10,-100])
        t = numpy.array([-100,-100])

        numpy.testing.assert_array_equal(y.tolist(),z.tolist())
        numpy.testing.assert_array_equal(q.tolist(),t.tolist())

        self.assertEqual(type(y),linear.ints)

        self.assertIsInstance(x,linear.ints)

    def test_add_iterable_outer(self):

        x = linear.array([1,2,3,None],ptype=int)
        y = linear.array([None,7,8],ptype=int)

        z = numpy.array([[-99999,8,9],[-99999,9,10],[-99999,10,11],[-99999,-99999,-99999]])

        s = numpy.add.outer(x,y)

        numpy.testing.assert_array_equal(s,z)

    def test_ceil(self):

        x = linear.array([11,2,None],null=-22_222,ptype=int)

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

        x = linear.array([11,2,None],ptype=int)

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

        x = linear.ints.arange(0,10,step=5)

        xx = numpy.array([0,5,10])

        numpy.testing.assert_array_equal(x.view(numpy.ndarray),xx)

        y = linear.ints.arange(0,10,size=3)

        yy = numpy.array([0,5,10])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)
        
    def test_static_repeat(self):

        x = linear.repeat([1,2,3,4,5,None],size=7,ptype=int)
        
        y = numpy.array([1,2,3,4,5,-99_999,1])

        numpy.testing.assert_array_equal(x.view(numpy.ndarray),y)

    def test_astype_float(self):

        x = linear.array([1,2,3,4,None,-222,99],null=-222,ptype=int)

        y = x.astype(float)

        yy = numpy.array([1,2,3,4,numpy.nan,numpy.nan,99])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)

    def test_astype_str(self):

        x = linear.repeat([1,2,3,4,5,None],size=7,ptype=int)

        y = x.astype("str")
        
        yy = numpy.array(["1","2","3","4","5","-99999","1"])

        numpy.testing.assert_array_equal(y.view(numpy.ndarray),yy)

    def test_property_issorted(self):

        x = linear.repeat([1,2,3,4,5,None],size=7,ptype=int)

        self.assertEqual(x.issorted,False)

        y = linear.repeat([1,2,3,4,5,None],size=6,ptype=int)

        self.assertEqual(y.issorted,True)

    def test_comparison_operators(self):

        x = linear.array([1,2,3,4,None,-222,99],null=-222,ptype=int)

        y = x==1

        yy = numpy.array([True,False,False,False,False,False,False])

        z = x!=1

        zz = numpy.array([False,True,True,True,True,True,True])

        numpy.testing.assert_array_equal(y,yy)
        numpy.testing.assert_array_equal(z,zz)

    def test_numpy_sum(self):

        x = linear.array([1,2,3,4,None,-222,9],null=-222,ptype=int)

        self.assertEqual(numpy.sum(x),19)
        self.assertEqual(x.min(),1)
        self.assertEqual(x.max(),9)

    def test_numpy_argmin(self):

        x = linear.array([1,2,3,-222,None],null=-222,ptype=int)

        self.assertEqual(x[:2].null,-222)
        self.assertEqual(x.argmin(),0)

    def test_numpy_argmax(self):
        
        x = linear.array([1,2,3,-222,None],null=-222,ptype=int)
        
        self.assertEqual(x.argmax(),2)

    def test_numpy_cumsum(self):

        x = linear.array([1,2,3,4,None,7],ptype=int)

        xx = x.cumsum()
        yy = numpy.array([1,3,6,10,10,17])

        self.assertIsInstance(xx,linear.ints)

        numpy.testing.assert_array_equal(xx.view(numpy.ndarray),yy)

    def test_numpy_cumprod(self):

        x = linear.array([1,2,3,4,None,7],ptype=int)

        xx = x.cumprod()
        yy = numpy.array([1,2,6,24,24,168])

        self.assertIsInstance(xx,linear.ints)

        numpy.testing.assert_array_equal(xx.view(numpy.ndarray),yy)

    def test_mean(self):

        x = linear.array([1,2,3,4,None,6],ptype=int)

        self.assertEqual(x.mean(),3.2)

    def test_var(self):

        x = linear.array([1,2,3,4,None,6],ptype=int)

        self.assertEqual(x.var(),3.7)

    def test_get_item(self):

        x = linear.array([1,2,3,4,None,6],ptype=int)

        xx = x[4]+1
        yy = linear.array([None],ptype=int)
        
        numpy.testing.assert_array_equal(xx.view(numpy.ndarray),yy.view(numpy.ndarray))

    def test_comparison(self):

        x = linear.array([1,2,3,4,None],ptype=int,null=-500)

        y = numpy.array([True,True,True,True,False])
        z = numpy.array([False,False,False,False,False])

        numpy.testing.assert_array_equal(x>0,y)
        numpy.testing.assert_array_equal(x<0,z)

if __name__ == "__main__":

    unittest.main()
