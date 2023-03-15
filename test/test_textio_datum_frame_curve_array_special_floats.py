import datetime

import unittest

import numpy

from borepy import reel

class TestFloatArray(unittest.TestCase):

    def test_integer(self):

        x = reel.array(5)

        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,reel.floats)

    def test_float_number(self):

        x = reel.array(5.)

        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,reel.floats)

    def test_string_number(self):

        x = reel.array('5')
        
        self.assertEqual(x.tolist()[0],5.)
        self.assertIsInstance(x,reel.floats)

    def test_string_characters(self):

        x = reel.array('cavid',float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_string_datetime(self):

        x = reel.array('2022-02-28',float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_datetime_datetime(self):

        x = reel.array(datetime.datetime.today(),float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_datetime_date(self):

        x = reel.array(datetime.date.today(),float)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_none(self):

        x = reel.array(None)
        y = numpy.array([numpy.nan])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_empty_list(self):

        x = reel.array([])

        numpy.testing.assert_array_equal(x.tolist(),[])

        self.assertIsInstance(x,reel.floats)

    def test_arange(self):

        x = reel.floats.arange(5)

        numpy.testing.assert_array_equal(x,numpy.arange(5,dtype="float64"))

        self.assertEqual(x.dtype,numpy.dtype("float64"))
        self.assertIsInstance(x,reel.floats)

    def test_functions(self):

        x = reel.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([1,2,3,4,numpy.nan,7])

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_addition(self):

        x = reel.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([2,3,4,5,numpy.nan,8])

        x = x+1

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_valids(self):

        x = reel.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        y = numpy.array([1,2,3,4,7])

        x = x.valids()

        numpy.testing.assert_array_equal(x.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

    def test_nanmin_nanmax(self):

        x = reel.array([1,2,3,4,None,7],ptype=float,null=-99.999)

        self.assertEqual(x.min(),1)
        self.assertEqual(x.max(),7)

    def test_normalize(self):

        x = reel.array([1,2,3,11,None],ptype=float,null=-99.999)

        z = x.normalize()

        y = numpy.array([0.,0.1,0.2,1.0,numpy.nan,])

        numpy.testing.assert_array_equal(z.tolist(),y.tolist())

        self.assertIsInstance(x,reel.floats)

if __name__ == "__main__":

    unittest.main()
