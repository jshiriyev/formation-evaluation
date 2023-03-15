import datetime

from dateutil import relativedelta

import unittest

import numpy
import pint

from datum import array
from datum import any2column
from datum import key2column

class TestDateArray(unittest.TestCase):

    def test_integer(self):

        a = array(5)
        # print(a,a.dtype,a.head,)

    def test_float_number(self):

        b = array(5.)
        # print(b,b.dtype,b.head)

    def test_string_number(self):

        c = array('5')
        # print(c,c.dtype,c.head)

    def test_string_characters(self):

        d = array('cavid')
        # print(d,d.dtype,d.head)

    def test_string_datetime(self):

        e = array('2022-02-28')
        # print(e,e.dtype,e.head)

    def test_datetime_datetime(self):

        f = array(datetime.datetime.today())
        # print(f,f.dtype,f.head)

    def test_datetime_date(self):

        g = array(datetime.date.today())
        # print(g,g.dtype,g.head)

    def test_none(self):

        h = array(None)
        # print(h,h.dtype,h.head,h.shape,h.size)

    def test_empty_list(self):

        i = array([])
        # print(i,i.dtype,i.head,i.shape,i.size)

    def _test_arange(self):

        arr_ = key2column('2022-05-01','2022-07-29',dtype='datetime64[s]')

        arr_true = numpy.array([
            datetime.date(2022,5,1),
            datetime.date(2022,6,1),
            datetime.date(2022,7,1)],
            dtype='datetime64[s]')

        # numpy.testing.assert_array_equal(arr_,arr_true)

if __name__ == "__main__":

    unittest.main()
