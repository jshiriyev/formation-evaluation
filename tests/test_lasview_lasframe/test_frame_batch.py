import unittest

import numpy

from borepy import Batch

class TestFrame(unittest.TestCase):

    def test_transpose_one_dim(self):

        bc = Batch([1,2,3,4])

        bc = bc.transpose()

        self.assertListEqual(bc.tolist(),[[1],[2],[3],[4]])

    def test_transpose_two_dim_equal(self):

        bc = Batch([[1,2,3,4],[4,5,6,7]])

        bc = bc.transpose()

        self.assertListEqual(bc.tolist(),[[1,4],[2,5],[3,6],[4,7]])

    def test_transpose_two_dim_unequal(self):

        bc = Batch([[1,2,3],[4,5]])

        bc = bc.transpose()

        self.assertListEqual(bc.tolist(),[[1,4],[2,5],[3,None]])

        bc = Batch([[4,5],[1,2,3]])

        bc = bc.transpose()

        self.assertListEqual(bc.tolist(),[[4,1],[5,2],[None,3]])

        # self.assertEqual()

        # self.assertCountEqual()

        # numpy.testing.assert_array_equal()

if __name__ == "__main__":

    unittest.main()
