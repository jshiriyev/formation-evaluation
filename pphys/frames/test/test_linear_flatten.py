import datetime

import unittest

import numpy

from borepy.scomp.arrays import flatten

class TestFlatten(unittest.TestCase):

    def test_integer(self):

        x = flatten(5)
        y = [5]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)

    def test_float_number(self):

        x = flatten(5.)
        y = [5.]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),float)

    def test_string_number(self):

        x = flatten('5')
        y = ['5']

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),str)

    def test_string_characters(self):

        x = flatten('cavid')
        y = ['cavid']

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),str)

    def test_string_datetime(self):

        x = flatten('2022-02-28')
        y = ['2022-02-28']

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),str)

    def test_datetime_datetime(self):

        time = datetime.datetime.today()

        x = flatten(time)
        y = [time]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),datetime.datetime)

    def test_datetime_date(self):

        time = datetime.date.today()

        x = flatten(time)
        y = [time]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),datetime.date)

    def test_none(self):

        x = flatten(None)
        y = [None]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(x[0],None)

    def test_empty_list(self):

        x = flatten([])
        y = []

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)

    def test_flat_list(self):

        x = flatten([5,6])
        y = [5,6]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)
        self.assertEqual(type(x[1]),int)

    def test_flat_tuple(self):

        x = flatten((5,6))
        y = [5,6]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)
        self.assertEqual(type(x[1]),int)

    def test_flat_sets(self):

        x = flatten({5,7})
        y = [5,7]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)
        self.assertEqual(type(x[1]),int)

    def test_flat_numpy_array(self):

        x = flatten(numpy.array([5]))
        y = [5]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)

    def test_nested_list(self):

        x = flatten(((1,2,3),(23,4)))
        y = [1,2,3,23,4]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)

    def test_triple_nested_list(self):

        x = flatten(((1,2,3,(2,5,6)),(23,4)))
        y = [1,2,3,2,5,6,23,4]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),int)

    def test_dictionary(self):

        dictionary = {}

        dictionary['name'] = 'John'
        dictionary['last'] = 'Smith'

        x = flatten(dictionary)
        y = ['name','last']

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),str)

    def test_dictionary_in_dictionary(self):

        dictionary = {}

        dictionary['name'] = 'John'
        dictionary['last'] = 'Smith'
        dictionary['numbers'] = {'first':[1,2,3],'second':[4,5,6]}

        x = flatten(dictionary)
        y = ['name','last','numbers']

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)
        self.assertEqual(type(x[0]),str)

    def test_mixed_data_types(self):

        var = [1,2.,'cavid',datetime.datetime.today()]

        x = flatten(var)
        y = [1,2.,'cavid',datetime.datetime.today()]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,y)

    def test_object_type_numpy_array(self):

        vara = ((1,2,3),(4,5))
        varb = numpy.array(vara,dtype='object')

        x = flatten(vara)
        y = flatten(varb)
        z = [1,2,3,4,5]

        self.assertIsInstance(x,list)
        self.assertListEqual(x,z)
        self.assertListEqual(y,z)

if __name__ == "__main__":

    unittest.main()