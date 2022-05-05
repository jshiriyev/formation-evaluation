import unittest

import numpy as np

if __name__ == "__main__":
    import setup

from dataset import DataFrame

class TestData(unittest.TestCase):

    def test_unique(self):

        df = DataFrame()

        A = np.array([
            1,1,1,2,2,3,3,
            3,4,5,6,6,6,6
            ])

        B = np.array([
            "A","A","B","B","C","C","C",
            "C","C","D","E","F","F","F"
            ])

        df.set_running(A,B,initHeadersFlag=True)

        df.unique(header_indices=[0,1],inplace=True)

        np.testing.assert_array_equal(df.running[0],
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df.running[1],
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")
                       
if __name__ == "__main__":

    unittest.main()
