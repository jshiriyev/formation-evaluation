import datetime
import io
import logging
import os
import unittest

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from textio import dirmaster
from textio import header
from textio import loadtxt

class TestHeader(unittest.TestCase):

    def test_init(self):

        names = header(first=['John','Jessica'],last=['Hass','Yummy'])

        self.assertListEqual(names.parameters,['first','last'])
        self.assertListEqual(names.first,['John','Jessica'])
        self.assertListEqual(names.last,['Hass','Yummy'])

        self.assertEqual(names['john'].first,'John')
        self.assertEqual(names['john'].last,'Hass')

        self.assertEqual(names['jessica'].first,'Jessica')
        self.assertEqual(names['jessica'].last,'Yummy')

    def test_all(self):

        front = header(first_name="john",last_name="smith")

        self.assertEqual(front.first_name,["john"])
        self.assertEqual(front["john"].first_name,"john")
        self.assertEqual(front["john"].last_name,"smith")

        gloss = header(mnemonic=[],unit=[],value=[],description=[])

        start = {
            "unit"          : "M",
            "value"         : 2576.,
            "description"   : "it shows the depth logging started",
            "mnemonic"      : "START",
            }
        
        stop = {
            "mnemonic"      : "STOP",
            "unit"          : "M",
            "value"         : 2896.,
            "description"   : "it shows the depth logging stopped",
            }
        
        null = {
            "mnemonic"      : "NULL",
            "value"         : -999.25,
            "description"   : "null values",
            "unit"          : ""
            }

        fld = {
            "mnemonic"      : "FLD",
            "value"         : "FIELD",
            "description"   : "GUNESLI",
            "unit"          : ""
            }

        gloss.extend(start)
        gloss.extend(stop)
        gloss.extend(null)
        gloss.extend(fld)

        self.assertListEqual(gloss.value,["2576.0","2896.0","-999.25","FIELD"])
        self.assertListEqual(gloss.value[1:],["2896.0","-999.25",'FIELD'])

class TestTxt(unittest.TestCase):

    def test_init(self):

        pass

class TestSched(unittest.TestCase):

    def test_init(self):

        pass

class TestSheet(unittest.TestCase):

    def test_init(self):

        pass

class TestDirMaster(unittest.TestCase):

    def test_init(self):

        db = dirmaster()

        db.homedir
        db.filedir

    def test_set_homedir(self):

        db = dirmaster()

        db.set_homedir(__file__)

        db.homedir

    def test_set_filedir(self):

        db = dirmaster()

        db.set_filedir(__file__)

        db.filedir

    def test_get_abspath(self):

        dirmaster().get_abspath(__file__)

    def test_get_dirpath(self):

        dirmaster().get_dirpath(__file__)

    def test_get_fnames(self):

        db = dirmaster()

        db.get_fnames(__file__,returnAbsFlag=True)

class TestLoad(unittest.TestCase):

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

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
