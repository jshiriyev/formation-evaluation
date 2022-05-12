import logging

import os

import unittest

import numpy as np

if __name__ == "__main__":
    import setup

from dataset import DirBase
from dataset import DataFrame
from dataset import RegText
from dataset import LogASCII
from dataset import Excel
from dataset import IrrText
from dataset import WSchedule
from dataset import VTKit

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

        df = DataFrame()

    def test_init_headers(self):

        df = DataFrame("col1","col2",filedir=__file__)

    def test_set_running(self):

        df = DataFrame("col0","col1")

        print(df.running)
        print(df.headers)

        df.set_running(np.array([1,2,3]),np.array([4,5,6]),np.array([4,5,6]),init=False)

        print(df.running)
        print(df.headers)

    def test_unique(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = np.array(["A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df.set_running(A,B,init=True)

        df.unique(header_indices=[0,1],inplace=True)

        np.testing.assert_array_equal(df.running[0],
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df.running[1],
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

class TestRegText(unittest.TestCase):

    def test_init(self):

        rt = RegText(filedir=__file__)

class TestLogASCII(unittest.TestCase):

    def test_init(self):

        pass

class TestExcel(unittest.TestCase):

    def test_init(self):

        pass

class IrrText(unittest.TestCase):

    def test_init(self):

        pass

class TestWSchedule(unittest.TestCase):

    def test_init(self):

        pass

class TestVTKit(unittest.TestCase):

    def test_init(self):

        pass
                       
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
