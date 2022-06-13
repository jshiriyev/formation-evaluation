from datetime import datetime

import logging

import os

import unittest

import numpy as np

if __name__ == "__main__":
    import setup

from textio import DirBase
from textio import Column
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

class TestColumn(unittest.TestCase):

    def test_init(self):

        column = Column(np.linspace(1,1000,100000),unit="m")

        column+1
        column-1
        column*2
        column/2

        column+column
        column-column
        column*column
        column/column

    def test_get_maxchar(self):

        column = Column(np.linspace(1,1000,100000),unit="m")

        self.assertEqual(column.get_maxchar_(),18,
            "get_maxchar_() does not return correct number of max chars for floats!")

        column = Column(np.arange(50),unit='cm')

        self.assertEqual(column.get_maxchar_(),2,
            "get_maxchar_() does not return correct number of max chars for ints!")

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

        a = np.array([1,2,3.])
        b = np.array([4,5,6.])

        df.set_running(a,b,cols=(0,1),init=False)

        self.assertCountEqual(df._headers,["col0","col1"],"Initialization of DataFrame Running is failed!")

        df.set_running(b,a,cols=(0,1))

        np.testing.assert_array_equal(df.columns("col0")[:3],a)
        np.testing.assert_array_equal(df.columns("col0")[3:],b)

        np.testing.assert_array_equal(df.columns("col1")[:3],b)
        np.testing.assert_array_equal(df.columns("col1")[3:],a)

    def test_columns(self):

        df = DataFrame("col0","col1")

        a = np.random.randint(0,100,10)
        b = np.random.randint(0,100,10)

        df.set_running(a,b,cols=(0,1),headers=["a","b"])

        self.assertCountEqual(df.headers,["a","b"],"Initialization of DataFrame Running is failed!")

        np.testing.assert_array_equal(df.columns("b"),df.columns(1))

    def test_add_attrs(self):

        df = DataFrame("col0","col1")

        df.add_attrs(name="raw_data")
        
        name1 = df.name

        df.add_attrs(name="raw_data_2")

        name2 = df.name

        self.assertEqual(name1,name2)
        self.assertEqual(name1,"raw_data")
        self.assertEqual(name2,"raw_data")

    def test_add_childattrs(self):

        df = DataFrame("A","B")

        df.add_childattrs("child",name1="john",name2="smith")

        df.add_childattrs("child",name1="tomy")

        self.assertEqual(df.child.name1,"john")

    def test_str2cols(self):

        full_names = np.array(["elthon\tsmith","bill\tgates\tshir"])

        df = DataFrame(full_names)

        df.set_headers("first name\tlast name",cols=(0,))

        df.str2cols(0,deliminator="\t")

        self.assertCountEqual(df._headers,["first name","last name"],
            "Splitting headers while splitting column has failed!")

    def test_cols2str(self):

        names = np.array(["elthon","john"])
        nicks = np.array(["smith","verdin"])

        df = DataFrame(names,nicks)
        
        df.cols2str([0,1])

    def test_astype(self):

        a = np.array([1,2,3,4,5])
        b = np.array([1.,3.4,np.nan,4.7,8])
        c = np.array([datetime.today(),datetime(2022,2,2),datetime(2022,1,2),datetime(2021,12,2),None])
        d = np.array(["1.","","5.7","6","None"])
        e = c.astype(np.datetime64)

        df = DataFrame(a,b,c,d,e)

        for dtype in (int,str,float,object):
            df.astype(0,dtype)

        for dtype in (int,str,float,object):
            df.astype(1,dtype)

        for dtype in (str,datetime,np.datetime64):
            df.astype(2,dtype)

        for dtype in (str,int,float):
            df.astype(3,dtype)

        for dtype in (str,datetime,np.datetime64):
            df.astype(4,np.datetime64)

    def test_edit_nones(self):

        A = np.array([1,2,3,4,None,6])
        B = np.array([0,1,2,None,3,4])

        df = DataFrame(A,B)

        df.edit_nones(0,none=50)
        df.edit_nones(1)

    def test_edit_dates(self):

        c = np.array([datetime.today(),datetime(2022,2,2),datetime(2022,1,2),datetime(2021,12,2),None])

        df = DataFrame(c)

        df.astype(0,np.datetime64)

        df.edit_dates(0,shiftyears=-2,shiftmonths=-3,shiftdays=10)

    def test_edit_strings(self):

        names = np.array(["elthon","john","1"])

        df = DataFrame(names)

        df.edit_strings(0,zfill=3)

    def test_unique(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = np.array(["A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df.set_running(A,B,init=True)

        df.unique(cols=(0,1),inplace=True)

        np.testing.assert_array_equal(df.running[0],
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df.running[1],
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

    def test_print(self):

        df = DataFrame("col0","col1")

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df.set_running(a,b,cols=(0,1),headers=["a","b"])

    def test_write(self):

        pass

    def test_writeb(self):

        df = DataFrame("col0","col1")

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df.set_running(a,b,cols=(0,1),headers=["a","b"])

class TestRegText(unittest.TestCase):

    def test_init(self):

        rt = RegText()

        rt.set_headers("WELL","DATE","OIL","WATER","GAS")
        
        well = np.array([
            "A01","A01","A01","A01","A01","A01","A01","A01",
            "A01","A01","A01","A01","B02","B02","B02","B02",
            "B02","B02","B02","B02","B02","B02","B02","B02"])

        date    = np.array([1,2,3,4,5,6,7,8,9,10,11,12,1,2,3,4,5,6,7,8,9,10,11,12])
        oil     = np.array([12,11,10,9,8,7,6,5,4,3,2,1,8,8,8,8,8,8,8,8,8,8,8,8])
        water   = np.array([24,23,22,21,20,19,18,17,16,16,14,13,15,15,15,15,15,15,15,15,15,15,15,15])
        gas     = np.array([36,35,34,33,32,31,30,29,28,27,26,25,25,25,25,25,25,25,25,25,25,25,25,25])

        rt.set_running(well,date,oil,water,gas,cols=(0,1,2,3,4))

        rt.print_rlim = 30

        text = rt.__str__()

class TestLogASCII(unittest.TestCase):

    def test_init(self):

        pass

class TestExcel(unittest.TestCase):

    def test_init(self):

        pass

class TestIrrText(unittest.TestCase):

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
