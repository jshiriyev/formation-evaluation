import unittest

import numpy

if __name__ == "__main__":
    import dirsetup

from arrays import integers

class TestArray(unittest.TestCase):

    def test_integer(self):

        a = integers(["5","None"],none=-100)

        print(a.none)

        print(a)

        print(a.isnone)

        print(a+1) # This should be corrected

        b = a+1

        print(type(b))

        print(b.isnone)
        print(type(b.isnone)) # This should be corrected

        print(b.none)

    # def test_float_number(self):

    #     b = array(5.)
    #     # print(b,b.dtype,b.head)

    # def test_string_number(self):

    #     c = array('5')
    #     # print(c,c.dtype,c.head)

    # def test_string_characters(self):

    #     d = array('cavid')
    #     # print(d,d.dtype,d.head)

    # def test_string_datetime(self):

    #     e = array('2022-02-28')
    #     # print(e,e.dtype,e.head)

    # def test_datetime_datetime(self):

    #     f = array(datetime.datetime.today())
    #     # print(f,f.dtype,f.head)

    # def test_datetime_date(self):

    #     g = array(datetime.date.today())
    #     # print(g,g.dtype,g.head)

    # def test_none(self):

    #     h = array(None)
    #     # print(h,h.dtype,h.head,h.shape,h.size)

    # def test_empty_list(self):

    #     i = array([])
    #     # print(i,i.dtype,i.head,i.shape,i.size)

    # def test_init(self):

    #     arr_ = key2column(5)
    #     numpy.testing.assert_array_equal(arr_,numpy.arange(5))

    #     arr_ = key2column(5.)
    #     numpy.testing.assert_array_equal(arr_,numpy.arange(5,dtype='float64'))

    #     arr_ = key2column('E')
    #     numpy.testing.assert_array_equal(arr_,numpy.array(['A','B','C','D','E']))

    #     arr_ = key2column('2022-05-01','2022-07-29',dtype='datetime64[s]')

    #     arr_true = numpy.array([
    #         datetime.date(2022,5,1),
    #         datetime.date(2022,6,1),
    #         datetime.date(2022,7,1)],
    #         dtype='datetime64[s]')

    #     # numpy.testing.assert_array_equal(arr_,arr_true)

    #     arr_ = any2column(('Python','NumPy','Great!'),dtype='str')
    #     arr2 = any2column(('Python','NumPy','Great!'))

    #     numpy.testing.assert_array_equal(
    #         arr_.vals,numpy.array(['Python','NumPy','Great!']))

    #     numpy.testing.assert_array_equal(arr_.vals,arr2.vals)

if __name__ == "__main__":

    unittest.main()
