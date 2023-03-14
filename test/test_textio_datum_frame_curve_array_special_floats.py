import datetime

from dateutil import relativedelta

import unittest

import numpy

from borepy import array

class TestArray(unittest.TestCase):

    def test_integer(self):

        a = array(5,float)
        # print(a,a.dtype,a.head,)

    def test_float_number(self):

        b = array(5.,float)
        # print(b,b.dtype,b.head)

    def test_string_number(self):

        c = array('5',float)
        # print(c,c.dtype,c.head)

    def test_string_characters(self):

        d = array('cavid',float)
        # print(d,d.dtype,d.head)

    def test_string_datetime(self):

        e = array('2022-02-28',float)
        # print(e,e.dtype,e.head)

    def test_datetime_datetime(self):

        f = array(datetime.datetime.today(),float)
        # print(f,f.dtype,f.head)

    def test_datetime_date(self):

        g = array(datetime.date.today(),float)
        # print(g,g.dtype,g.head)

    def test_none(self):

        h = array(None,float)
        # print(h,h.dtype,h.head,h.shape,h.size)

    def test_empty_list(self):

        i = array([],float)
        # print(i,i.dtype,i.head,i.shape,i.size)

    def _test_init(self):

        arr_ = key2column(5)
        numpy.testing.assert_array_equal(arr_,numpy.arange(5))

        arr_ = key2column(5.)
        numpy.testing.assert_array_equal(arr_,numpy.arange(5,dtype='float64'))

        arr_ = key2column('E')
        numpy.testing.assert_array_equal(arr_,numpy.array(['A','B','C','D','E']))

        arr_ = key2column('2022-05-01','2022-07-29',dtype='datetime64[s]')

        arr_true = numpy.array([
            datetime.date(2022,5,1),
            datetime.date(2022,6,1),
            datetime.date(2022,7,1)],
            dtype='datetime64[s]')

        # numpy.testing.assert_array_equal(arr_,arr_true)

        arr_ = any2column(('Python','NumPy','Great!'),dtype='str')
        arr2 = any2column(('Python','NumPy','Great!'))

        numpy.testing.assert_array_equal(
            arr_.vals,numpy.array(['Python','NumPy','Great!']))

        numpy.testing.assert_array_equal(arr_.vals,arr2.vals)

    def test_functions(self):

        values = array([1,2,3,4,None,7],float,null=-99.999)

        print(values)
        print(values+1)

        print(values.valids())

        print(values.min())
        print(values.max())

        print(values.normalize())

    def test_remove_thousand_separator(self):

        a1 = str2float("10 000,00",sep_decimal=",",sep_thousand=" ")
        a2 = str2float("10.000,00",sep_decimal=",",sep_thousand=".")
        a3 = str2float("10,000.00")

        self.assertEqual(a1,10000.,"could not remove thousand separator...")
        self.assertEqual(a2,10000.,"could not remove thousand separator...")
        self.assertEqual(a3,10000.,"could not remove thousand separator...")

if __name__ == "__main__":

    unittest.main()
