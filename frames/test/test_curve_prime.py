import datetime

from dateutil import relativedelta

import unittest

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from datum import column

from datum import key2column
        
class TestColumn(unittest.TestCase):

    # def test_init(self):

    #     col_ = column([],head="A")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([],dtype="float"))
    #     self.assertEqual(col_.head,"A")
    #     self.assertEqual(col_.unit,"dimensionless")
    #     self.assertEqual(col_.info," ")

    #     col_ = key2column(5,head='A')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.arange(5))
    #     self.assertEqual(col_.head,"A")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = key2column(5.,size=5,head='A')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.linspace(0,5,5))
    #     self.assertEqual(col_.head,"A")
    #     self.assertEqual(col_.unit,"dimensionless")
    #     self.assertEqual(col_.info," ")

    #     col_ = column('',head='A',size=5,dtype="U30")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.empty(5,dtype="U30"))
    #     self.assertEqual(col_.head,"A")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column(numpy.datetime64('NaT'),head="5 months",size=5,dtype="datetime64[D]",info="5 months starting from January 1, 2000")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([numpy.datetime64('NaT')]*5))
    #     self.assertEqual(col_.head,"5months")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info,"5 months starting from January 1, 2000")

    #     col_ = column(5,head="number")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([5]))
    #     self.assertEqual(col_.head,"number")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column(5.,head="number")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([5.]))
    #     self.assertEqual(col_.head,"number")
    #     self.assertEqual(col_.unit,"dimensionless")
    #     self.assertEqual(col_.info," ")

    #     col_ = column("textio.py",head="names")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(["textio.py"]))
    #     self.assertEqual(col_.head,"names")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     dt = datetime.datetime.today()
    #     col_ = column(dt,head="time,")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([dt],dtype="datetime64[s]"))
    #     self.assertEqual(col_.head,"time")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column(numpy.arange(5),head="Integers")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.arange(5))
    #     self.assertEqual(col_.head,"Integers")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column([1,2,3],head="Integers To Float",unit="cm")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,2,3]))
    #     self.assertEqual(col_.head,"IntegersToFloat")
    #     self.assertEqual(col_.unit,"cm")
    #     self.assertEqual(col_.info," ")

    #     col_ = column(numpy.linspace(1,1000,100000),head="Random Floating Numbers",unit="m")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.linspace(1,1000,100000))
    #     self.assertEqual(col_.head,"RandomFloatingNumbers")
    #     self.assertEqual(col_.unit,"m")
    #     self.assertEqual(col_.info," ")

    #     col_ = column(["1","5","7"],head="Strings To Float",unit="km")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1,5,7.]))
    #     self.assertEqual(col_.head,"StringsToFloat")
    #     self.assertEqual(col_.unit,"km")
    #     self.assertEqual(col_.info," ")

    #     col_ = column(["1","5","7"],head="Strings")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(["1","5","7"]))
    #     self.assertEqual(col_.head,"Strings")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     dt_list = [datetime.datetime.today()]*2
    #     col_ = column(dt_list,head="time")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(dt_list,dtype="datetime64[s]"))
    #     self.assertEqual(col_.head,"time")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")
        
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
        vals_true = numpy.array([datetime.datetime.today().date()]*2,dtype="datetime64[s]")
        numpy.testing.assert_array_equal(col_.vals,vals_true)
        self.assertEqual(col_.unit,None)

        col_ = column(["1.","2"],unit="m")
        numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,2.]))
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

    # def test_representation(self):
        
    #     col_ = column(head="integers",vals=-numpy.arange(1,10000))
    #     self.assertEqual(col_._valstr(),'[-1,-2,-3,...,-9997,-9998,-9999]')

    #     col_ = column(head="float",vals=numpy.linspace(1,1000,100000),unit="m")
    #     self.assertEqual(col_._valstr(),'[1.,1.0099901,1.0199802,...,999.9800198,999.9900099,1000.]')

    #     col_ = column(head="modules",vals=["1 textio.py","2 graphics.py","3 geometries.py","4 items.py"])
    #     self.assertEqual(col_._valstr(),"['1 textio.py','2 graphics.py','3 geometries.py','4 items.py']")

    #     vals = [datetime.datetime.today()-relativedelta.relativedelta(days=i) for i in reversed(range(1,11))]
    #     col_ = column(vals=vals,head="datetime")
    #     vals_ = numpy.array(vals,dtype="datetime64[s]")
    #     self.assertEqual(col_._valstr(2),"['{}',...,'{}']".format(vals_[0],vals_[-1]))

    def test_comparison(self):

        col_1 = column(vals=numpy.array([1,2,3]),head="length",unit="km")
        col_2 = col_1.convert("m")

        cond = col_1==col_2
        
        numpy.testing.assert_array_equal(cond,numpy.array([True,True,True]))

    # def test_search_methods(self):

    #     col_ = column(head="floats",vals=numpy.linspace(1,1000,100000),unit="m")

    #     self.assertEqual(col_.maxchar(),7,
    #         "maxchar() does not return correct number of chars in the largest str(float)!")

    #     # self.assertEqual(col_.maxchar(return_value=True),"1.0299702997029971")

    #     col_ = column(head="integers",vals=numpy.arange(50))

    #     self.assertEqual(col_.maxchar(),2,
    #         "maxchar() does not return correct number of chars in the largest str(ints)!")

    def test_container_methods(self):

        vals = numpy.linspace(1,5,5)
        col_ = column(vals=vals,head="floats",unit="m",info="linspace data")
        numpy.testing.assert_array_equal(col_[:],vals)

        col_[-1] = 50
        numpy.testing.assert_array_equal(col_[:],numpy.array([1,2,3,4,50]))

        self.assertEqual(len(col_),5)

    def test_conversion_astype(self):
        
        col_ = column(["1.","2"],unit="m")
        col_ = col_.astype("int")
        self.assertEqual(col_.unit,None)

        col_ = col_.astype("float")
        self.assertEqual(col_.unit,"dimensionless")

    def test_conversion_replace(self):

        A = column(vals=numpy.array([1,2,3,4,None,6]))
        B = column(vals=numpy.array([0,1,2,None,None,4]))

        A.replace(new=50)
        numpy.testing.assert_array_equal(A.vals,numpy.array([1,2,3,4,50,6]))
        B.replace()
        numpy.testing.assert_array_equal(B.vals,numpy.array([0,1,2,2,2,4]))

    def test_conversion_float_unit(self):

        col_1 = column(head="values",vals=["1.","2"],unit="m")
        col_2 = col_1.convert("km")
        self.assertEqual(col_1.unit,'m')
        self.assertEqual(col_2.unit,'km')
        numpy.testing.assert_array_equal(col_1.vals,numpy.array([1.,2.]))
        numpy.testing.assert_array_equal(col_2.vals,numpy.array([0.001,0.002]))

    # def test_conversion_from_to_string(self):

    #     col_ = column(numpy.arange(1,5))
    #     col_ = col_.tostring(fstring="{:d}")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(["1","2","3","4"]))
    #     self.assertEqual(col_.head,"HEAD")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")
        
    #     col_ = column(numpy.linspace(1,5,4),unit="km")
    #     col_ = col_.tostring(fstring="{:.1f}")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(["1.0","2.3","3.7","5.0"]))
    #     self.assertEqual(col_.head,"HEAD")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column(numpy.array(["78,.45,2","98,3.,28","1,75,3,."]))
    #     col_ = col_.tostring(fstring="{:15s}")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(['78,.45,2       ',
    #         '98,3.,28       ','1,75,3,.       ']))
    #     self.assertEqual(col_.head,"HEAD")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info," ")

    #     col_ = column(numpy.array(["john 78,45.2","valeria 98,3.28","throne 1,75,3.0"]))
    #     col_ = col_.fromstring('float64')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([7845.2,983.28,1753.0]))
    #     self.assertEqual(col_.head,"HEAD")
    #     self.assertEqual(col_.unit,'dimensionless')
    #     self.assertEqual(col_.info," ")

    #     col_ = column(vals=numpy.array(["elthon","john","1"]),head="string")
    #     col_ = col_.tostring(zfill=3)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(['elthon',
    #         'john','001']))

    #     dt1 = datetime.datetime.today()-relativedelta.relativedelta(months=0)
    #     dt0 = datetime.datetime.today()-relativedelta.relativedelta(months=1)
    #     col_ = key2column(size=2,step_unit="M",head="Dates",info="Two months",dtype="datetime64[D]")
    #     col_ = col_.tostring(fstring="Date is {%Y-%m-%d}")
    #     true_vals = (dt0,dt1)
    #     true_vals = ["Date is {}".format(dt.strftime("%Y-%m-%d")) for dt in true_vals]
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(true_vals))
    #     self.assertEqual(col_.head,"Dates")
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(col_.info,"Two months")

    # def test_shift(self):

    #     col_ = column(head="integers",vals=numpy.array([1,2,3,4,5],dtype="int"))
    #     col_ = col_.shift(5)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([6,7,8,9,10]))

    #     col_ = column(head="floats",vals=numpy.linspace(1,4,7),unit="km")
    #     col_ = col_.shift(5,"m")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([
    #         1.005,1.505,2.005,2.505,3.005,3.505,4.005]))

    #     col_ = column(["textio","petrophysics","helloworld!"])
    #     col_ = col_.shift(5)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([
    #         '     textio','     petrophysics','     helloworld!']))
        
    #     col_ = column(numpy.arange(numpy.datetime64('2019-02-27'),numpy.datetime64('2019-03-02'),numpy.timedelta64(1,'D')))
    #     col_ = col_.shift(1,'Y')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([
    #         numpy.datetime64('2020-02-27'),numpy.datetime64('2020-02-28'),numpy.datetime64('2020-03-01')]))
    #     col_ = col_.shift(7,'Y')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([
    #         numpy.datetime64('2027-02-27'),numpy.datetime64('2027-02-28'),numpy.datetime64('2027-03-01')]))
    #     col_ = col_.shift(100,'Y')
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([
    #         numpy.datetime64('2127-02-27'),numpy.datetime64('2127-02-28'),numpy.datetime64('2127-03-01')]))

    #     col__vals = numpy.array([
    #         datetime.datetime(2022,2,2),
    #         datetime.datetime(2022,1,2),
    #         datetime.datetime(2021,12,2),
    #         None])
        
    #     col_ = column(vals=col__vals)

    #     col_ = col_.shift(delta=-2,deltaunit='Y')
    #     col_ = col_.shift(delta=10,deltaunit='D')

    #     numpy.testing.assert_array_equal(col_.vals,
    #         numpy.array([
    #             numpy.datetime64('2020-02-12'),
    #             numpy.datetime64('2020-01-12'),
    #             numpy.datetime64('2019-12-12'),
    #             numpy.datetime64('NaT')]))

    #     col_ = column(vals=col__vals)

    #     col_ = col_.shift(delta=-2,deltaunit='M')

    #     numpy.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
    #         numpy.array([
    #             numpy.datetime64('2021-12-02'),
    #             numpy.datetime64('2021-11-02'),
    #             numpy.datetime64('2021-10-02'),
    #             numpy.datetime64('NaT')]))

    #     col_ = col_.toeom()

    #     numpy.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
    #         numpy.array([
    #             numpy.datetime64('2021-12-31'),
    #             numpy.datetime64('2021-11-30'),
    #             numpy.datetime64('2021-10-31'),
    #             numpy.datetime64('NaT')]))

    #     col_ = col_.tobom()

    #     numpy.testing.assert_array_equal(col_.vals.astype('datetime64[D]'),
    #         numpy.array([
    #             numpy.datetime64('2021-12-01'),
    #             numpy.datetime64('2021-11-01'),
    #             numpy.datetime64('2021-10-01'),
    #             numpy.datetime64('NaT')]))

    # def test_mathematical_operations(self):

    #     # Addition

    #     col_ = column(numpy.arange(1,7,2))
    #     colnew = col_+1
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1,3,5]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2,4,6]))

    #     colnew = col_+1.
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1,3,5]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2,4,6]))

    #     colnew = col_+"1"
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1,3,5]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2,4,6]))

    #     col_ = column(numpy.linspace(1,10,4))
    #     colnew = col_+1
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,4.,7.,10.]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2.,5.,8.,11.]))

    #     colnew = col_+"1"
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,4.,7.,10.]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2.,5.,8.,11.]))

    #     col_ = column(numpy.linspace(1,10,4),unit="m")
    #     with self.assertRaises(pint.errors.DimensionalityError):
    #         colnew = col_+1
    #     self.assertEqual(col_.unit,"m")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,4.,7.,10.]))

    #     colnew = col_+col_
    #     self.assertEqual(col_.unit,"m")
    #     self.assertEqual(colnew.unit,"m")
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array([1.,4.,7.,10.]))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array([2.,8.,14.,20.]))

    #     col_ = column(['john','boris','jonas'])
    #     colnew = col_+1
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(['john','boris','jonas']))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array(['john1','boris1','jonas1']))

    #     colnew = col_+" smith"
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(col_.vals,numpy.array(['john','boris','jonas']))
    #     numpy.testing.assert_array_equal(colnew.vals,numpy.array(['john smith','boris smith','jonas smith']))

    #     col_ = column([numpy.datetime64('2022-07-30'),numpy.datetime64('2022-07-30')])
    #     colnew = col_+column([1.5,2.],unit='year')
    #     self.assertEqual(col_.unit,None)
    #     self.assertEqual(colnew.unit,None)
    #     numpy.testing.assert_array_equal(
    #         col_.vals,numpy.array([numpy.datetime64('2022-07-30'),numpy.datetime64('2022-07-30')]))
    #     numpy.testing.assert_array_equal(
    #         colnew.vals,numpy.array([numpy.datetime64('2024-01-30'),numpy.datetime64('2024-07-30')]))

    #     # Floor Division


    #     # Multiplication

    #     col_ = column(numpy.linspace(1,1000,100000),unit="m")
        
    #     col_*2

    #     col_*col_

    #     # Not Equal

    #     # To The Power:

    #     # Subtraction

    #     col_ = column(numpy.linspace(1,1000,100000),unit="m")
        
    #     col_-1
    #     col_-col_

    #     # True Division

    #     col_ = column(numpy.linspace(1,1000,100000),unit="m")
        
    #     col_/2
    #     col_/col_

    def test_advanced_methods(self):

        col_ = column(["sabrina","john","timathy"])
        colnew = col_.sort()
        numpy.testing.assert_array_equal(colnew.vals,numpy.array(["john","sabrina","timathy"]))

        col_ = column(["A","12text5","text345","125text","C","C","C","C","C","D","E","F","F","F"])
        colnew = col_.filter(["E","F"])
        numpy.testing.assert_array_equal(colnew.vals,numpy.array(["E","F","F","F"]))

        colnew = col_.filter(regex=r".*\d")
        numpy.testing.assert_array_equal(colnew.vals,numpy.array(["12text5","text345","125text"]))

        colnew = col_.unique()
        numpy.testing.assert_array_equal(colnew.vals,numpy.array(["125text","12text5","A","C","D","E","F","text345"]))

    # def test_appending(self):

    #     a = numpy.array([1,2,3,4,5])
    #     b = numpy.array([1.,3.4,numpy.nan,4.7,8])
    #     c = numpy.array([datetime.date(2022,1,1)])
    #     # d = numpy.array(["1.","","5.7","6",""])
    #     # e = c.astype("datetime64")

    #     a = column(a)
    #     a.append(b)
    #     numpy.testing.assert_array_equal(a.vals,numpy.array([1,2,3,4,5,1,3,-99999,4,8]))

    #     c = column(c)
    #     c.append(c)
    #     numpy.testing.assert_array_equal(c.vals,numpy.array([numpy.datetime64('2022-01-01'),numpy.datetime64('2022-01-01')]))

    def test_property_general_nondim(self):
        
        col_ = column(["1.","2"],unit="m")
        self.assertEqual(col_.nondim,False)

        col_ = col_.astype("int")
        self.assertEqual(col_.nondim,True)

    # def test_property_date_time(self):

    #     dates = numpy.arange(numpy.datetime64('2020-02-29'),numpy.datetime64('2020-03-04'),numpy.timedelta64(1,'D'))
    #     dates = numpy.append(dates,numpy.datetime64('NaT'))

    #     col_ = column(dates)
        
    #     numpy.testing.assert_array_equal(col_.year,
    #         numpy.array([2020,2020,2020,2020,-99999]))
    #     numpy.testing.assert_array_equal(col_.month,
    #         numpy.array([2,3,3,3,-99999]))
    #     numpy.testing.assert_array_equal(col_.day,
    #         numpy.array([29,1,2,3,-99999]))
    #     numpy.testing.assert_array_equal(col_.monthrange,
    #         numpy.array([29,31,31,31,-99999]))
    #     numpy.testing.assert_array_equal(col_.nextmonthrange,
    #         numpy.array([31,30,30,30,-99999]))
    #     numpy.testing.assert_array_equal(col_.prevmonthrange,
    #         numpy.array([31,29,29,29,-99999]))

    #     col_ = column(numpy.arange(1,4))

    #     # self.assertEqual(col_.year,None)

if __name__ == "__main__":

    unittest.main()
