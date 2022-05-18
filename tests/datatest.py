import logging

import os

import unittest

import numpy as np

if __name__ == "__main__":
    import setup

from textio import DirBase
from textio import DataFrame
from textio import RegText
from textio import LogASCII
from textio import Excel
from textio import IrrText
from textio import WSchedule
from textio import VTKit

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

    def test_set_headers(self):

        df = DataFrame()

        df.set_headers("col1","col2","col3")

        self.assertEqual(len(df.headers),3,"Initialization of DataFrame Headers is failed!")
        self.assertEqual(len(df.running),3,"Initialization of DataFrame Headers is failed!")

    def test_set_running(self):

        df = DataFrame("col0","col1")

        a = np.array([1,2,3])
        b = np.array([4,5,6])

        df.set_running(a,b,cols=(0,1),init=False)

        self.assertCountEqual(df._headers,["col0","col1"],"Initialization of DataFrame Running is failed!")

    def test_columns(self):

        df = DataFrame("col0","col1")

        a = np.random.randint(0,100,10)
        b = np.random.randint(0,100,10)

        df.set_running(a,b,cols=(0,1),headers=["a","b"])

        self.assertCountEqual(df.headers,["a","b"],"Initialization of DataFrame Running is failed!")

        np.testing.assert_array_equal(df.columns("b"),df.columns(1))

    def test_str2col(self):

        full_names = np.array(["elthon\tsmith","bill\tgates\tshir"])

        df = DataFrame(full_names)

        df.str2col(0,deliminator="\t")

    def test_col2str(self):

        names = np.array(["elthon","john"])
        nicks = np.array(["smith","verdin"])

        df = DataFrame(names,nicks)
        
        df.col2str([0,1])

    def test_edit_nones(self):

        A = np.array([1,2,3,4,None,6])
        B = np.array([0,1,2,None,3,4])

        df = DataFrame(A,B)

        df.edit_nones([0],replace=50)
        df.edit_nones()

    def test_edit_strings(self):

        names = np.array(["elthon","john","1"])

        df = DataFrame(names)

        df.edit_strings(0,zfill=3)

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

    def test_print(self):

        df = DataFrame("col0","col1")

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df.set_running(a,b,cols=(0,1),headers=["a","b"])

        df.print()

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
