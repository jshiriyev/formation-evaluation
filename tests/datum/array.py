import datetime

from dateutil import relativedelta

import unittest

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from datum import any2column
from datum import key2column

class TestArray(unittest.TestCase):

    def test_init(self):

        arr_ = key2column(5)
        numpy.testing.assert_array_equal(arr_,numpy.arange(5))

        arr_ = key2column(5.)
        numpy.testing.assert_array_equal(arr_,numpy.arange(5,dtype='float64'))

        arr_ = key2column('E')
        numpy.testing.assert_array_equal(arr_,numpy.array(['A','B','C','D','E']))

        arr_ = key2column('2022-05-01','2022-07-29')
        arr_true = numpy.array([
            datetime.date(2022,5,1),
            datetime.date(2022,6,1),
            datetime.date(2022,7,1)],
            dtype='datetime64[s]')

        numpy.testing.assert_array_equal(arr_,arr_true)

        arr_ = any2column(('Python','NumPy','Great!'),dtype='str')
        arr2 = any2column(('Python','NumPy','Great!'))

        numpy.testing.assert_array_equal(
            arr_.vals,numpy.array(['Python','NumPy','Great!']))

        numpy.testing.assert_array_equal(arr_.vals,arr2.vals)

if __name__ == "__main__":

    unittest.main()
