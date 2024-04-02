import datetime
import io
import logging
import os
import unittest

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from textio import header

class TestHeader(unittest.TestCase):

    def test_init(self):

        names = header(first=['John','Jessica'],last=['Hass','Yummy'])

        self.assertListEqual(names.params,['first','last'])
        self.assertListEqual(names.first,['John','Jessica'])
        self.assertListEqual(names.last,['Hass','Yummy'])

        self.assertEqual(names['john'].first,'John')
        self.assertEqual(names['john'].last,'Hass')

        self.assertEqual(names['jessica'].first,'Jessica')
        self.assertEqual(names['jessica'].last,'Yummy')

    def test_all(self):

        front = header(first_name="john",last_name="smith")

        self.assertEqual(front.first_name,"john")
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

        self.assertListEqual(gloss.value,[2576.0,2896.0,-999.25,"FIELD"])
        self.assertListEqual(gloss.value[1:],[2896.0,-999.25,'FIELD'])

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
