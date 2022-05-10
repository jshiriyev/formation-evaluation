import os

import unittest

import numpy as np

if __name__ == "__main__":
    import setup

from dataset import DirBase
from dataset import DataFrame
from dataset import Excel
from dataset import VTKit
from dataset import WSchedule
from dataset import LogASCII
from dataset import NpText

class TestDirBase(unittest.TestCase):

    def test_init(self):

        db = DirBase()

        db.homedir
        db.filedir

    def test_set_homedir(self):

        db = DirBase()

        db.set_homedir(__file__)

        db.homedir

    def test_set_filedir(self):

        db = DirBase()

        db.set_filedir(__file__)

        db.filedir

    def test_get_abspath(self):

        DirBase().get_abspath(__file__)

    def test_get_dirpath(self):

        DirBase().get_dirpath(__file__)

    def test_get_fnames(self):

        db = DirBase()

        db.get_fnames(__file__,returnAbsFlag=True)

class TestDataFrame(unittest.TestCase):

    def test_init_none(self):

        pass

    def test_init_filepath(self):

        df = DataFrame(filepath="datatest")

        df.read(skiplines=1)

    def test_init_headers(self):

        pass

    def test_init_filepath_headers(self):

        pass

    def test_unique(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = np.array(["A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df.set_running(A,B,initHeadersFlag=True)

        df.unique(header_indices=[0,1],inplace=True)

        np.testing.assert_array_equal(df.running[0],
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df.running[1],
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

class TestExcel(unittest.TestCase):

    def test_init(self):

        pass

class TestVTKit(unittest.TestCase):

    def test_init(self):

        pass

class TestWellSched(unittest.TestCase):

    def test_init(self):

        pass

class TestLogASCII(unittest.TestCase):

    def test_init(self):

        pass

class TestNpText(unittest.TestCase):

    def test_init(self):

        pass
                       
if __name__ == "__main__":

    unittest.main()
