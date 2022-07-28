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
from textio import nones
from textio import array
from textio import column
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

class TestNones(unittest.TestCase):

    def test_nones(self):

        nones = nones()
        nones.datetime64 = np.datetime64('NaT')
        self.assertEqual(nones.int,-99_999)

        nones.int = 0.
        self.assertEqual(nones.int,0)

        with self.assertRaises(AttributeError):
            nones.dtypes

    def test_todict(self):

        nones = nones()

        nones.int = 0

        nones_dict = nones.todict()

        nones_dict['none_float'] = -99999.999

        self.assertEqual(nones_dict["none_int"],0)
        self.assertEqual(nones_dict["none_float"],-99999.999)
        self.assertEqual(nones_dict["none_str"],"")
        self.assertEqual(np.isnan(nones_dict["none_datetime64"]),True)

        nones_dict = nones.todict("int","str")

        self.assertEqual(len(nones_dict),2)

class TestColumn(unittest.TestCase):

    def test_init(self):

        col_ = column(head="A")
        np.testing.assert_array_equal(col_.vals,np.array([],dtype="float"))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column(head="A",size=5)
        np.testing.assert_array_equal(col_.vals,np.linspace(0,5,5))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column(head="A",size=5,dtype="int")
        np.testing.assert_array_equal(col_.vals,np.arange(5))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(head="A",size=5,dtype="float")
        np.testing.assert_array_equal(col_.vals,np.linspace(0,5,5))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column(head="A",size=5,dtype="str")
        np.testing.assert_array_equal(col_.vals,np.empty(5,dtype="U30"))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(head="5 months",size=5,dtype="datetime64[D]",info="5 months starting from January 1, 2000")
        self.assertEqual(col_.head,"5months")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info,"5 months starting from January 1, 2000")

        col_ = column(head="number",vals=5)
        np.testing.assert_array_equal(col_.vals,np.array([5]))
        self.assertEqual(col_.head,"number")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(head="number",vals=5.)
        np.testing.assert_array_equal(col_.vals,np.array([5.]))
        self.assertEqual(col_.head,"number")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column(head="names",vals="textio.py")
        np.testing.assert_array_equal(col_.vals,np.array(["textio.py"]))
        self.assertEqual(col_.head,"names")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        dt = datetime.datetime.today()
        col_ = column(head="time,",vals=dt)
        np.testing.assert_array_equal(col_.vals,np.array([dt],dtype="datetime64[s]"))
        self.assertEqual(col_.head,"time")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(head="Integers",vals=np.arange(5))
        np.testing.assert_array_equal(col_.vals,np.arange(5))
        self.assertEqual(col_.head,"Integers")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(head="Integers To Float",vals=[1,2,3],unit="cm")
        np.testing.assert_array_equal(col_.vals,np.array([1.,2,3]))
        self.assertEqual(col_.head,"IntegersToFloat")
        self.assertEqual(col_.unit,"cm")
        self.assertEqual(col_.info," ")

        col_ = column(head="Random Floating Numbers",vals=np.linspace(1,1000,100000),unit="m")
        np.testing.assert_array_equal(col_.vals,np.linspace(1,1000,100000))
        self.assertEqual(col_.head,"RandomFloatingNumbers")
        self.assertEqual(col_.unit,"m")
        self.assertEqual(col_.info," ")

        col_ = column(head="Strings To Float",vals=["1","5","7"],unit="km")
        np.testing.assert_array_equal(col_.vals,np.array([1,5,7.]))
        self.assertEqual(col_.head,"StringsToFloat")
        self.assertEqual(col_.unit,"km")
        self.assertEqual(col_.info," ")

        col_ = column(head="Strings",vals=["1","5","7"])
        np.testing.assert_array_equal(col_.vals,np.array(["1","5","7"]))
        self.assertEqual(col_.head,"Strings")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        dt_list = [datetime.datetime.today()]*2
        col_ = column(head="time",vals=dt_list)
        np.testing.assert_array_equal(col_.vals,np.array(dt_list,dtype="datetime64[s]"))
        self.assertEqual(col_.head,"time")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")
        
    def test_set_head(self):
        
        col_ = column(head="time%",vals=[datetime.datetime.today()]*2)
        self.assertEqual(col_.head,"time")

        col_.head = 'Two_Dates'
        self.assertEqual(col_.head,"Two_Dates")

        col_.head = None
        self.assertEqual(col_.head,"Two_Dates")

        col_.head = 'Edited'
        self.assertEqual(col_.head,"Edited")

    def test_set_unit(self):
        
        col_ = column(head="time",vals=[datetime.datetime.today().date()]*2)
        self.assertEqual(col_.unit,None)

        col_.unit = None
        self.assertEqual(col_.unit,None)

        col_.unit = "seconds"
        vals_true = np.array([datetime.datetime.today().date()]*2,dtype="datetime64[s]")
        np.testing.assert_array_equal(col_.vals,vals_true)
        self.assertEqual(col_.unit,None)

        col_ = column(["1.","2"],unit="m")
        np.testing.assert_array_equal(col_.vals,np.array([1.,2.]))
        self.assertEqual(col_.unit,"m")

        col_.unit = None
        self.assertEqual(col_.unit,"m")

        col_.unit = "km"
        self.assertEqual(col_.unit,"km")

    def test_set_info(self):
        
        col_ = column([datetime.datetime.today()]*2)
        self.assertEqual(col_.info," ")

        col_.info = 'INFO: Two Dates'
        self.assertEqual(col_.info,"INFO: Two Dates")

        col_.info = None
        self.assertEqual(col_.info,"INFO: Two Dates")

        col_.info = 'INFO: Edited'
        self.assertEqual(col_.info,"INFO: Edited")

    def test_astype(self):
        
        col_ = column(["1.","2"],unit="m")
        col_.astype("int")
        self.assertEqual(col_.unit,None)

        col_.astype("float")
        self.assertEqual(col_.unit,"dimensionless")

    def test_tostring(self):

        col_ = column(np.arange(1,5))
        col_ = col_.tostring(fstring="{:d}")
        np.testing.assert_array_equal(col_.vals,np.array(["1","2","3","4"]))
        self.assertEqual(col_.head,"HEAD")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")
        
        col_ = column(np.linspace(1,5,4),unit="km")
        col_ = col_.tostring(fstring="{:.1f}")
        np.testing.assert_array_equal(col_.vals,np.array(["1.0","2.3","3.7","5.0"]))
        self.assertEqual(col_.head,"HEAD")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(np.array(["78,.45,2","98,3.,28","1,75,3,."]))
        col_ = col_.tostring(fstring="{:15s}")
        np.testing.assert_array_equal(col_.vals,np.array(['78,.45,2       ',
            '98,3.,28       ','1,75,3,.       ']))
        self.assertEqual(col_.head,"HEAD")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(vals=np.array(["elthon","john","1"]),head="string")
        col_ = col_.tostring(zfill=3)
        np.testing.assert_array_equal(col_.vals,np.array(['elthon',
            'john','001']))

        col_ = column(dtype="datetime64[D]",size=2,step_unit="M",head="Dates",info="Two months")
        col_ = col_.tostring(fstring="Date is {%Y-%m-%d}")
        true_vals = (
            datetime.datetime.today()-relativedelta.relativedelta(months=2),
            datetime.datetime.today()-relativedelta.relativedelta(months=1),
            )
        true_vals = ["Date is {}".format(dt.strftime("%Y-%m-%d")) for dt in true_vals]
        np.testing.assert_array_equal(col_.vals,np.array(true_vals))
        self.assertEqual(col_.head,"Dates")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info,"Two months")

    def test_representation_operations(self):
        
        col_ = column(head="integers",vals=-np.arange(1,10000))
        self.assertEqual(col_._valstr_(),'[-1,-2,-3,...,-9997,-9998,-9999]')

        col_ = column(head="float",vals=np.linspace(1,1000,100000),unit="m")
        self.assertEqual(col_._valstr_(),'[1.,1.0099901,1.0199802,...,999.9800198,999.9900099,1000.]')

        col_ = column(head="modules",vals=["1 textio.py","2 graphics.py","3 geometries.py","4 items.py"])
        self.assertEqual(col_._valstr_(),"['1 textio.py','2 graphics.py','3 geometries.py','4 items.py']")

        vals = [datetime.datetime.today()-relativedelta.relativedelta(days=i) for i in reversed(range(1,11))]
        col_ = column(vals=vals,head="datetime")
        vals_ = np.array(vals,dtype="datetime64[s]")
        self.assertEqual(col_._valstr_(2),"['{}',...,'{}']".format(vals_[0],vals_[-1]))

    def test_nondim(self):
        
        col_ = column(["1.","2"],unit="m")
        self.assertEqual(col_.nondim(),False)

        col_.astype("int")
        self.assertEqual(col_.nondim(),True)

    def test_comparison_operations(self):

        col_1 = column(vals=np.array([1,2,3]),head="length",unit="km")
        col_2 = col_1.convert("m")

        cond = col_1==col_2
        
        np.testing.assert_array_equal(cond,np.array([True,True,True]))

    def test_searching(self):

        col_ = column(head="floats",vals=np.linspace(1,1000,100000),unit="m")

        self.assertEqual(col_.maxchar(),18,
            "maxchar() does not return correct number of chars in the largest str(float)!")

        self.assertEqual(col_.maxchar(string=True),"1.0299702997029971")

        col_ = column(head="integers",vals=np.arange(50))

        self.assertEqual(col_.maxchar(),2,
            "maxchar() does not return correct number of chars in the largest str(ints)!")

    def test_replace(self):

        A = column(vals=np.array([1,2,3,4,None,6]))
        B = column(vals=np.array([0,1,2,None,None,4]))

        A.replace(new=50)
        np.testing.assert_array_equal(A.vals,np.array([1,2,3,4,50,6]))
        B.replace()
        np.testing.assert_array_equal(B.vals,np.array([0,1,2,2,2,4]))

    def test_container_operations(self):

        vals = np.linspace(1,5,5)
        col_ = column(vals=vals,head="floats",unit="m",info="linspace data")
        np.testing.assert_array_equal(col_[:],vals)

        col_[-1] = 50
        np.testing.assert_array_equal(col_[:],np.array([1,2,3,4,50]))

        self.assertEqual(len(col_),5)

    def test_unit_conversion(self):

        col_1 = column(head="values",vals=["1.","2"],unit="m")
        col_2 = col_1.convert("km")
        self.assertEqual(col_1.unit,'m')
        self.assertEqual(col_2.unit,'km')
        np.testing.assert_array_equal(col_1.vals,np.array([1.,2.]))
        np.testing.assert_array_equal(col_2.vals,np.array([0.001,0.002]))

    def test_shift(self):

        col_ = column(head="integers",vals=np.array([1,2,3,4,5],dtype="int"))
        col_ = col_.shift(5)
        np.testing.assert_array_equal(col_.vals,np.array([6,7,8,9,10]))

        col_ = column(head="floats",vals=np.linspace(1,4,7),unit="km")
        col_ = col_.shift(5,"m")
        np.testing.assert_array_equal(col_.vals,np.array([
            1.005,1.505,2.005,2.505,3.005,3.505,4.005]))

        col_ = column(["textio","petrophysics","helloworld!"])
        col_ = col_.shift(5)
        np.testing.assert_array_equal(col_.vals,np.array([
            '     textio','     petrophysics','     helloworld!']))
        
        col_ = column(np.arange(np.datetime64('2019-02-27'),np.datetime64('2019-03-02'),np.timedelta64(1,'D')))
        col_ = col_.shift(1,'Y')
        np.testing.assert_array_equal(col_.vals,np.array([
            np.datetime64('2020-02-27'),np.datetime64('2020-02-29'),np.datetime64('2020-03-01')]))
        col_ = col_.shift(7,'Y')
        np.testing.assert_array_equal(col_.vals,np.array([
            np.datetime64('2027-02-27'),np.datetime64('2027-02-28'),np.datetime64('2027-03-01')]))
        col_ = col_.shift(100,'Y')
        np.testing.assert_array_equal(col_.vals,np.array([
            np.datetime64('2127-02-27'),np.datetime64('2127-02-28'),np.datetime64('2127-03-01')]))

        col__vals = np.array([
            datetime.datetime(2022,2,2),
            datetime.datetime(2022,1,2),
            datetime.datetime(2021,12,2),
            None])
        
        col_ = column(vals=col__vals)

        col_ = col_.shift(delta=-2,deltaunit='Y')
        col_ = col_.shift(delta=10,deltaunit='D')

        np.testing.assert_array_equal(col_.vals,
            np.array([
                np.datetime64('2020-02-12'),
                np.datetime64('2020-01-12'),
                np.datetime64('2019-12-12'),
                np.datetime64('NaT')]))

        col_ = column(vals=col__vals)

        col_ = col_.shift(delta=-2,deltaunit='M')

        np.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
            np.array([
                np.datetime64('2021-12-02'),
                np.datetime64('2021-11-02'),
                np.datetime64('2021-10-02'),
                np.datetime64('NaT')]))

        col_ = col_.shift(delta='EOM')

        np.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
            np.array([
                np.datetime64('2021-12-31'),
                np.datetime64('2021-11-30'),
                np.datetime64('2021-10-31'),
                np.datetime64('NaT')]))

        col_ = col_.shift(delta='BOM')

        np.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
            np.array([
                np.datetime64('2021-12-01'),
                np.datetime64('2021-11-01'),
                np.datetime64('2021-10-01'),
                np.datetime64('NaT')]))

    def test_numeric_operations(self):

        # Addition

        col_ = column(np.arange(1,7,2))
        colnew = col_+1
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(col_.vals,np.array([1,3,5]))
        np.testing.assert_array_equal(colnew.vals,np.array([2,4,6]))

        colnew = col_+1.
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(col_.vals,np.array([1,3,5]))
        np.testing.assert_array_equal(colnew.vals,np.array([2,4,6]))

        colnew = col_+"1"
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(col_.vals,np.array([1,3,5]))
        np.testing.assert_array_equal(colnew.vals,np.array([2,4,6]))

        col_ = column(np.linspace(1,10,4))
        colnew = col_+1
        np.testing.assert_array_equal(col_.vals,np.array([1.,4.,7.,10.]))
        np.testing.assert_array_equal(colnew.vals,np.array([2.,5.,8.,11.]))

        colnew = col_+"1"
        np.testing.assert_array_equal(col_.vals,np.array([1.,4.,7.,10.]))
        np.testing.assert_array_equal(colnew.vals,np.array([2.,5.,8.,11.]))

        col_ = column(np.linspace(1,10,4),unit="m")
        with self.assertRaises(pint.errors.DimensionalityError):
            colnew = col_+1
        self.assertEqual(col_.unit,"m")
        np.testing.assert_array_equal(col_.vals,np.array([1.,4.,7.,10.]))

        colnew = col_+col_
        self.assertEqual(col_.unit,"m")
        self.assertEqual(colnew.unit,"m")
        np.testing.assert_array_equal(col_.vals,np.array([1.,4.,7.,10.]))
        np.testing.assert_array_equal(colnew.vals,np.array([2.,8.,14.,20.]))

        col_ = column(['john','boris','jonas'])
        colnew = col_+1
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(col_.vals,np.array(['john','boris','jonas']))
        np.testing.assert_array_equal(colnew.vals,np.array(['john1','boris1','jonas1']))

        colnew = col_+" smith"
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(col_.vals,np.array(['john','boris','jonas']))
        np.testing.assert_array_equal(colnew.vals,np.array(['john smith','boris smith','jonas smith']))

        col_ = column([np.datetime64('today'),np.datetime64('today')])
        # print(col_.dtype)
        # Floor Division


        # Multiplication

        col_ = column(np.linspace(1,1000,100000),unit="m")
        
        col_*2

        col_*col_

        # Not Equal

        # To The Power:

        # Subtraction

        col_ = column(np.linspace(1,1000,100000),unit="m")
        
        col_-1
        col_-col_

        # True Division

        col_ = column(np.linspace(1,1000,100000),unit="m")
        
        col_/2
        col_/col_

    def test_property_methods(self):

        dates = np.arange(np.datetime64('2020-02-29'),np.datetime64('2020-03-04'),np.timedelta64(1,'D'))
        dates = np.append(dates,np.datetime64('NaT'))

        col_ = column(dates)
        
        np.testing.assert_array_equal(col_.year,
            np.array([2020,2020,2020,2020,-99999]))
        np.testing.assert_array_equal(col_.month,
            np.array([2,3,3,3,-99999]))
        np.testing.assert_array_equal(col_.day,
            np.array([29,1,2,3,-99999]))
        np.testing.assert_array_equal(col_.eom,
            np.array([29,31,31,31,-99999]))
        np.testing.assert_array_equal(col_.eonm,
            np.array([31,30,30,30,-99999]))
        np.testing.assert_array_equal(col_.eopm,
            np.array([31,29,29,29,-99999]))

        col_ = column(np.arange(1,4))

        # self.assertEqual(col_.year,None)

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

        df = DataFrame(col0=[],col1=[])
        a = np.array([1,2,3.])
        b = np.array([4,5,6.])

        df["col0"] = a
        df["col1"] = b

        self.assertCountEqual(df.heads,["col0","col1"],"Initialization of DataFrame Running has failed!")

        df["col0"] = b
        df["col1"] = a

        np.testing.assert_array_equal(df["col0"],b)
        np.testing.assert_array_equal(df["col1"],a)

    def test_col__astype(self):

        a = np.array([1,2,3,4,5])
        b = np.array([1.,3.4,np.nan,4.7,8])
        c = np.array([datetime.datetime.today(),datetime.datetime(2022,2,2),datetime.datetime(2022,1,2),datetime.datetime(2021,12,2),None])
        d = np.array(["1.","","5.7","6",""])
        e = c.astype("datetime64")

        df = DataFrame(a=a,b=b,c=c,d=d,e=e)

        for dtype in ("int","str","float"):
            df[0].astype(dtype)

        bb = [
            np.array([1,3,-99999,4,8]),
            np.array(["1","3","","4","8"]),
            np.array([1.,3.,np.nan,4.,8.]),
            ]

        for index,dtype in enumerate(("int","str","float")):
            df[1].astype(dtype)
            np.testing.assert_array_equal(df[1].vals,bb[index])

        for dtype in ("str","datetime64[D]"):
            df[2].astype(dtype)

        for dtype in ("str","int","float"):

            if dtype=="int":
                df[3].fromstring(dtype="int",regex=r"[-+]?\d+\b")
                df[3].astype(dtype)
            else:
                df[3].astype(dtype)

        for dtype in ("str","datetime64[D]"):
            df[4].astype(dtype)

    def test_representation_methods(self):

        df = DataFrame(col0=[],col1=[])

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df["a"] = a
        df["b"] = b

    def test_add_attrs(self):

        df = DataFrame(col0=[],col1=[])

        df.add_attrs(name="raw_data")

        with self.assertLogs() as captured:
            df.add_attrs(name="raw_data_2")

        self.assertEqual(captured.records[0].getMessage(),
            "Added value after replacing name with name_1.")

        self.assertEqual(df.name,"raw_data")
        self.assertEqual(df.name_1,"raw_data_2")

    def test_add_glossary(self):

        df = DataFrame(A=[],B=[])

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

    def test_container_methods(self):

        df = DataFrame()

        a = np.random.randint(0,100,10)
        b = np.random.randint(0,100,10)

        df['a'] = a
        df['b'] = b

        np.testing.assert_array_equal(df["b"],df[1])

    def test_str2cols(self):

        head = "first name\tlast name"

        full_names = np.array(["elthon\tsmith","bill\tgates\tjohn"])

        df = DataFrame(head=full_names)

        df.str2cols("head",delimiter="\t")

        self.assertEqual(df.heads,["head","head_1","head_2"],
            "Splitting headers while splitting col_ has failed!")
        np.testing.assert_array_equal(df["head"],np.array(["elthon","bill"]))
        np.testing.assert_array_equal(df["head_1"],np.array(["smith","gates"]))
        np.testing.assert_array_equal(df["head_2"],np.array(["","john"]))

    def test_cols2str(self):

        names = np.array(["elthon","john"])
        nicks = np.array(["smith","verdin"])

        df = DataFrame(names=names,nicks=nicks)
        
        col__ = df.cols2str(["names","nicks"])

        np.testing.assert_array_equal(col__,np.array(["elthon smith","john verdin"]))

    def test_unique(self):

        df = DataFrame()

        A = np.array([1,1,1,2,2,3,3,3,4,5,6,6,6,6])
        B = np.array(["A","A","B","B","C","C","C","C","C","D","E","F","F","F"])

        df["A"] = A
        df["B"] = B

        df.unique(cols=(0,1))

        np.testing.assert_array_equal(df[0].vals,
            np.array([1,1,2,2,3,4,5,6,6]),err_msg="DataFrame.unique() has an issue!")

        np.testing.assert_array_equal(df.running[1],
            np.array(['A','B','B','C','C','C','D','E','F']),err_msg="DataFrame.unique() has an issue!")

    def test_write(self):

        pass

    def test_writeb(self):

        df = DataFrame(col0=[],col1=[])

        a = np.random.randint(0,100,20)
        b = np.random.randint(0,100,20)

        df["a"] = a
        df["b"] = b

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
