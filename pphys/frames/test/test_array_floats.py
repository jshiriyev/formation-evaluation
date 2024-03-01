import datetime

import unittest

import numpy

from borepy import linear

class TestFloatArray(unittest.TestCase):

    def test_integer(self):

        x = linear.array(5)

        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,linear.floats)

    def test_float_number(self):

        x = linear.array(5.)

        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,linear.floats)

    def test_string_number(self):

        x = linear.array('5')
        
        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,linear.floats)

    def test_string_characters(self):

        x = linear.array('cavid',ptype=float)

        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_string_datetime(self):

        x = linear.array('2022-02-28',ptype=float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_datetime_datetime(self):

        x = linear.array(datetime.datetime.today(),ptype=float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_datetime_date(self):

        x = linear.array(datetime.date.today(),ptype=float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_none(self):

        x = linear.array(None)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_empty_list(self):

        x = linear.array([])

        numpy.testing.assert_array_equal(x.tolist(),[])

        self.assertIsInstance(x,linear.floats)

    def test_arange(self):

        x = linear.floats.arange(5)

        numpy.testing.assert_array_equal(x,numpy.arange(5,dtype="float64"))

        self.assertEqual(x.dtype,numpy.dtype("float64"))
        self.assertIsInstance(x,linear.floats)

    def test_functions(self):

        x = linear.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([1,2,3,4,numpy.nan,7])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_addition(self):

        x = linear.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([2,3,4,5,numpy.nan,8])

        x = x+1

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_valids(self):

        x = linear.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([1,2,3,4,7])

        x = x.valids()

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

    def test_nanmin_nanmax(self):

        x = linear.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        self.assertEqual(x.min(),1)
        self.assertEqual(x.max(),7)

    def test_normalize(self):

        x = linear.array([1,2,3,11,None],ptype=float,null=-99.999)

        z = x.normalize()

        y = numpy.array([0.,0.1,0.2,1.0,numpy.nan,])

        numpy.testing.assert_array_equal(z.tolist(),y.tolist())

        self.assertIsInstance(x,linear.floats)

if __name__ == "__main__":

    unittest.main()
