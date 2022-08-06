import datetime

from dateutil import relativedelta

import logging

import os

import unittest

import numpy as np
import pint

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

from cypy.vectorpy import str2float

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

    def test_init(self):

        df = DataFrame()
        self.assertEqual(len(df.heads),0,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),0,"Initialization of DataFrame Headers has failed!")

        df = DataFrame(col1=[],col2=[],filedir=__file__)
        self.assertEqual(len(df.heads),2,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),2,"Initialization of DataFrame Headers has failed!")

        df = DataFrame()

        df["col1"] = []
        df["col2"] = []
        df["col3"] = []

        self.assertEqual(len(df.heads),3,"Initialization of DataFrame Headers has failed!")
        self.assertEqual(len(df.running),3,"Initialization of DataFrame Headers has failed!")

        a = np.array([1,2,3.])
        b = np.array([4,5,6.])

        df = DataFrame(col0=a,col1=b)

        self.assertCountEqual(df.heads,["col0","col1"],"Initialization of DataFrame Running has failed!")

        df["col0"] = b
        df["col1"] = a

        np.testing.assert_array_equal(df["col0"],b)
        np.testing.assert_array_equal(df["col1"],a)

    def test_col_astype(self):

        a = np.array([1,2,3,4,5])
        b = np.array([1.,3.4,np.nan,4.7,8])
        c = np.array([datetime.datetime.today(),datetime.datetime(2022,2,2),datetime.datetime(2022,1,2),datetime.datetime(2021,12,2),None])
        d = np.array(["1.","","5.7","6",""])
        e = c.astype("datetime64")

        df = DataFrame(a=a,b=b,c=c,d=d,e=e)

        for dtype in ("int","str","float"):
            df['a'] = df['a'].astype(dtype)

        bb = [
            np.array([1,3,-99999,4,8]),
            np.array(["1","3","","4","8"]),
            np.array([1.,3.,np.nan,4.,8.]),
            ]

        for index,dtype in enumerate(("int","str","float")):
            df['b'] = df['b'].astype(dtype)
            np.testing.assert_array_equal(df['b'].vals,bb[index])

        for dtype in ("str","datetime64[D]"):
            df['c'] = df['c'].astype(dtype)

        for dtype in ("str","int","float"):

            if dtype=="int":
                df['d'] = df['d'].fromstring(dtype="int",regex=r"[-+]?\d+\b")
                df['d'] = df['d'].astype(dtype)
            else:
                df['d'] = df['d'].astype(dtype)

        for dtype in ("str","datetime64[D]"):
            df['e'] = df['e'].astype(dtype)

    def test_representation_methods(self):

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df = DataFrame(a=a,b=b)

    def test_add_attrs(self):

        df = DataFrame(col0=[],col1=[])

        df.name = "main_data"

        with self.assertRaises(KeyError):
            df.name = "other_data"
            
        # self.assertEqual(captured.records[0].getMessage(),
        #     "object already has 'name' attribute.")

        self.assertEqual(df.name,"main_data")

    def test_setglossary(self):

        df = DataFrame(A=[],B=[])

        df.setglossary("child",first_name=str,last_name=str)

        df.child.add_line(first_name="john",last_name="smith")

        with self.assertRaises(KeyError):
            df.setglossary("child","first_name")

        self.assertEqual(df.child[0,"first_name"],"john")
        self.assertEqual(df.child["john","first_name"],"john")
        self.assertEqual(df.child["john","last_name"],"smith")

        df.setglossary("glos",Mnemonic=str,Unit=str,Value=float,Description=str)

        start = {
            "unit" : "M",
            "value" : 2576,
            "description" : "it shows the depth logging started",
            "mnemonic" : "START",
            }
        
        stop = {
            "mnemonic" : "STOP",
            "unit" : "M",
            "value" : 2896,
            "description" : "it shows the depth logging stopped",
            }
        
        null = {
            "mnemonic" : "NULL",
            "value" : -999.25,
            "description" : "null values",
            }

        fld = {
            "mnemonic" : "FLD",
            "value" : "FIELD",
            "description" : "GUNESLI",
            }

        df.glos.add_line(**start)
        df.glos.add_line(**stop)
        df.glos.add_line(**null)
        df.glos.add_line(**fld)

        df.glos

        self.assertListEqual(df.glos[:,"value"],[2576.,2896.,-999.25,'FIELD'])
        self.assertListEqual(df.glos[1:,"value"],[2896.,-999.25,'FIELD'])

    def test_container_methods(self):

        df = DataFrame()

        a = np.random.randint(0,100,10)
        b = np.random.randint(0,100,10)

        df['a'] = a
        df['b'] = b

    def test_str2col(self):

        head = "first name\tlast name"

        full_names = np.array(["elthon\tsmith","bill\tgates\tjohn"])

        df = DataFrame(head=full_names)
        # print('\n')
        # print(df)

        df.str2col("head",delimiter="\t")

        self.assertEqual(df.heads,["head_0","head_1","head_2"],
            "Splitting headers while splitting col_ has failed!")
        np.testing.assert_array_equal(df["head_0"],np.array(["elthon","bill"]))
        np.testing.assert_array_equal(df["head_1"],np.array(["smith","gates"]))
        np.testing.assert_array_equal(df["head_2"],np.array(["","john"]))

        # print(df)

    def test_col2str(self):

        names = np.array(["elthon","john","tommy"])
        nicks = np.array(["smith","verdin","brian"])

        df = DataFrame(names=names,nicks=nicks)
        
        col_ = df.col2str(["names","nicks"])

        np.testing.assert_array_equal(col_.vals,
            np.array(["elthon smith","john verdin","tommy brian"]))

    def test_tostruct(self):

        names = np.array(["elthon","john","tommy"])
        lasts = np.array(["smith","verdin","brian"])
        ages = np.array([23,45,38])

        df = DataFrame(names=names,lasts=lasts,ages=ages)

        arr_ = df.tostruct()

        np.testing.assert_array_equal(arr_[0].tolist(),('elthon', 'smith', 23))

    def test_sort(self):

        A = np.array([ 6 , 6 , 2 , 2 , 3 , 5 , 3 , 4 , 3 , 1 , 2 , 1 ])
        B = np.array(["A","B","C","D","D","C","C","C","C","E","F","F"])

        df = DataFrame(A=A,B=B)

        df = df.sort(('A',))

        np.testing.assert_array_equal(df["A"].vals,
            np.array([1,1,2,2,2,3,3,3,4,5,6,6]))

        np.testing.assert_array_equal(df["B"].vals,
            np.array(["E","F","C","D","F","D","C","C","C","C","A","B"]))

        df = DataFrame(A=A,B=B)

        df = df.sort(('A','B'))

        np.testing.assert_array_equal(df["A"].vals,
            np.array([1,1,2,2,2,3,3,3,4,5,6,6]))

        np.testing.assert_array_equal(df["B"].vals,
            np.array(["E","F","C","D","F","C","C","D","C","C","A","B"]))

        df = DataFrame(A=A,B=B)

        df = df.sort(('A','B'),reverse=True)

        np.testing.assert_array_equal(df["A"].vals,
            np.array([6,6,5,4,3,3,3,2,2,2,1,1]))

        np.testing.assert_array_equal(df["B"].vals,
            np.array(["B","A","C","C","D","C","C","F","D","C","F","E"]))

    def test_filter(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = np.array([
            "A","12text5","text345","125text","C","C","C","C","C","D","E","F","F","F"])

        df["A"] = A
        df["B"] = B

        df = df.filter("B",["E","F"])

        np.testing.assert_array_equal(df["A"].vals,
            np.array([6,6,6,6]))

        np.testing.assert_array_equal(df["B"].vals,
            np.array(["E","F","F","F"]))

        df = DataFrame()

        df["A"] = A
        df["B"] = B

        df = df.filter("B",regex=r".*\d")

        np.testing.assert_array_equal(df["A"].vals,
            np.array([1,1,2]))

        np.testing.assert_array_equal(df["B"].vals,
            np.array(["12text5","text345","125text"]))

    def test_unique(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])

        B = np.array([
            "A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df["A"] = A
        df["B"] = B

        df = df.unique(("A","B"))

        np.testing.assert_array_equal(df["A"].vals,
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df["B"].vals,
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

        df = df.unique(("A",))

        np.testing.assert_array_equal(df["A"].vals,
            np.array([1,2,3,4,5,6]),err_msg="DataFrame.unique() has an issue!")

    def test_write(self):

        pass

    def test_writeb(self):

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df = DataFrame(a=a,b=b)

class TestGlossary(unittest.TestCase):

    def test_init(self):

        pass

class TestLoadtxt(unittest.TestCase):

    def test_init(self):

        pass

class TestRegText(unittest.TestCase):

    def test_init(self):

        rt = RegText()
        
        well = np.array([
            "A01","A01","A01","A01","A01","A01","A01","A01",
            "A01","A01","A01","A01","B02","B02","B02","B02",
            "B02","B02","B02","B02","B02","B02","B02","B02"])

        date    = np.array([1,2,3,4,5,6,7,8,9,10,11,12,1,2,3,4,5,6,7,8,9,10,11,12])
        oil     = np.array([12,11,10,9,8,7,6,5,4,3,2,1,8,8,8,8,8,8,8,8,8,8,8,8])
        water   = np.array([24,23,22,21,20,19,18,17,16,16,14,13,15,15,15,15,15,15,15,15,15,15,15,14])
        gas     = np.array([36,35,34,33,32,31,30,29,28,27,26,25,25,25,25,25,25,25,25,25,25,25,25,25])

        rt["WELL"] = well
        rt["DATE"] = date
        rt["OIL"] = oil
        rt["WATER"] = water
        rt["GAS"] = gas

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

class TestFunctions(unittest.TestCase):

    def test_remove_thousand_separator(self):

        a1 = str2float("10 000,00",sep_decimal=",",sep_thousand=" ")
        a2 = str2float("10.000,00",sep_decimal=",",sep_thousand=".")
        a3 = str2float("10,000.00")

        self.assertEqual(a1,10000.,"could not remove thousand separator...")
        self.assertEqual(a2,10000.,"could not remove thousand separator...")
        self.assertEqual(a3,10000.,"could not remove thousand separator...")
                       
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
