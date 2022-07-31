import datetime

from dateutil import relativedelta

import unittest

import numpy as np
import pint

if __name__ == "__main__":
    import setup

from core import nones
from core import column
from core import any2column
from core import key2column

from cypy.vectorpy import str2float

class TestNones(unittest.TestCase):

    def test_nones(self):

        Nones = nones()
        Nones.datetime64 = np.datetime64('NaT')
        self.assertEqual(Nones.int,-99_999)

        Nones.int = 0.
        self.assertEqual(Nones.int,0)

        with self.assertRaises(AttributeError):
            Nones.dtypes

    def test_todict(self):

        Nones = nones()

        Nones.int = 0

        nones_dict = Nones.todict()

        nones_dict['none_float'] = -99999.999

        self.assertEqual(nones_dict["none_int"],0)
        self.assertEqual(nones_dict["none_float"],-99999.999)
        self.assertEqual(nones_dict["none_str"],"")
        self.assertEqual(np.isnan(nones_dict["none_datetime64"]),True)

        nones_dict = Nones.todict("int","str")

        self.assertEqual(len(nones_dict),2)
        
class TestColumn(unittest.TestCase):

    def test_init(self):

        col_ = column([],head="A")
        np.testing.assert_array_equal(col_.vals,np.array([],dtype="float"))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = key2column(5,head='A')
        np.testing.assert_array_equal(col_.vals,np.arange(5))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = key2column(5.,size=5,head='A')
        np.testing.assert_array_equal(col_.vals,np.linspace(0,5,5))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column('',head='A',size=5,dtype="U30")
        np.testing.assert_array_equal(col_.vals,np.empty(5,dtype="U30"))
        self.assertEqual(col_.head,"A")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(np.datetime64('NaT'),head="5 months",size=5,dtype="datetime64[D]",info="5 months starting from January 1, 2000")
        np.testing.assert_array_equal(col_.vals,np.array([np.datetime64('NaT')]*5))
        self.assertEqual(col_.head,"5months")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info,"5 months starting from January 1, 2000")

        col_ = column(5,head="number")
        np.testing.assert_array_equal(col_.vals,np.array([5]))
        self.assertEqual(col_.head,"number")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(5.,head="number")
        np.testing.assert_array_equal(col_.vals,np.array([5.]))
        self.assertEqual(col_.head,"number")
        self.assertEqual(col_.unit,"dimensionless")
        self.assertEqual(col_.info," ")

        col_ = column("textio.py",head="names")
        np.testing.assert_array_equal(col_.vals,np.array(["textio.py"]))
        self.assertEqual(col_.head,"names")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        dt = datetime.datetime.today()
        col_ = column(dt,head="time,")
        np.testing.assert_array_equal(col_.vals,np.array([dt],dtype="datetime64[s]"))
        self.assertEqual(col_.head,"time")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column(np.arange(5),head="Integers")
        np.testing.assert_array_equal(col_.vals,np.arange(5))
        self.assertEqual(col_.head,"Integers")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        col_ = column([1,2,3],head="Integers To Float",unit="cm")
        np.testing.assert_array_equal(col_.vals,np.array([1.,2,3]))
        self.assertEqual(col_.head,"IntegersToFloat")
        self.assertEqual(col_.unit,"cm")
        self.assertEqual(col_.info," ")

        col_ = column(np.linspace(1,1000,100000),head="Random Floating Numbers",unit="m")
        np.testing.assert_array_equal(col_.vals,np.linspace(1,1000,100000))
        self.assertEqual(col_.head,"RandomFloatingNumbers")
        self.assertEqual(col_.unit,"m")
        self.assertEqual(col_.info," ")

        col_ = column(["1","5","7"],head="Strings To Float",unit="km")
        np.testing.assert_array_equal(col_.vals,np.array([1,5,7.]))
        self.assertEqual(col_.head,"StringsToFloat")
        self.assertEqual(col_.unit,"km")
        self.assertEqual(col_.info," ")

        col_ = column(["1","5","7"],head="Strings")
        np.testing.assert_array_equal(col_.vals,np.array(["1","5","7"]))
        self.assertEqual(col_.head,"Strings")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")

        dt_list = [datetime.datetime.today()]*2
        col_ = column(dt_list,head="time")
        np.testing.assert_array_equal(col_.vals,np.array(dt_list,dtype="datetime64[s]"))
        self.assertEqual(col_.head,"time")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info," ")
        
    def test_init_set_head(self):
        
        col_ = column([datetime.datetime.today()]*2,head="time%")
        self.assertEqual(col_.head,"time")

        col_.head = 'Two_Dates'
        self.assertEqual(col_.head,"Two_Dates")

        col_.head = None
        self.assertEqual(col_.head,"Two_Dates")

        col_.head = 'Edited'
        self.assertEqual(col_.head,"Edited")

    def test_init_set_unit(self):
        
        col_ = column([datetime.datetime.today().date()]*2,head="time")
        self.assertEqual(col_.unit,None)

        col_.unit = None
        self.assertEqual(col_.unit,None)

        col_ = col_.astype('datetime64[s]')
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

    def test_init_set_info(self):
        
        col_ = column([datetime.datetime.today()]*2)
        self.assertEqual(col_.info," ")

        col_.info = 'INFO: Two Dates'
        self.assertEqual(col_.info,"INFO: Two Dates")

        col_.info = None
        self.assertEqual(col_.info,"INFO: Two Dates")

        col_.info = 'INFO: Edited'
        self.assertEqual(col_.info,"INFO: Edited")

    def test_representation(self):
        
        col_ = column(head="integers",vals=-np.arange(1,10000))
        self.assertEqual(col_._valstr(),'[-1,-2,-3,...,-9997,-9998,-9999]')

        col_ = column(head="float",vals=np.linspace(1,1000,100000),unit="m")
        self.assertEqual(col_._valstr(),'[1.,1.0099901,1.0199802,...,999.9800198,999.9900099,1000.]')

        col_ = column(head="modules",vals=["1 textio.py","2 graphics.py","3 geometries.py","4 items.py"])
        self.assertEqual(col_._valstr(),"['1 textio.py','2 graphics.py','3 geometries.py','4 items.py']")

        vals = [datetime.datetime.today()-relativedelta.relativedelta(days=i) for i in reversed(range(1,11))]
        col_ = column(vals=vals,head="datetime")
        vals_ = np.array(vals,dtype="datetime64[s]")
        self.assertEqual(col_._valstr(2),"['{}',...,'{}']".format(vals_[0],vals_[-1]))

    def test_comparison(self):


        col_1 = column(vals=np.array([1,2,3]),head="length",unit="km")
        col_2 = col_1.convert("m")

        cond = col_1==col_2
        
        np.testing.assert_array_equal(cond,np.array([True,True,True]))

    def test_search_methods(self):

        col_ = column(head="floats",vals=np.linspace(1,1000,100000),unit="m")

        self.assertEqual(col_.maxchar(),18,
            "maxchar() does not return correct number of chars in the largest str(float)!")

        self.assertEqual(col_.maxchar(return_value=True),"1.0299702997029971")

        col_ = column(head="integers",vals=np.arange(50))

        self.assertEqual(col_.maxchar(),2,
            "maxchar() does not return correct number of chars in the largest str(ints)!")

    def test_container_methods(self):

        vals = np.linspace(1,5,5)
        col_ = column(vals=vals,head="floats",unit="m",info="linspace data")
        np.testing.assert_array_equal(col_[:],vals)

        col_[-1] = 50
        np.testing.assert_array_equal(col_[:],np.array([1,2,3,4,50]))

        self.assertEqual(len(col_),5)

    def test_conversion_astype(self):
        
        col_ = column(["1.","2"],unit="m")
        col_ = col_.astype("int")
        self.assertEqual(col_.unit,None)

        col_ = col_.astype("float")
        self.assertEqual(col_.unit,"dimensionless")

    def test_conversion_replace(self):

        A = column(vals=np.array([1,2,3,4,None,6]))
        B = column(vals=np.array([0,1,2,None,None,4]))

        A.replace(new=50)
        np.testing.assert_array_equal(A.vals,np.array([1,2,3,4,50,6]))
        B.replace()
        np.testing.assert_array_equal(B.vals,np.array([0,1,2,2,2,4]))

    def test_conversion_float_unit(self):

        col_1 = column(head="values",vals=["1.","2"],unit="m")
        col_2 = col_1.convert("km")
        self.assertEqual(col_1.unit,'m')
        self.assertEqual(col_2.unit,'km')
        np.testing.assert_array_equal(col_1.vals,np.array([1.,2.]))
        np.testing.assert_array_equal(col_2.vals,np.array([0.001,0.002]))

    def test_conversion_from_to_string(self):

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

        col_ = column(np.array(["john 78,45.2","valeria 98,3.28","throne 1,75,3.0"]))
        col_ = col_.fromstring('float64')
        np.testing.assert_array_equal(col_.vals,np.array([7845.2,983.28,1753.0]))
        self.assertEqual(col_.head,"HEAD")
        self.assertEqual(col_.unit,'dimensionless')
        self.assertEqual(col_.info," ")

        col_ = column(vals=np.array(["elthon","john","1"]),head="string")
        col_ = col_.tostring(zfill=3)
        np.testing.assert_array_equal(col_.vals,np.array(['elthon',
            'john','001']))

        dt1 = datetime.datetime.today()-relativedelta.relativedelta(months=0)
        dt0 = datetime.datetime.today()-relativedelta.relativedelta(months=1)
        col_ = key2column(size=2,step_unit="M",head="Dates",info="Two months",dtype="datetime64[D]")
        col_ = col_.tostring(fstring="Date is {%Y-%m-%d}")
        true_vals = (dt0,dt1)
        true_vals = ["Date is {}".format(dt.strftime("%Y-%m-%d")) for dt in true_vals]
        np.testing.assert_array_equal(col_.vals,np.array(true_vals))
        self.assertEqual(col_.head,"Dates")
        self.assertEqual(col_.unit,None)
        self.assertEqual(col_.info,"Two months")

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
            np.datetime64('2020-02-27'),np.datetime64('2020-02-28'),np.datetime64('2020-03-01')]))
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

        col_ = col_.toeom()

        np.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
            np.array([
                np.datetime64('2021-12-31'),
                np.datetime64('2021-11-30'),
                np.datetime64('2021-10-31'),
                np.datetime64('NaT')]))

        col_ = col_.tobom()

        np.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
            np.array([
                np.datetime64('2021-12-01'),
                np.datetime64('2021-11-01'),
                np.datetime64('2021-10-01'),
                np.datetime64('NaT')]))

    def test_mathematical_operations(self):

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

        col_ = column([np.datetime64('2022-07-30'),np.datetime64('2022-07-30')])
        colnew = col_+column([1.5,2.],unit='year')
        self.assertEqual(col_.unit,None)
        self.assertEqual(colnew.unit,None)
        np.testing.assert_array_equal(
            col_.vals,np.array([np.datetime64('2022-07-30'),np.datetime64('2022-07-30')]))
        np.testing.assert_array_equal(
            colnew.vals,np.array([np.datetime64('2024-01-30'),np.datetime64('2024-07-30')]))

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

    def test_property_general_nondim(self):
        
        col_ = column(["1.","2"],unit="m")
        self.assertEqual(col_.nondim,False)

        col_ = col_.astype("int")
        self.assertEqual(col_.nondim,True)

    def test_property_date_time(self):

        dates = np.arange(np.datetime64('2020-02-29'),np.datetime64('2020-03-04'),np.timedelta64(1,'D'))
        dates = np.append(dates,np.datetime64('NaT'))

        col_ = column(dates)
        
        np.testing.assert_array_equal(col_.year,
            np.array([2020,2020,2020,2020,-99999]))
        np.testing.assert_array_equal(col_.month,
            np.array([2,3,3,3,-99999]))
        np.testing.assert_array_equal(col_.day,
            np.array([29,1,2,3,-99999]))
        np.testing.assert_array_equal(col_.monthrange,
            np.array([29,31,31,31,-99999]))
        np.testing.assert_array_equal(col_.nextmonthrange,
            np.array([31,30,30,30,-99999]))
        np.testing.assert_array_equal(col_.prevmonthrange,
            np.array([31,29,29,29,-99999]))

        col_ = column(np.arange(1,4))

        # self.assertEqual(col_.year,None)

class TestArray(unittest.TestCase):

    def test_init(self):

        arr_ = key2column(5)
        np.testing.assert_array_equal(arr_,np.arange(5))

        arr_ = key2column(5.)
        np.testing.assert_array_equal(arr_,np.arange(5,dtype='float64'))

        arr_ = key2column('E')
        np.testing.assert_array_equal(arr_,np.array(['A','B','C','D','E']))

        arr_ = key2column('2022-05-01','2022-07-29')
        arr_true = np.array([
            datetime.date(2022,5,1),
            datetime.date(2022,6,1),
            datetime.date(2022,7,1)],
            dtype='datetime64[s]')

        np.testing.assert_array_equal(arr_,arr_true)

        arr_ = any2column(('Python','NumPy','Great!'),dtype='str')
        arr2 = any2column(('Python','NumPy','Great!'))

        np.testing.assert_array_equal(
            arr_.vals,np.array(['Python','NumPy','Great!']))

        np.testing.assert_array_equal(arr_.vals,arr2.vals)

if __name__ == "__main__":

    unittest.main()
