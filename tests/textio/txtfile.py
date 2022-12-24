import io

import unittest

if __name__ == "__main__":
    import dirsetup

from textio import txtfile
from textio import loadtxt
from textio import txtbatch

class TestTxtFile(unittest.TestCase):

    def test_init(self):

        pass

class TestLoadTxt(unittest.TestCase):

    def test_init(self):
    
        txt = "well date oil water gas\n" \
              " A01    1  12    24  36\n" \
              " A01    2  11    23  35\n" \
              " A01    3  10    22  34\n" \
              " A01    4   9    21  33\n" \
              " A01    5   8    20  32\n" \
              " A01    6   7    19  31\n" \
              " A01    7   6    18  30\n" \
              " A01    8   5    17  29\n" \
              " A01    9   4    16  28\n" \
              " A01   10   3    16  27\n" \
              " A01   11   2    14  26\n" \
              " A01   12   1    13  25\n" \
              " B02    1   8    15  25\n" \
              " B02    2   8    15  25\n" \
              " B02    3   8    15  25\n" \
              " B02    4   8    15  25\n" \
              " B02    5   8    15  25\n" \
              " B02    6   8    15  25\n" \
              " B02    7   8    15  25\n" \
              " B02    8   8    15  25\n" \
              " B02    9   8    15  25\n" \
              " B02   10   8    15  25\n" \
              " B02   11   8    15  25\n" \
              " B02   12   8    14  25\n" \

        txtfile = io.StringIO(txt)

        prod = loadtxt(txtfile,skiprows=1,headline=0)

        self.assertListEqual(prod.frame["date"].vals[:3].tolist(),[1,2,3.])
        self.assertListEqual(prod.frame.heads,["well","date","oil","water","gas"])
        self.assertListEqual(list(prod.frame.shape),[24,5])

class TestTxtBatch(unittest.TestCase):

    def __init__(self):

        pass

if __name__ == "__main__":

    unittest.main()