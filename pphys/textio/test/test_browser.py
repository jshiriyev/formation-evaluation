import datetime
import io
import logging
import os
import unittest

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from textio import dirmaster as Browser

class TestDirMaster(unittest.TestCase):

    def test_init(self):

        db = Browser()

        db.homedir
        db.filedir

    def test_set_homedir(self):

        db = Browser()

        db.set_homedir(__file__)

        db.homedir

    def test_set_filedir(self):

        db = Browser()

        db.set_filedir(__file__)

        db.filedir

    def test_get_abspath(self):

        Browser().get_abspath(__file__)

    def test_get_dirpath(self):

        Browser().get_dirpath(__file__)

    def test_get_fnames(self):

        db = Browser()

        db.get_fnames(__file__,returnAbsFlag=True)

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
