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

class TestColumn(unittest.TestCase):

    def test_init(self):

        column = Column()
        np.testing.assert_array_equal(column.vals,np.array([],dtype=float))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,"dimensionless")
        self.assertEqual(column.info," ")

        column = Column(size=5)
        np.testing.assert_array_equal(column.vals,np.zeros(5))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,"dimensionless")
        self.assertEqual(column.info," ")

        column = Column(size=5,dtype=int)
        np.testing.assert_array_equal(column.vals,np.arange(5))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(size=5,dtype=float)
        np.testing.assert_array_equal(column.vals,np.zeros(5))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,"dimensionless")
        self.assertEqual(column.info," ")

        column = Column(size=5,dtype=str)
        np.testing.assert_array_equal(column.vals,np.empty(5,dtype="U30"))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(size=5,dtype=np.datetime64,head="5 months starting from January 1, 2000")
        self.assertEqual(column.head,"5 months starting from January 1, 2000")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(5)
        np.testing.assert_array_equal(column.vals,np.array([5]))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(5.)
        np.testing.assert_array_equal(column.vals,np.array([5.]))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,"dimensionless")
        self.assertEqual(column.info," ")

        column = Column("textio.py")
        np.testing.assert_array_equal(column.vals,np.array(["textio.py"]))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(datetime.today())
        np.testing.assert_array_equal(column.vals,np.array([datetime.today()],dtype=np.datetime64))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column(np.arange(5),head="Integers")
        np.testing.assert_array_equal(column.vals,np.arange(5))
        self.assertEqual(column.head,"Integers")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column([1,2,3],head="Integers to Float",unit="cm")
        np.testing.assert_array_equal(column.vals,np.array([1.,2,3]))
        self.assertEqual(column.head,"Integers to Float")
        self.assertEqual(column.unit,"cm")
        self.assertEqual(column.info," ")

        column = Column(np.linspace(1,1000,100000),head="Random Floating Numbers",unit="m")
        np.testing.assert_array_equal(column.vals,np.linspace(1,1000,100000))
        self.assertEqual(column.head,"Random Floating Numbers")
        self.assertEqual(column.unit,"m")
        self.assertEqual(column.info," ")

        column = Column(["1","5","7"],head="Strings to Float",unit="km")
        np.testing.assert_array_equal(column.vals,np.array([1,5,7.]))
        self.assertEqual(column.head,"Strings to Float")
        self.assertEqual(column.unit,"km")
        self.assertEqual(column.info," ")

        column = Column(["1","5","7"],head="Strings")
        np.testing.assert_array_equal(column.vals,np.array(["1","5","7"]))
        self.assertEqual(column.head,"Strings")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")

        column = Column([datetime.today(),datetime.today()])
        np.testing.assert_array_equal(column.vals,np.array([datetime.today(),datetime.today()],dtype=np.datetime64))
        self.assertEqual(column.head," ")
        self.assertEqual(column.unit,None)
        self.assertEqual(column.info," ")
        
    def test_set_head(self):
        
        column = Column([datetime.today(),datetime.today()])
        self.assertEqual(column.head," ")

        column.set_head('Two Dates')
        self.assertEqual(column.head,"Two Dates")

        column.set_head()
        self.assertEqual(column.head,"Two Dates")

        column.set_head('Edited')
        self.assertEqual(column.head,"Edited")

    def test_set_unit(self):
        
        column = Column([datetime.today().date(),datetime.today().date()])
        self.assertEqual(column.unit,None)

        column.set_unit()
        self.assertEqual(column.unit,None)

        column.set_unit("seconds")
        np.testing.assert_array_equal(column.vals,np.array([datetime.today().date()]*2,dtype=np.datetime64).astype(float))
        self.assertEqual(column.unit,"seconds")

        column = Column(["1.","2"],unit="m")
        self.assertEqual(column.unit,"m")

        column.set_unit()
        self.assertEqual(column.unit,"m")

        column.set_unit("km")
        self.assertEqual(column.unit,"km")

    def test_set_info(self):
        
        column = Column([datetime.today(),datetime.today()])
        self.assertEqual(column.info," ")

        column.set_info('INFO: Two Dates')
        self.assertEqual(column.info,"INFO: Two Dates")

        column.set_info()
        self.assertEqual(column.info,"INFO: Two Dates")

        column.set_info('INFO: Edited')
        self.assertEqual(column.info,"INFO: Edited")

    def test_astype(self):
        pass

    # def test_get_valstr(self):
    #     pass

    # def test_get_maxchar(self):

    #     column = Column(np.linspace(1,1000,100000),unit="m")

    #     self.assertEqual(column.get_maxchar_(),18,
    #         "get_maxchar_() does not return correct number of max chars for floats!")

    #     column = Column(np.arange(50),unit='cm')

    #     self.assertEqual(column.get_maxchar_(),2,
    #         "get_maxchar_() does not return correct number of max chars for ints!")

    # def test_is_dimensionless(self):
    #     pass

    # def test_addition(self):

    #     column = Column(np.linspace(1,1000,100000),unit="m")
        
    #     column+1
    #     column+column

    # def test_check_equality(self):
    #     pass

    # def test_floor_division(self):
    #     pass

    # def test_greater_equal(self):
    #     pass

    # def test_greater_than(self):
    #     pass

    # def test_less_equal(self):
    #     pass

    # def test_less_than(self):
    #     pass

    # def test_remainder(self):
    #     pass

    # def test_multiplication(self):

    #     column = Column(np.linspace(1,1000,100000),unit="m")
        
    #     column*2

    #     column*column

    # def test_not_equal(self):
    #     pass

    # def test_to_the_power(self):
    #     pass

    # def test_repr(self):
    #     pass

    # def test_str(self):
    #     pass

    # def test_subtraction(self):

    #     column = Column(np.linspace(1,1000,100000),unit="m")
        
    #     column-1
    #     column-column

    # def test_true_division(self):

    #     column = Column(np.linspace(1,1000,100000),unit="m")
        
    #     column/2
    #     column/column

    # def test_unit_conversion(self):
    #     pass

    # def test_stringify(self):
    #     pass

    # def test_shift(self):
    #     pass

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

        with self.assertLogs() as captured:
            df.add_attrs(name="raw_data_2")

        self.assertEqual(captured.records[0].getMessage(),
            "Added value after replacing name with name_1.")

        self.assertEqual(df.name,"raw_data")
        self.assertEqual(df.name_1,"raw_data_2")

    def test_add_glossary(self):

        df = DataFrame("A","B")

        df.add_glossary("child",first_name=str,last_name=str)

        df.child.add_line(first_name="john",last_name="smith")

        with self.assertLogs() as captured:
            df.add_glossary("child","first_name")

        self.assertEqual(captured.records[0].getMessage(),
            "child already exists.")

        self.assertEqual(df.child[0,"first_name"],"john")
        self.assertEqual(df.child["john","first_name"],"john")
        self.assertEqual(df.child["john","last_name"],"smith")

        df.add_glossary("glos",Mnemonic=str,Unit=str,Value=float,Description=str)

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

class TestGlossary(unittest.TestCase):

    def test_init(self):

        pass

class TestLoadtxt(unittest.TestCase):

    def test_init(self):

        pass

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

class TestFunctions(unittest.TestCase):

    def test_remove_thousand_separator(self):

        a1 = str2float("10 000,00")
        a2 = str2float("10.000,00")
        a3 = str2float("10,000.00")

        self.assertEqual(a1,10000.,"could not remove thousand separator...")
        self.assertEqual(a2,10000.,"could not remove thousand separator...")
        self.assertEqual(a3,10000.,"could not remove thousand separator...")
                       
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    unittest.main()
