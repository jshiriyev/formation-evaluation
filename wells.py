from dataclasses import dataclass

import json

import os

from matplotlib import pyplot

import numpy

if __name__ == "__main__":
    import dirsetup

from datum import frame
from datum import column

from textio import header
from textio import dirmaster

filedir = os.path.dirname(__file__)

filepath = os.path.join(filedir,"wells.json")

with open(filepath,"r") as jsonfile:
    library = json.load(jsonfile)

@dataclass
class Config:
    
    name: str = None
    index: int = None
    platform: str = None
    field: str = None
    xhead: float = 0.0
    yhead: float = 0.0
    datum: float = 0.0
    status: str = "prospect"

class Slot():

    def __init__(self,config:Config):

        self.name = config.name
        self.index = config.index
        self.platform = config.platform
        self.field = config.field
        self.xhead = config.xhead
        self.yhead = config.yhead
        self.datum = config.datum
        self.status = config.status

    def set_track(self,headers=["X","Y","Z","MD"],**kwargs):

        super().__init__(headers=headers,**kwargs)

    def set_tops(self):

        pass

class Stock():

    itemnames = []                 # well names
    statuses = []
    radii = []
    flowconds = []

    def __init__(self,number=0,wnamefstr=None,**kwargs):

        super().__init__(**kwargs)

        self.wnamefstr = "Well-{}" if wnamefstr is None else wnamefstr

    def set_names(self,*args,wnamefstr=None,sortFlag=False):

        warnNWIF = "No well name was added or could be found."

        [self.itemnames.append(str(arg)) for arg in args]

        if len(args)==0:

            twells = np.unique(self.Trajectory.get_wellnames())
            cwells = np.unique(self.Completion.get_wellnames())
            lwells = np.unique(self.Logging.get_wellnames())
            pwells = np.unique(self.Production.get_wellnames())

            self.itemnames = np.concatenate((twells,cwells,lwells,pwells)).tolist()

        self.number = len(self.itemnames)

        if self.number==0:
            warnings.warn(warnNWIF)
            return

        if wnamefstr is not None:
            self.wnamefstr = wnamefstr      # string format to save well names

        get_digits = lambda x: re.sub("[^0-9]","",x)

        get_digitnum = lambda x: len(get_digits(x))
        arr_digitnum = np.vectorize(get_digitnum)

        max_digitnum = arr_digitnum(self.itemnames).max()

        get_wellname = lambda x: self.wnamefstr.format(get_digits(x).zfill(max_digitnum))
        arr_wellname = np.vectorize(get_wellname)

        self.itemnames = arr_wellname(self.itemnames)

        # self.itemnames = np.unique(np.array(self.itemnames)).tolist()

        if sortFlag:
            self.itemnames.sort()

    def set_statuses(self,*args,):

        for arg in args:
            self.statuses.append(arg)

    def set_radii(self,*args):

        for arg in args:
            self.radii.append(arg)

        self.radii = np.array(self.radii)

    def set_flowconds(self,conditions,limits,fluids=None):

        self.consbhp = np.array(conditions)=="bhp"

        self.limits = np.array(limits)

        if fluids is not None:
            self.water = (np.array(fluids)!="oil")
            self.oil = (np.array(fluids)!="water")

    def set_skinfactors(self,*args,skinfactorlist=None):

        self.skinfactors = []

        for arg in args[:self.number]:
            self.skinfactors.append(arg)

        if skinfactorlist is not None:
            self.skinfactors = skinfactorlist

        self.skinfactors = np.array(self.skinfactors)

    def set_schedule(self,wellname):

        flagShowSteps = False if wellname is None else True

        warnNOPROD = "{} has completion but no production data."
        warnNOCOMP = "{} has production but no completion data."

        path1 = os.path.join(self.workdir,self.filename_op+"2")
        path2 = os.path.join(self.workdir,self.filename_comp+"1")
        path3 = os.path.join(self.workdir,self.filename_comp+"uni")

        self.op_get(filending="2")
        self.comp_get(filending="1")
        self.comp_get(filending="uni")

        prodwellnames = np.unique(self.op2.running[0])
        compwellnames = np.unique(self.comp1.running[0])

        for wname in np.setdiff1d(prodwellnames,compwellnames):
            warnings.warn(warnNOCOMP.format(wname))

        for wname in np.setdiff1d(compwellnames,prodwellnames):
            warnings.warn(warnNOPROD.format(wname))

        proddata = frame(headers=self.headers_op[:7])
        schedule = frame(headers=self.schedule_headers)

        for wname in self.itemnames:

            if wellname is not None:
                if wellname!=wname:
                    continue

            self.get_conflict(wname)

            shutdates = np.array(shutdates,dtype=object)
            shutwells = np.empty(shutdates.shape,dtype=object)

            shutwells[:] = wname

            shutdays = np.zeros(shutdates.shape,dtype=int)

            shutoptype = np.empty(shutdates.shape,dtype=object)

            shutoptype[:] = "shut"

            shutroil = np.zeros(shutdates.shape,dtype=int)
            shutrwater = np.zeros(shutdates.shape,dtype=int)
            shutrgas = np.zeros(shutdates.shape,dtype=int)

            rows = np.array([shutwells,shutdates,shutdays,shutoptype,shutroil,shutrwater,shutrgas]).T.tolist()

            proddata.set_rows(rows)

            if flagShowSteps:
                print("{} check is complete.".format(wname))

        proddata.sort(header_indices=[1],inplace=True)

        toil = np.cumsum(proddata.running[4])
        twater = np.cumsum(proddata.running[5])
        tgas = np.cumsum(proddata.running[6])

        proddata.set_column(toil,header_new="TOIL")
        proddata.set_column(twater,header_new="TWATER")
        proddata.set_column(tgas,header_new="TGAS")

        proddata.astype(header=self.headers_op[2],dtype=int)

        path = os.path.join(self.workdir,self.filename_op+"3")

        fstring = "{:6s}\t{:%Y-%m-%d}\t{:2d}\t{:10s}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\n"

        proddata.write(filepath=path,fstring=fstring)

    def get_conflicts(self,wellname):

        warnCROSS = "{} production has been defined before completion."

        warnWPGPF = "{:%Y-%m-%d}: {} first perf and last plug dates do not fit production days."
        warnWPERF = "{:%Y-%m-%d}: {} first perf date does not fit production days."
        warnWPLUG = "{:%Y-%m-%d}: {} last plug date does not fit production days."
        warnWEFAC = "{:%Y-%m-%d}: {} efficiency is more than unit [{:2d} out of {:2d} days]."

        self.op2.filter(0,keywords=[wname],inplace=False)

        self.comp1.filter(0,keywords=[wname],inplace=False)
        self.compuni.filter(0,keywords=[wname],inplace=False)

        try:
            datemin = self.op2.running[1].min()
        except ValueError:
            datemin = datetime(3000,1,1)

        date = datemin+relativedelta(months=1)

        days = calendar.monthrange(date.year,date.month)[1]

        date = datetime(date.year,date.month,days)

        if self.compuni.running[1].min()>=date:
            warnings.warn(warnCROSS.format(wname))

        schedule.set_rows([[self.comp1.running[1][0],"WELSPECS",self.schedule_welspecs.format(wname)]])

        for compdate,compevent,comptop,compbottom in zip(self.comp1.running[1],self.comp1.running[2],self.comp1.running[3],self.comp1.running[4]):

            if compevent == "PERF":
                schedule.set_rows([[compdate,"COMPDATMD",self.schedule_compdatop.format(wname,comptop,compbottom,"OPEN")]])
            elif compevent == "PLUG":
                schedule.set_rows([[compdate,"COMPDATMD",self.schedule_compdatsh.format(wname,comptop,"1*","SHUT")]])

        for compunidate in self.compuni.running[1]:

            schedule.set_rows([[compunidate,"COMPORD",self.schedule_compord.format(wname)]])

        flagNoPrevProd = True

        print("{} schedule is in progress ...".format(wname))

        opdata = zip(
            self.op2.running[1],
            self.op2.running[2],
            self.op2.running[3],
            self.op2.running[4],
            self.op2.running[5],
            self.op2.running[6],
            )

        shutdates = []

        for index,(date,days,optype,oil,water,gas) in enumerate(opdata):

            prodmonthSTARTday = date+relativedelta(days=1)

            prodmonthdaycount = calendar.monthrange(prodmonthSTARTday.year,prodmonthSTARTday.month)[1]

            prodmonthENDday = datetime(prodmonthSTARTday.year,prodmonthSTARTday.month,prodmonthdaycount)

            if np.sum(self.compuni.running[1]<prodmonthSTARTday)==0:
                compSTARTindex = 0
            else:
                compSTARTindex = np.sum(self.compuni.running[1]<prodmonthSTARTday)-1

            compENDindex = np.sum(self.compuni.running[1]<=prodmonthENDday)

            compupdatedates = self.compuni.running[1][compSTARTindex:compENDindex]
            compupdatecounts = self.compuni.running[2][compSTARTindex:compENDindex]

            perfdates = compupdatedates[compupdatecounts!=0]
            plugdates = compupdatedates[compupdatecounts==0]

            try:
                flagNoPostProd = True if self.op2.running[1][index+1]-relativedelta(months=1)>prodmonthENDday else False
            except IndexError:
                flagNoPostProd = True

            if np.sum(self.compuni.running[1]<prodmonthSTARTday)==0:
                flagCompShutSTART = True
            else:
                flagCompShutSTART = compupdatecounts[0]==0

            flagCompShutEND = compupdatecounts[-1]==0

            flagPlugPerf = any([compopencount==0 for compopencount in compupdatecounts[1:-1]])

            if flagCompShutSTART and flagCompShutEND:
                compday = plugdates[-1].day-perfdates[0].day
                prodeff = days/compday
                if optype == "production":
                    schedule.set_rows([[perfdates[0],"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                elif optype == "injection":
                    schedule.set_rows([[perfdates[0],"WCONINJH",self.schedule_injhist.format(wname,water)]])
                schedule.set_rows([[perfdates[0],"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                proddata.set_rows([[wname,perfdates[0],days,optype,oil,water,gas]])
                schedule.set_rows([[plugdates[-1],"WELOPEN",self.schedule_welopen.format(wname)]])
                shutdates.append(plugdates[-1])
                flagNoPrevProd = True
                if flagShowSteps:
                    print("{:%d %b %Y} Peforated and Plugged: OPEN ({:%d %b %Y}) and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,perfdates[0],plugdates[-1],prodeff))

            elif flagCompShutSTART:
                compday = prodmonthENDday.day-perfdates[0].day
                prodeff = days/compday
                if optype == "production":
                    schedule.set_rows([[perfdates[0],"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                elif optype == "injection":
                    schedule.set_rows([[perfdates[0],"WCONINJH",self.schedule_injhist.format(wname,water)]])
                schedule.set_rows([[perfdates[0],"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                proddata.set_rows([[wname,perfdates[0],days,optype,oil,water,gas]])
                if flagNoPostProd:
                    schedule.set_rows([[prodmonthENDday,"WELOPEN",self.schedule_welopen.format(wname)]])
                    shutdates.append(prodmonthENDday)
                    flagNoPrevProd = True
                    if flagShowSteps:
                        print("{:%d %b %Y} Peforated and Open: OPEN ({:%d %b %Y}) and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,perfdates[0],prodmonthENDday,prodeff))
                else:                  
                    flagNoPrevProd = False
                    if flagShowSteps:
                        print("{:%d %b %Y} Peforated and Open: OPEN ({:%d %b %Y}) and CONT WEFAC ({:.3f})".format(prodmonthENDday,perfdates[0],prodeff))

            elif flagCompShutEND:
                for plugdate in plugdates:
                    if plugdate.day>=days: break
                if not plugdate.day>=days:
                    warnings.warn(warnWPLUG.format(prodmonthENDday,wname))
                compday = plugdate.day
                prodeff = days/compday
                if optype == "production":
                    schedule.set_rows([[date,"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                elif optype == "injection":
                    schedule.set_rows([[date,"WCONINJH",self.schedule_injhist.format(wname,water)]])
                schedule.set_rows([[date,"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                proddata.set_rows([[wname,date,days,optype,oil,water,gas]])
                schedule.set_rows([[plugdate,"WELOPEN",self.schedule_welopen.format(wname)]])
                shutdates.append(plugdate)
                flagNoPrevProd = True
                if flagShowSteps:
                    print("{:%d %b %Y} Open and Plugged: CONT and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,plugdate,prodeff))

            elif flagPlugPerf:
                if flagNoPrevProd and flagNoPostProd:
                    # shift the start day to the first perf day
                    # shut the well at the last plug day
                    if not plugdates[-1].day-perfdates[1].day>=days:
                        warnings.warn(warnWPGPF.format(prodmonthENDday,wname))
                    compday = plugdates[-1].day-perfdates[1].day
                    prodeff = days/compday
                    if optype == "production":
                        schedule.set_rows([[perfdates[1],"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                    elif optype == "injection":
                        schedule.set_rows([[perfdates[1],"WCONINJH",self.schedule_injhist.format(wname,water)]])
                    schedule.set_rows([[perfdates[1],"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                    proddata.set_rows([[wname,perfdates[1],days,optype,oil,water,gas]])
                    schedule.set_rows([[plugdates[-1],"WELOPEN",self.schedule_welopen.format(wname)]])
                    shutdates.append(plugdates[-1])
                    flagNoPrevProd = True
                    if flagShowSteps:
                        print("{:%d %b %Y} Plugged and Perforated: OPEN ({:%d %b %Y}) and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,perfdates[1],plugdates[-1],prodeff))
                elif flagNoPrevProd and not flagNoPostProd:
                    # shift the start day to the proper perf day
                    for perfdate in np.flip(perfdates[1:]):
                        if prodmonthENDday.day-perfdate.day>=days: break
                    if not prodmonthENDday.day-perfdate.day>=days:
                        warnings.warn(warnWPERF.format(prodmonthENDday,wname))
                    compday = prodmonthENDday.day-perfdate.day
                    prodeff = days/compday
                    if optype == "production":
                        schedule.set_rows([[perfdate,"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                    elif optype == "injection":
                        schedule.set_rows([[perfdate,"WCONINJH",self.schedule_injhist.format(wname,water)]])
                    schedule.set_rows([[perfdate,"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                    proddata.set_rows([[wname,perfdate,days,optype,oil,water,gas]])
                    flagNoPrevProd = False
                    if flagShowSteps:
                        print("{:%d %b %Y} Plugged and Perforated: OPEN ({:%d %b %Y}) and CONT WEFAC ({:.3f})".format(prodmonthENDday,perfdate,prodeff))
                elif not flagNoPrevProd and flagNoPostProd:
                    # try shut the well at the proper plug day if not successful shut it at the end of month
                    for plugdate in plugdates:
                        if plugdate.day>=days: break
                    if not plugdate.day>=days:
                        plugdate = prodmonthENDday
                    compday = plugdate.day
                    prodeff = days/compday
                    if optype == "production":
                        schedule.set_rows([[date,"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                    elif optype == "injection":
                        schedule.set_rows([[date,"WCONINJH",self.schedule_injhist.format(wname,water)]])
                    schedule.set_rows([[date,"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                    proddata.set_rows([[wname,date,days,optype,oil,water,gas]])
                    schedule.set_rows([[plugdate,"WELOPEN",self.schedule_welopen.format(wname)]])
                    shutdates.append(plugdate)
                    flagNoPrevProd = True
                    if flagShowSteps:
                        print("{:%d %b %Y} Plugged and Perforated: CONT and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,plugdate,prodeff))
                elif not flagNoPrevProd and not flagNoPostProd:
                    # try shut the well if not successful do nothing
                    for plugdate in plugdates:
                        if plugdate.day>=days: break
                    if not plugdate.day>=days:
                        compday = prodmonthdaycount
                        prodeff = days/compday
                        flagNoPrevProd = False
                        if flagShowSteps:
                            print("{:%d %b %Y} Plugged and Perforated: CONT and CONT WEFAC ({:.3f})".format(prodmonthENDday,prodeff))
                    else:
                        compday = plugdate.day
                        prodeff = days/compday
                        schedule.set_rows([[plugdate,"WELOPEN",self.schedule_welopen.format(wname)]])
                        shutdates.append(plugdate)
                        flagNoPrevProd = True
                        if flagShowSteps:
                            print("{:%d %b %Y} Plugged and Perforated: CONT and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,plugdate,prodeff))
                    if optype == "production":
                        schedule.set_rows([[date,"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                    elif optype == "injection":
                        schedule.set_rows([[date,"WCONINJH",self.schedule_injhist.format(wname,water)]])
                    schedule.set_rows([[date,"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                    proddata.set_rows([[wname,date,days,optype,oil,water,gas]])

            else:
                compday = prodmonthdaycount
                prodeff = days/compday
                if optype == "production":
                    schedule.set_rows([[date,"WCONHIST",self.schedule_prodhist.format(wname,oil,water,gas)]])
                elif optype == "injection":
                    schedule.set_rows([[date,"WCONINJH",self.schedule_injhist.format(wname,water)]])
                schedule.set_rows([[date,"WEFAC",self.schedule_wefac.format(wname,prodeff)]])
                proddata.set_rows([[wname,date,days,optype,oil,water,gas]])
                if flagNoPostProd:
                    schedule.set_rows([[prodmonthENDday,"WELOPEN",self.schedule_welopen.format(wname)]])
                    shutdates.append(prodmonthENDday)
                    flagNoPrevProd = True
                    if flagShowSteps:
                        print("{:%d %b %Y} No completion events: CONT and SHUT ({:%d %b %Y}) WEFAC ({:.3f})".format(prodmonthENDday,prodmonthENDday,prodeff))
                else:
                    flagNoPrevProd = False
                    if flagShowSteps:
                        print("{:%d %b %Y} No completion events: CONT and CONT WEFAC ({:.3f})".format(prodmonthENDday,prodeff))

            if prodeff>1:
                warnings.warn(warnWEFAC.format(prodmonthENDday,wname,days,compday))

    def set_itemnames(self,namelist,fstring=None,zfill=3):
        
        fstring = "{}" if fstring is None else fstring

        getwname = lambda x: fstring.format(re.sub(r"[^\d]","",str(x)).zfill(zfill))

        getwname = np.vectorize(getwname)

        self.itemnames = getwname(namelist)

    def set_distance(self,depth=None):

        coords = np.zeros((len(self.files),3))

        for index,data in enumerate(self.files):

            if depth is None:
                depthIndex = 0

            coords[index,:] = data[depthIndex,:3]

        dx = coords[:,0]-coords[:,0].reshape((-1,1))
        dy = coords[:,1]-coords[:,1].reshape((-1,1))
        dz = coords[:,2]-coords[:,2].reshape((-1,1))

        self.distance = np.sqrt(dx**2+dy**2+dz**2)

    def get_kneighbors(self,k=1):

        min_indices = np.zeros((self.distance.shape[0],k),dtype=int)

        for index_self,row in enumerate(self.distance):

            indices = np.argpartition(row,range(k+1))[:k+1]

            min_indices[index_self,:] = np.delete(indices,indices==index_self)

        return min_indices

    def set_tracks(self,tracks):

        self.tracks = np.array(tracks)

class Tops():

    def __init__(self):

        pass

class TimeCurve():

    def __init__(self):

        pass

class Completion():

    headersRAW = ["Wells","Horizont","Top","Bottom","start","stoped",]

    headersOPT = ["WELL","DATE","EVENT","TOP","BOTTOM","DIAM",]

    headersUNI = ["WELL","DATE","COUNT",]
    
    def __init__(self):

        pass

    def get_wellnames(self):

        pass

    def comp_call(self,wellname=None):

        warnWELLNAME = "{} has name conflict in completion directory."
        warnFORMNAME = "{} does not have proper layer name in completion directory."
        warnUPPDEPTH = "{} top level depths must be positive in completion directory."
        warnBTMDEPTH = "{} bottom level depths must be positive in completion directory."
        warnUPBOTTOM = "{} top level must be smaller than bottom levels in completion directory."
        warnSTRTDATE = "{} start date is not set properly in completion directory."
        warnSTOPDATE = "{} stop date is not set properly in completion directory."
        warnSTARTEND = "{} start date is after or equal to stop date in completion directory."

        compraw = frame(headers=self.headers_compraw)

        for wname in self.itemnames:

            print("{} gathering completion data ...".format(wname))

            wellindex = int(re.sub("[^0-9]","",wname))

            folder1 = "GD-{}".format(str(wellindex).zfill(3))

            filename = "GD-{}.xlsx".format(str(wellindex).zfill(3))

            filepath = os.path.join(self.comprawdir,folder1,filename)
            
            comp = frame(filepath=filepath,sheetname=folder1,headerline=1,skiplines=2,min_row=2,min_col=2)

            comp.get_columns(headers=self.headers_compraw,inplace=True)

            comp.astype(header=self.headers_compraw[2],dtype=np.float64)
            comp.astype(header=self.headers_compraw[3],dtype=np.float64)

            if np.any(comp.running[0]!=wname):
                warnings.warn(warnWELLNAME.format(wname))

            if np.any(comp.running[1]==None) or np.any(np.char.strip(comp.running[1].astype(str))==""):
                warnings.warn(warnFORMNAME.format(wname))

            if np.any(comp.running[2]<0):
                warnings.warn(warnUPPDEPTH.format(wname))

            if np.any(comp.running[3]<0):
                warnings.warn(warnBTMDEPTH.format(wname))

            if np.any(comp.running[2]-comp.running[3]>0):
                warnings.warn(warnUPBOTTOM.format(wname))

            if any([not isinstance(value,datetime) for value in comp.running[4].tolist()]):
                warnings.warn(warnSTRTDATE.format(wname))

            indices = [not isinstance(value,datetime) for value in comp.running[5].tolist()]

            if any(indices) and np.any(comp.running[5][indices]!="ACTIVE"):
                warnings.warn(warnSTOPDATE.format(wname))

            comp.running[5][indices] = datetime.now()

            if any([(s2-s1).days<0 for s1,s2 in zip(comp.running[4].tolist(),comp.running[5].tolist())]):
                warnings.warn(warnSTARTEND.format(wname))

            compraw.set_rows(comp.get_rows())

        path = os.path.join(self.workdir,self.filename_comp+"0")

        fstring = "{:6s}\t{}\t{:.1f}\t{:.1f}\t{:%Y-%m-%d}\t{:%Y-%m-%d}\n"

        compraw.write(filepath=path,fstring=fstring)

    def comp_process(self):

        path = os.path.join(self.workdir,self.filename_comp+"0")

        comp1 = frame(filepath=path,skiplines=1)
        comp2 = frame(filepath=path,skiplines=1)

        comp1.texttocolumn(0,deliminator="\t")
        comp2.texttocolumn(0,deliminator="\t")

        headers_compraw1 = self.headers_compraw[:4]+(self.headers_compraw[4],)
        headers_compraw2 = self.headers_compraw[:4]+(self.headers_compraw[5],)

        comp1.get_columns(headers=headers_compraw1,inplace=True)
        comp2.get_columns(headers=headers_compraw2,inplace=True)

        comp1.astype(header=headers_compraw1[2],dtype=np.float64)
        comp1.astype(header=headers_compraw1[3],dtype=np.float64)
        comp1.astype(header=headers_compraw1[4],datestring=True)

        comp2.astype(header=headers_compraw2[2],dtype=np.float64)
        comp2.astype(header=headers_compraw2[3],dtype=np.float64)
        comp2.astype(header=headers_compraw2[4],datestring=True)

        col_perf = np.empty(comp1.running[0].size,dtype=object)
        col_perf[:] = "PERF"

        col_diam = np.empty(comp1.running[0].size,dtype=object)
        col_diam[:] = "0.14"

        comp1.set_column(col_perf,header_new="EVENT")
        comp1.set_column(col_diam,header_new="DIAM")

        col_plug = np.empty(comp2.running[0].size,dtype=object)
        col_plug[:] = "PLUG"

        col_none = np.empty(comp2.running[0].size,dtype=object)
        col_none[:] = ""

        comp2.set_column(col_plug,header_new="EVENT")
        comp2.set_column(col_none,header_new="DIAM")

        comp1.set_rows(comp2.get_rows())

        comp1.set_header(0,self.headers_comp[0])
        comp1.set_header(2,self.headers_comp[3])
        comp1.set_header(3,self.headers_comp[4])
        comp1.set_header(4,self.headers_comp[1])

        comp1.get_columns(headers=self.headers_comp,inplace=True)

        comp1.sort(header_indices=[1],inplace=True)

        path = os.path.join(self.workdir,self.filename_comp+"1")

        fstring = "{:6s}\t{:%Y-%m-%d}\t{:4s}\t{:.1f}\t{:.1f}\t{:4s}\n"

        comp1.write(filepath=path,fstring=fstring)

        compuni = frame(headers=self.headers_compuni)

        for wname in self.itemnames:

            comp1.filter(0,keywords=[wname],inplace=False)

            update_dates = np.unique(comp1.running[1])
            update_wells = np.empty(update_dates.size,dtype=object)
            update_counts = np.zeros(update_dates.size,dtype=int)

            update_wells[:] = wname

            update_indices = np.insert(
                np.cumsum(np.sum(comp1.running[1]==update_dates.reshape((-1,1)),axis=1)),0,0)

            open_intervals = np.empty((0,2))

            for index,date in enumerate(update_dates):

                compevents = comp1.running[2][update_indices[index]:update_indices[index+1]]
                compuppers = comp1.running[3][update_indices[index]:update_indices[index+1]]
                complowers = comp1.running[4][update_indices[index]:update_indices[index+1]]

                perfevents = compevents=="PERF"

                perfintervals = np.array([compuppers[perfevents],complowers[perfevents]]).T

                open_intervals = np.concatenate((open_intervals,perfintervals),axis=0)

                plugevents = compevents=="PLUG"

                pluguppermatch = np.any(open_intervals[:,0]==compuppers[plugevents].reshape((-1,1)),axis=0)
                pluglowermatch = np.any(open_intervals[:,1]==complowers[plugevents].reshape((-1,1)),axis=0)

                plugmatch = np.where(np.logical_and(pluguppermatch,pluglowermatch))[0]

                open_intervals = np.delete(open_intervals,plugmatch,0)

                update_counts[index] = open_intervals.shape[0]

            rows = np.array([update_wells,update_dates,update_counts]).T.tolist()

            compuni.set_rows(rows)

        compuni.astype(header_index=2,dtype=int)

        compuni.sort(header_indices=[1],inplace=True)

        path = os.path.join(self.workdir,self.filename_comp+"uni")

        fstring = "{:6s}\t{:%Y-%m-%d}\t{:d}\n"

        compuni.write(filepath=path,fstring=fstring)

    def comp_get(self,filending=None,wellname=None):

        for filename in os.listdir(self.workdir):

            if filename[:len("completion")]=="completion":

                path = os.path.join(self.workdir,filename)

                ending = filename[len("completion"):]

                if filename[:4]+ending in self.attrnames:
                    continue

                if filending is not None:
                    if filending!=ending:
                        continue

                try:
                    index = int(ending)
                except ValueError:
                    index = None

                attrname = filename[:4]+ending

                attrvals = frame(filepath=path,skiplines=1)

                setattr(self,attrname,attrvals)

                if index is not None:

                    if index==0:
                        getattr(self,attrname).texttocolumn(0,deliminator="\t")
                        getattr(self,attrname).astype(header=self.headers_compraw[2],dtype=np.float64)
                        getattr(self,attrname).astype(header=self.headers_compraw[3],dtype=np.float64)
                        getattr(self,attrname).astype(header=self.headers_compraw[4],datestring=True)
                        getattr(self,attrname).astype(header=self.headers_compraw[5],datestring=True)
                    else:
                        getattr(self,attrname).texttocolumn(0,deliminator="\t",maxsplit=6)
                        getattr(self,attrname).astype(header=self.headers_comp[1],datestring=True)
                        getattr(self,attrname).astype(header=self.headers_comp[3],dtype=np.float64)
                        getattr(self,attrname).astype(header=self.headers_comp[4],dtype=np.float64)

                else:

                    if ending == "uni":
                        getattr(self,attrname).texttocolumn(0,deliminator="\t")
                        getattr(self,attrname).astype(header=self.headers_compuni[1],datestring=True)
                        getattr(self,attrname).astype(header=self.headers_compuni[2],dtype=int)

                self.attrnames.append(attrname)

                if wellname is not None:
                    getattr(self,attrname).filter(0,keywords=[wellname],inplace=False)

class Production():

    headersSIM = ["Wells","Date","Days","oil","water","gas","Wi",]

    headersOPT = ["WELL","DATE","DAYS","OPTYPE","ROIL","RWATER","RGAS","TOIL","TWATER","TGAS",]
    
    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

    def get_wellnames(self):

        pass

    def fill_missing_daily_production(timeO,rateO,timeStart=None,timeEnd=None):

        timeStart = datetime(datetime.today().year,1,1) if timeStart is None else timeStart

        timeEnd = datetime.today() if timeEnd is None else timeEnd

        delta = timeEnd-timeStart

        timeaxis = np.array([timeStart+timedelta(days=i) for i in range(delta.days)],dtype=np.datetime64)

        nonzeroproduction = np.where(timeaxis==timeO.reshape((-1,1)))[1]

        rateEdited = np.zeros(delta.days)

        rateEdited[nonzeroproduction] = rateO

        return rateEdited

    def op_process(self):

        warnDNEOM = "{:%d %b %Y} {} date is not the last day of month."
        warnADGDM = "{:%d %b %Y} {} active days is greater than the days in the month."
        warnOPHNE = "{:%d %b %Y} {} oil production has negative entry."
        warnWPHNE = "{:%d %b %Y} {} water production has negative entry."
        warnGPHNE = "{:%d %b %Y} {} gas production has negative entry."
        warnWIHNE = "{:%d %b %Y} {} water injection has negative entry."
        warnHZPAI = "{:%d %b %Y} {} has zero production and injection."
        warnHBPAI = "{:%d %b %Y} {} has both production and injection data."

        path = os.path.join(self.workdir,self.filename_op+"0")

        prod = frame(filepath=path,skiplines=1)

        prod.texttocolumn(0,deliminator="\t",maxsplit=7)
        prod.get_columns(headers=self.headers_opraw,inplace=True)
        prod.sort(header_indices=[1],inplace=True)

        prod.astype(header=self.headers_opraw[1],datestring=True)
        prod.astype(header=self.headers_opraw[2],dtype=np.int64)
        prod.astype(header=self.headers_opraw[3],dtype=np.float64)
        prod.astype(header=self.headers_opraw[4],dtype=np.float64)
        prod.astype(header=self.headers_opraw[5],dtype=np.float64)
        prod.astype(header=self.headers_opraw[6],dtype=np.float64)

        vdate1 = np.vectorize(lambda x: x.day!=calendar.monthrange(x.year,x.month)[1])

        if any(vdate1(prod.running[1])):
            for index in np.where(vdate1(prod.running[1]))[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnDNEOM.format(date,well))

        vdate2 = np.vectorize(lambda x,y: x.day<y)

        if any(vdate2(prod.running[1],prod.running[2])):
            for index in np.where(vdate2(prod.running[1],prod.running[2]))[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnADGDM.format(date,well))

        if any(prod.running[3]<0):
            for index in np.where(prod.running[3]<0)[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnOPHNE.format(date,well))

        if any(prod.running[4]<0):
            for index in np.where(prod.running[4]<0)[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnWPHNE.format(date,well))

        if any(prod.running[5]<0):
            for index in np.where(prod.running[5]<0)[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnGPHNE.format(date,well))

        if any(prod.running[6]<0):
            for index in np.where(prod.running[6]<0)[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnWIHNE.format(date,well))

        roil = prod.running[3]
        rwater = prod.running[4]+prod.running[6]
        rgas = prod.running[5]

        rprod = prod.running[3]+prod.running[4]+prod.running[5]
        rinj = prod.running[6]

        rtot = rprod+rinj

        optype = np.empty(prod.running[2].shape,dtype=object)

        optype[rprod>0] = "production"
        optype[rinj>0] = "injection"

        if any(rtot==0):
            for index in np.where(rtot==0)[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnHZPAI.format(date,well))

        if any(np.logical_and(rprod!=0,rinj!=0)):
            for index in np.where(np.logical_and(rprod!=0,rinj!=0))[0]:
                well = prod.running[0][index]
                date = prod.running[1][index]
                warnings.warn(warnHBPAI.format(date,well))

        if self.wnamefstr is not None:
            vname = np.vectorize(lambda x: self.wnamefstr.format(re.sub("[^0-9]","",str(x)).zfill(3)))
            prod.set_column(vname(prod.running[0]),header_index=0)

        def shifting(x):
            date = x+relativedelta(months=-1)
            days = calendar.monthrange(date.year,date.month)[1]
            return datetime(date.year,date.month,days)

        vdate3 = np.vectorize(lambda x: shifting(x))

        prod.set_column(vdate3(prod.running[1]),header_index=1)

        path = os.path.join(self.workdir,self.filename_op+"1")

        fstring = "{:6s}\t{:%Y-%m-%d}\t{:2d}\t{:.1f}\t{:.1f}\t{:.1f}\t{:.1f}\n"

        prod.write(filepath=path,fstring=fstring)

        prod.set_column(roil,header_new="ROIL")
        prod.set_column(rwater,header_new="RWATER")
        prod.set_column(rgas,header_new="RGAS")

        prod.set_column(optype,header_new="OPTYPE")

        prod.set_header(0,self.headers_op[0])
        prod.set_header(1,self.headers_op[1])
        prod.set_header(2,self.headers_op[2])

        prod.get_columns(headers=self.headers_op[:7],inplace=True)
        
        path = os.path.join(self.workdir,self.filename_op+"2")

        fstring = "{:6s}\t{:%Y-%m-%d}\t{:2d}\t{:10s}\t{:.1f}\t{:.1f}\t{:.1f}\n"

        prod.write(filepath=path,fstring=fstring)

    def op_get(self,filending=None,wellname=None):

        for filename in os.listdir(self.workdir):

            if filename[:len("operation")]=="operation":

                path = os.path.join(self.workdir,filename)

                ending = filename[len("operation"):]

                if filename[:2]+ending in self.attrnames:
                    continue

                if filending is not None:
                    if filending!=ending:
                        continue

                try:
                    index = int(ending)
                except ValueError:
                    index = None

                attrname = filename[:2]+ending

                attrvals = frame(filepath=path,skiplines=1)

                setattr(self,attrname,attrvals)

                getattr(self,attrname).texttocolumn(0,deliminator="\t")

                if index < 2:
                    getattr(self,attrname).astype(header=self.headers_opraw[1],datestring=True)
                    getattr(self,attrname).astype(header=self.headers_opraw[2],dtype=int)
                    getattr(self,attrname).astype(header=self.headers_opraw[3],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_opraw[4],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_opraw[5],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_opraw[6],dtype=np.float64)         
                elif index < 3:
                    getattr(self,attrname).astype(header=self.headers_op[1],datestring=True)
                    getattr(self,attrname).astype(header=self.headers_op[2],dtype=int)
                    getattr(self,attrname).astype(header=self.headers_op[4],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[5],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[6],dtype=np.float64)
                elif index == 3:
                    getattr(self,attrname).astype(header=self.headers_op[1],datestring=True)
                    getattr(self,attrname).astype(header=self.headers_op[2],dtype=int)
                    getattr(self,attrname).astype(header=self.headers_op[4],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[5],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[6],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[7],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[8],dtype=np.float64)
                    getattr(self,attrname).astype(header=self.headers_op[9],dtype=np.float64)

                self.attrnames.append(attrname)

                if wellname is not None:
                    getattr(self,attrname).filter(0,keywords=[wellname],inplace=False)

class SchedFile(dirmaster):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

    def write(self):

        path = os.path.join(self.workdir,self.schedule_filename)

        with open(path,"w",encoding='utf-8') as wfile:

            welspec = schedule.running[1]=="WELSPECS"
            compdat = schedule.running[1]=="COMPDATMD"
            compord = schedule.running[1]=="COMPORD"
            prodhst = schedule.running[1]=="WCONHIST"
            injdhst = schedule.running[1]=="WCONINJH"
            wefffac = schedule.running[1]=="WEFAC"
            welopen = schedule.running[1]=="WELOPEN"

            for date in numpy.unique(schedule.running[0]):

                currentdate = schedule.running[0]==date

                currentcont = schedule.running[1][currentdate]

                wfile.write("\n\n")
                wfile.write("DATES\n")
                wfile.write(self.schedule_dates.format(date.strftime("%d %b %Y").upper()))
                wfile.write("\n")
                wfile.write("/\n\n")

                if any(currentcont=="WELSPECS"):
                    indices = numpy.logical_and(currentdate,welspec)
                    wfile.write("WELSPECS\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="COMPDATMD"):
                    indices = numpy.logical_and(currentdate,compdat)
                    wfile.write("COMPDATMD\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="COMPORD"):
                    indices = numpy.logical_and(currentdate,compord)
                    wfile.write("COMPORD\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WCONHIST"):
                    indices = numpy.logical_and(currentdate,prodhst)
                    wfile.write("WCONHIST\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WCONINJH"):
                    indices = numpy.logical_and(currentdate,injdhst)
                    wfile.write("WCONINJH\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WEFAC"):
                    indices = numpy.logical_and(currentdate,wefffac)
                    wfile.write("WEFAC\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WELOPEN"):
                    indices = numpy.logical_and(currentdate,welopen)
                    wfile.write("WELOPEN\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

def loadsched():

    pass

class SchedWorm():

    def __init__(self,filepath):

        pass

    def read(self,skiprows=0,headerline=None,comment="--",endline="/",endfile="END"):

        # While looping inside the file it does not read lines:
        # - starting with comment phrase, e.g., comment = "--"
        # - after the end of line phrase, e.g., endline = "/"
        # - after the end of file keyword e.g., endfile = "END"

        if headerline is None:
            headerline = skiprows-1
        elif headerline<skiprows:
            headerline = headerline
        else:
            headerline = skiprows-1

        _running = []

        with open(self.filepath,"r") as text:

            for line in text:

                line = line.split('\n')[0].strip()

                line = line.strip(endline)

                line = line.strip()
                line = line.strip("\t")
                line = line.strip()

                if line=="":
                    continue

                if comment is not None:
                    if line[:len(comment)] == comment:
                        continue

                if endfile is not None:
                    if line[:len(endfile)] == endfile:
                        break

                _running.append([line])

        self.title = []

        for _ in range(skiprows):
            self.title.append(_running.pop(0))

        num_cols = len(_running[0])

        if skiprows==0:
            self.set_headers(num_cols=num_cols,init=False)
        elif skiprows!=0:
            self.set_headers(headers=self.title[headerline],init=False)

        nparray = numpy.array(_running).T

    def catch(self,header_index=None,header=None,regex=None,regex_builtin="INC_HEADERS",title="SUB-HEADERS"):

        nparray = numpy.array(self._running[header_index])

        if regex is None and regex_builtin=="INC_HEADERS":
            regex = r'^[A-Z]+$'                         #for strings with only capital letters no digits
        elif regex is None and regex_builtin=="INC_DATES":
            regex = r'^\d{1,2} [A-Za-z]{3} \d{2}\d{2}?$'   #for strings with [1 or 2 digits][space][3 capital letters][space][2 or 4 digits], e.g. DATES

        vmatch = numpy.vectorize(lambda x: bool(re.compile(regex).match(x)))

        match_index = vmatch(nparray)

        firstocc = numpy.argmax(match_index)

        lower = numpy.where(match_index)[0]
        upper = numpy.append(lower[1:],nparray.size)

        repeat_count = upper-lower-1

        match_content = nparray[match_index]

        nparray[firstocc:][~match_index[firstocc:]] = numpy.repeat(match_content,repeat_count)

        self._headers.insert(header_index,title)
        self._running.insert(header_index,numpy.asarray(nparray))

        for index,datacolumn in enumerate(self._running):
            self._running[index] = numpy.array(self._running[index][firstocc:][~match_index[firstocc:]])

        self.headers = self._headers
        self.running = [numpy.asarray(datacolumn) for datacolumn in self._running]

    def program(self):

        # KEYWORDS: DATES,COMPDATMD,COMPORD,WCONHIST,WCONINJH,WEFAC,WELOPEN 

        dates      = " {} / "#.format(date)
        welspecs   = " '{}'\t1*\t2* / "
        compdatop  = " '{}'\t1*\t{}\t{}\tMD\t{}\t2*\t0.14 / "#.format(wellname,top,bottom,optype)
        compdatsh  = " '{}'\t1*\t{}\t{}\tMD\t{} / "#.format(wellname,top,bottom,optype)
        compord    = " '{}'\tINPUT\t/ "#.format(wellname)
        prodhist   = " '{}'\tOPEN\tORAT\t{}\t{}\t{} / "#.format(wellname,oilrate,waterrate,gasrate)
        injhist    = " '{}'\tWATER\tOPEN\t{}\t7*\tRATE / "#.format(wellname,waterrate)
        wefac      = " '{}'\t{} / "#.format(wellname,efficiency)
        welopen    = " '{}'\tSHUT\t3* / "#.format(wellname)

class TimeView():

    legendpos = (
        "best","right",
        "upper left","upper center","upper right",
        "lower left","lower center","lower right",
        "center left","center","center right",
        )

    drawstyles = (
        'default','steps','steps-pre','steps-mid','steps-post',
        )

    linestyles = (
        ('-',    "solid line"),
        ('--',   "dashed line"),
        ('-.',   "dash dot line"),
        (':',    "dotted line"),
        (None,   "None Line"),
        (' ',    "Empty Space"),
        ('',     "Empty String"),
        )

    markers = (
        (None, "no marker"),
        ('.',  "point marker"),
        (',',  "pixel marker"),
        ('o',  "circle marker"),
        ('v',  "triangle down marker"),
        ('^',  "triangle up marker"),
        ('<',  "triangle left marker"),
        ('>',  "triangle right marker"),
        ('1',  "tri down marker"),
        ('2',  "tri up marker"),
        ('3',  "tri left marker"),
        ('4',  "tri right marker"),
        ('s',  "square marker"),
        ('p',  "pentagon marker"),
        ('*',  "star marker"),
        ('h',  "hexagon1 marker"),
        ('H',  "hexagon2 marker"),
        ('+',  "plus marker"),
        ('x',  "saltire marker"),
        ('D',  "diamond marker"),
        ('d',  "thin diamond marker"),
        ('|',  "vline marker"),
        ('_',  "hline marker"),
        )

    linecolors = (
        ('b', "blue"),
        ('g', "green"),
        ('r', "red"),
        ('c', "cyan"),
        ('m', "magenta"),
        ('y', "yellow"),
        ('k', "black"),
        ('w', "white"),
        )

    template0 = {
        "name": "Standard",
        #
        "subplots": [1,1],
        "title": [""],
        "twinx": [False],
        "xlabel": ["x-axis"],
        "ylabel": ["y-axis"],
        "legends": [True],
        "xticks": [None],
        "yticks": [None],
        "grid": [True],
        #
        "sublines": [[3]],
        "xaxes": [[(0,1),(0,1),(0,1)]],
        "yaxes": [[(0,2),(0,3),(0,4)]],
        "colors": [[6,0,2]],
        "markers": [[0,0,0]],
        "linestyles": [[0,1,0]],
        "drawstyles": [[0,0,0]],
        }

    template1 = {
        "name": "Standard-dual horizontal stack",
        #
        "subplots": [1,2],
        "twinx": [False,False],
        "title": ["Left","Right"],
        "xlabel": ["x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis"],
        "legends": [True,True],
        "xticks": [None,None],
        "yticks": [None,None],
        "grid": [True,True],
        #
        "sublines": [[1],[2]],
        "xaxes": [[(0,1)],[(0,1),(0,1)]],
        "yaxes": [[(0,2)],[(0,3),(0,4)]],
        "colors": [[6],[0,2]],
        "markers": [[0],[0,0]],
        "linestyles": [[0],[0,0]],
        "drawstyles": [[0],[0,0]],
        }

    template2 = {
        "name": "Standard-dual vertical stack",
        #
        "subplots": [2,1],
        "twinx": [False,False],
        "title": ["Top","Bottom"],
        "xlabel": ["x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis"],
        "legends": [True,True],
        "xticks": [None,None],
        "yticks": [None,None],
        "grid": [True,True],
        #
        "sublines": [[1],[2]],
        "xaxes": [[(0,1)],[(0,1),(0,1)]],
        "yaxes": [[(0,2)],[(0,3),(0,4)]],
        "colors": [[6],[0,2]],
        "markers": [[0],[0,0]],
        "linestyles": [[0],[0,0]],
        "drawstyles": [[4],[0,0]],
        }

    template3 = {
        "name": "Standard-quadruple",
        #
        "subplots": [2,2],
        "twinx": [False,False,False,False],
        "title": ["NW","NE","SW","SE"],
        "xlabel": ["x-axis","x-axis","x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis","y-axis","y-axis"],
        "legends": [True,True,True,False],
        "xticks": [None,None,None,None],
        "yticks": [None,None,None,None],
        "grid": [True,True,True,True],
        #
        "sublines": [[1],[1],[1],[0]],
        "xaxes": [[(0,1)],[(0,1)],[(0,1)],[]],
        "yaxes": [[(0,2)],[(0,3)],[(0,4)],[]],
        "colors": [[6],[0],[2],[0]],
        "markers": [[0],[0],[0],[0]],
        "linestyles": [[0],[0],[0],[0]],
        "drawstyles": [[0],[0],[0],[0]],
        }

    templates = (
        template0,template1,template2,template3,
        )

    def __init__(self,window,**kwargs):

        super().__init__(**kwargs)

        self.dirname = os.path.dirname(__file__)

        self.root = window

    def set_plot(self):

        # configuration of window pane
        self.pane_NS = tkinter.ttk.PanedWindow(self.root,orient=tkinter.VERTICAL,width=1000)

        self.frame_body = tkinter.ttk.Frame(self.root,height=450)

        self.pane_NS.add(self.frame_body,weight=1)

        self.footer = tkinter.Listbox(self.root,height=5)

        self.pane_NS.add(self.footer,weight=0)

        self.pane_NS.pack(expand=1,fill=tkinter.BOTH)

        # configuration of top pane
        self.pane_EW = tkinter.ttk.PanedWindow(self.frame_body,orient=tkinter.HORIZONTAL)

        self.frame_side = tkinter.ttk.Frame(self.frame_body)

        self.pane_EW.add(self.frame_side,weight=0)

        self.frame_plot = tkinter.ttk.Frame(self.frame_body)

        self.pane_EW.add(self.frame_plot,weight=1)

        self.pane_EW.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.frame_plot.columnconfigure(0,weight=1)
        self.frame_plot.columnconfigure(1,weight=0)

        self.frame_plot.rowconfigure(0,weight=1)
        self.frame_plot.rowconfigure(1,weight=0)

        self.figure = pyplot.Figure()
        self.canvas = FigureCanvasTkAgg(self.figure,self.frame_plot)

        self.plotbox = self.canvas.get_tk_widget()
        self.plotbox.grid(row=0,column=0,sticky=tkinter.NSEW)        

        self.plotbar = VerticalNavigationToolbar2Tk(self.canvas,self.frame_plot)
        self.plotbar.update()
        self.plotbar.grid(row=0,column=1,sticky=tkinter.N)

        # configuration of top left pane
        self.pane_ns = tkinter.ttk.PanedWindow(self.frame_side,orient=tkinter.VERTICAL,width=300)

        self.itembox = AutocompleteEntryListbox(self.frame_side,height=250,padding=0)

        self.itembox.content = self.itemnames.tolist()
        self.itembox.config(completevalues=self.itembox.content,allow_other_values=True)

        self.itembox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_lines(event))

        self.pane_ns.add(self.itembox,weight=1)

        self.tempbox = tkinter.ttk.Frame(self.frame_side,height=200)

        self.tempbox.rowconfigure(0,weight=0)
        self.tempbox.rowconfigure(1,weight=1)

        self.tempbox.columnconfigure(0,weight=1)
        self.tempbox.columnconfigure(1,weight=0)
        self.tempbox.columnconfigure(2,weight=0)

        self.tempbox.label = tkinter.ttk.Label(self.tempbox,text="Graph Templates")
        self.tempbox.label.grid(row=0,column=0,sticky=tkinter.EW)

        self.tempbox.iconadd = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Add","Add-9.png"))
        self.tempbox.iconedit = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Edit","Edit-9.png"))
        self.tempbox.icondel = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Delete","Delete-9.png"))

        self.tempbox.buttonadd = tkinter.ttk.Button(self.tempbox,image=self.tempbox.iconadd,command=lambda:self.get_template("add"))
        self.tempbox.buttonadd.grid(row=0,column=1)

        self.tempbox.buttonedit = tkinter.ttk.Button(self.tempbox,image=self.tempbox.iconedit,command=lambda:self.get_template("edit"))
        self.tempbox.buttonedit.grid(row=0,column=2)

        self.tempbox.buttondel = tkinter.ttk.Button(self.tempbox,image=self.tempbox.icondel,command=lambda:self.get_template("delete"))
        self.tempbox.buttondel.grid(row=0,column=3)

        self.tempbox.listbox = tkinter.Listbox(self.tempbox,exportselection=False)
        self.tempbox.listbox.grid(row=1,column=0,columnspan=4,sticky=tkinter.NSEW)

        for template in self.templates:
            self.tempbox.listbox.insert(tkinter.END,template.get("name"))

        self.curtemp = {}

        self.tempbox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_axes(event))

        self.pane_ns.add(self.tempbox,weight=1)

        self.pane_ns.pack(expand=1,fill=tkinter.BOTH)

    def set_axes(self,event):

        if not self.tempbox.listbox.curselection():
            return

        if self.curtemp == self.templates[self.tempbox.listbox.curselection()[0]]:
            return
        
        self.curtemp = self.templates[self.tempbox.listbox.curselection()[0]]

        naxrows,naxcols = self.curtemp.get("subplots")

        twinx = self.curtemp.get("twinx")

        self.curtemp["flagMainAxes"] = []

        for flagTwinAxis in twinx:
            self.curtemp["flagMainAxes"].append(True)
            if flagTwinAxis: self.curtemp["flagMainAxes"].append(False)

        if hasattr(self,"axes"):
            self.figure.clear()
            # [self.figure.delaxes(axis) for axis in self.axes]

        self.axes = []

        for index,flagMainAxis in enumerate(self.curtemp.get("flagMainAxes")):

            index_main = sum(self.curtemp.get("flagMainAxes")[:index+1])-1

            if flagMainAxis:
                axis = self.figure.add_subplot(naxrows,naxcols,index_main+1)
            else:
                axis = self.axes[-1].twinx()
                
            if flagMainAxis and self.curtemp.get("title")[index_main] is not None:
                axis.set_title(self.curtemp.get("title")[index_main])

            if flagMainAxis and self.curtemp.get("xlabel")[index_main] is not None:
                axis.set_xlabel(self.curtemp.get("xlabel")[index_main])

            if self.curtemp.get("ylabel")[index] is not None:
                axis.set_ylabel(self.curtemp.get("ylabel")[index])

            if flagMainAxis and self.curtemp.get("xticks")[index_main] is not None:
                axis.set_xticks(self.curtemp.get("xticks")[index_main])

            if self.curtemp.get("yticks")[index] is not None:
                axis.set_yticks(self.curtemp.get("yticks")[index])

            if flagMainAxis and self.curtemp.get("grid")[index_main] is not None:
                axis.grid(self.curtemp.get("grid")[index_main])

            self.axes.append(axis)

            # for tick in axis0.get_xticklabels():
            #     tick.set_rotation(45)

        status = "{} template has been selected.".format(self.curtemp.get("name"))

        self.footer.insert(tkinter.END,status)
        self.footer.see(tkinter.END)

        self.figure.set_tight_layout(True)

        self.canvas.draw()

    def set_lines(self,event):

        if self.itembox.listbox.curselection():
            itemname = self.itemnames[self.itembox.listbox.curselection()[0]]
        else:
            return

        if not hasattr(self,"axes"):
            status = "No template has been selected."
            self.footer.insert(tkinter.END,status)
            self.footer.see(tkinter.END)
            return

        for attrname in self.attrnames:
            if hasattr(self,attrname):
                getattr(self,attrname).filter(0,keywords=[itemname],inplace=False)

        if hasattr(self,"lines"):
            [line.remove() for line in self.lines]
                
        self.lines = []

        self.plotbar.update()

        for index,axis in enumerate(self.axes):

            xaxes = self.curtemp.get("xaxes")[index]
            yaxes = self.curtemp.get("yaxes")[index]

            colors = self.curtemp.get("colors")[index]
            markers = self.curtemp.get("markers")[index]
            lstyles = self.curtemp.get("linestyles")[index]
            dstyles = self.curtemp.get("drawstyles")[index]

            for xaxis,yaxis,color,marker,lstyle,dstyle in zip(xaxes,yaxes,colors,markers,lstyles,dstyles):
                line = axis.plot(
                    getattr(self,self.attrnames[xaxis[0]]).running[xaxis[1]],
                    getattr(self,self.attrnames[yaxis[0]]).running[yaxis[1]],
                    color=self.linecolors[color][0],
                    marker=self.markers[marker][0],
                    linestyle=self.linestyles[lstyle][0],
                    drawstyle=self.drawstyles[dstyle],
                    label=getattr(self,self.attrnames[yaxis[0]]).headers[yaxis[1]])[0]
                self.lines.append(line)

            # if self.curtemp.get("legends")[index]:
            #     axis.legend()

            axis.relim()
            axis.autoscale()
            axis.set_ylim(bottom=0,top=None,auto=True)

        self.figure.set_tight_layout(True)

        self.canvas.draw()

    def get_template(self,manipulation):

        if manipulation=="add":

            self.curtemp = {# when creating a template
                "name": "",
                "subplots": [1,1],
                "title": [""],
                "twinx": [False],
                "xlabel": [""],
                "ylabel": [""],
                "legends": [False],
                "xticks": [None],
                "yticks": [None],
                "grid": [False],
                #
                "sublines": [[0]],
                "xaxes": [[]],
                "yaxes": [[]],
                "colors": [[]],
                "markers": [[]],
                "linestyles": [[]],
                "drawstyles": [[]],
                }

            self.set_temptop("add") # when adding a new one

        elif manipulation=="edit":

            if not self.tempbox.listbox.curselection(): return # when editing

            self.curtemp = self.templates[self.tempbox.listbox.curselection()[0]] # when editing
            self.set_temptop(tempid=self.tempbox.listbox.curselection()[0]) # editing the existing one
            
        elif manipulation=="delete":
            # deleting a template

            if not self.tempbox.listbox.curselection(): return

            name = self.tempbox.listbox.get(self.tempbox.listbox.curselection())

            item = self.curtemp.get("name").index(name)
            
            self.tempbox.listbox.delete(item)

            self.curtemp.get("name").pop(item)
            # self.curtemp.get("naxrows").pop(item)
            # self.curtemp.get("naxcols").pop(item)

    def set_temptop(self,manipulation,tempid=None):

        if hasattr(self,"temptop"):
            if self.temptop.winfo_exists(): return

        if tempid is not None:
            curtemp = self.templates[tempid]
        else:
            curtemp = {"subplots": [1,1]}
            curtemp["sublines"] = [[1,0]]

        self.temptop = tkinter.Toplevel()

        self.temptop.title("Template Editor")

        self.temptop.geometry("700x450")

        self.temptop.resizable(0,0)

        self.style = tkinter.ttk.Style(self.temptop)

        self.style.configure("TNotebook.Tab",width=15,anchor=tkinter.CENTER)

        self.tempedit = tkinter.ttk.Notebook(self.temptop)

        # General Properties

        self.tempeditgeneral = tkinter.Frame(self.tempedit)

        self.tempeditgeneral0 = tkinter.Frame(self.tempeditgeneral,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditgeneral0.templabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Settings")
        self.tempeditgeneral0.templabel.grid(row=0,column=0,columnspan=2,sticky=tkinter.W,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.tempnamelabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Template Name")
        self.tempeditgeneral0.tempnamelabel.grid(row=1,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.tempname = tkinter.ttk.Entry(self.tempeditgeneral0,width=30)
        self.tempeditgeneral0.tempname.grid(row=1,column=1,padx=(0,20),pady=(2,2),sticky=tkinter.EW)

        self.tempeditgeneral0.tempname.focus()

        self.tempeditgeneral0.legendLabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Legend Position")
        self.tempeditgeneral0.legendLabel.grid(row=2,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.legend = tkinter.ttk.Entry(self.tempeditgeneral0,width=30)
        self.tempeditgeneral0.legend.grid(row=2,column=1,padx=(0,20),pady=(2,2),sticky=tkinter.EW)

        self.tempeditgeneral0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditgeneral1 = tkinter.Frame(self.tempeditgeneral,borderwidth=2)

        self.tempeditgeneral1.naxlabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Number of Axes")
        self.tempeditgeneral1.naxlabel.grid(row=0,column=0,columnspan=2,sticky=tkinter.EW,padx=(10,2),pady=(2,2))

        self.tempeditgeneral1.naxrowslabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Rows")
        self.tempeditgeneral1.naxrowslabel.grid(row=1,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral1.naxval0 = tkinter.StringVar(self.root)
        self.tempeditgeneral1.naxrows = tkinter.ttk.Spinbox(self.tempeditgeneral1,textvariable=self.tempeditgeneral1.naxval0,from_=1,to=5,command=lambda:self.set_temptopdict("rows"))
        self.tempeditgeneral1.naxrows.grid(row=1,column=1,sticky=tkinter.EW,padx=(0,2),pady=(2,2))

        self.tempeditgeneral1.naxcolslabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Columns")
        self.tempeditgeneral1.naxcolslabel.grid(row=2,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral1.naxval1 = tkinter.StringVar(self.root)
        self.tempeditgeneral1.naxcols = tkinter.ttk.Spinbox(self.tempeditgeneral1,textvariable=self.tempeditgeneral1.naxval1,from_=1,to=5,command=lambda:self.set_temptopdict("columns"))
        self.tempeditgeneral1.naxcols.grid(row=2,column=1,sticky=tkinter.EW,padx=(0,2),pady=(2,2))

        self.tempeditgeneral1.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)
        
        self.tempedit.add(self.tempeditgeneral,text="General",compound=tkinter.CENTER)

        # Axes Properties

        self.tempeditaxes = tkinter.Frame(self.tempedit)

        self.tempeditaxes0 = tkinter.Frame(self.tempeditaxes,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditaxes0.axislabel = tkinter.ttk.Label(self.tempeditaxes0,text="Axis List")
        self.tempeditaxes0.axislabel.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditaxes0.listbox = tkinter.Listbox(self.tempeditaxes0)

        self.tempeditaxes0.listbox.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditaxes0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditaxes1 = tkinter.Frame(self.tempeditaxes,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditaxes1.entry00 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check00 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Draw X Twin",variable=self.tempeditaxes1.entry00,command=lambda:self.set_temptopdict("entry00"))
        self.tempeditaxes1.check00.grid(row=0,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.label01 = tkinter.ttk.Label(self.tempeditaxes1,text="Title")
        self.tempeditaxes1.label01.grid(row=1,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry01 = tkinter.ttk.Entry(self.tempeditaxes1)
        self.tempeditaxes1.entry01.grid(row=1,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label02 = tkinter.ttk.Label(self.tempeditaxes1,text="X Label")
        self.tempeditaxes1.label02.grid(row=2,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry02 = tkinter.ttk.Entry(self.tempeditaxes1)
        self.tempeditaxes1.entry02.grid(row=2,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label03 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-1 Label")
        self.tempeditaxes1.label03.grid(row=3,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry03 = tkinter.ttk.Entry(self.tempeditaxes1,state=tkinter.NORMAL)
        self.tempeditaxes1.entry03.grid(row=3,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label04 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-2 Label",state=tkinter.DISABLED)
        self.tempeditaxes1.label04.grid(row=4,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry04 = tkinter.ttk.Entry(self.tempeditaxes1,state=tkinter.DISABLED)
        self.tempeditaxes1.entry04.grid(row=4,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry05 = tkinter.StringVar(self.root)
        self.tempeditaxes1.label05 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-1 Lines")
        self.tempeditaxes1.label05.grid(row=5,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.spinb05 = tkinter.ttk.Spinbox(self.tempeditaxes1,to=20,textvariable=self.tempeditaxes1.entry05,command=lambda:self.set_temptopdict("entry05"))
        self.tempeditaxes1.spinb05.grid(row=5,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry06 = tkinter.StringVar(self.root)
        self.tempeditaxes1.label06 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-2 Lines",state=tkinter.DISABLED)
        self.tempeditaxes1.label06.grid(row=6,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.spinb06 = tkinter.ttk.Spinbox(self.tempeditaxes1,to=20,textvariable=self.tempeditaxes1.entry06,command=lambda:self.set_temptopdict("entry06"),state=tkinter.DISABLED)
        self.tempeditaxes1.spinb06.grid(row=6,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry07 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check07 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Legends",variable=self.tempeditaxes1.entry07)
        self.tempeditaxes1.check07.grid(row=7,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry08 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check08 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show X Ticks",variable=self.tempeditaxes1.entry08)
        self.tempeditaxes1.check08.grid(row=8,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry09 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check09 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Y-1 Ticks",variable=self.tempeditaxes1.entry09)
        self.tempeditaxes1.check09.grid(row=9,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry10 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check10 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Y-2 Ticks",variable=self.tempeditaxes1.entry10,state=tkinter.DISABLED)
        self.tempeditaxes1.check10.grid(row=10,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry11 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check11 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Grids",variable=self.tempeditaxes1.entry11)
        self.tempeditaxes1.check11.grid(row=11,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.tempedit.add(self.tempeditaxes,text="Axes",compound=tkinter.CENTER)

        # Line Properties

        self.tempeditlines = tkinter.Frame(self.tempedit)

        self.tempeditlines0 = tkinter.Frame(self.tempeditlines,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditlines0.axislabel = tkinter.ttk.Label(self.tempeditlines0,text="Axis List")
        self.tempeditlines0.axislabel.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines0.listbox = tkinter.Listbox(self.tempeditlines0)

        self.tempeditlines0.listbox.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditlines1 = tkinter.Frame(self.tempeditlines,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditlines1.line1label = tkinter.ttk.Label(self.tempeditlines1,text="Y-1 Lines")
        self.tempeditlines1.line1label.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines1.listbox1 = tkinter.Listbox(self.tempeditlines1)

        self.tempeditlines1.listbox1.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines1.line2label = tkinter.ttk.Label(self.tempeditlines1,text="Y-2 Lines")
        self.tempeditlines1.line2label.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines1.listbox2 = tkinter.Listbox(self.tempeditlines1)

        self.tempeditlines1.listbox2.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines1.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditlines2 = tkinter.Frame(self.tempeditlines)

        self.tempeditlines2.label = tkinter.ttk.Label(self.tempeditlines2,text="Line Details")
        self.tempeditlines2.label.grid(row=0,column=0,columnspan=2,sticky=tkinter.W,padx=(10,),pady=(4,))

        self.tempeditlines2.label0 = tkinter.ttk.Label(self.tempeditlines2,text="X-axis")
        self.tempeditlines2.label0.grid(row=1,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label1 = tkinter.ttk.Label(self.tempeditlines2,text="Y-axis")
        self.tempeditlines2.label1.grid(row=2,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label2 = tkinter.ttk.Label(self.tempeditlines2,text="Draw Style")
        self.tempeditlines2.label2.grid(row=3,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label3 = tkinter.ttk.Label(self.tempeditlines2,text="Line Style")
        self.tempeditlines2.label3.grid(row=4,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label4 = tkinter.ttk.Label(self.tempeditlines2,text="Line Color")
        self.tempeditlines2.label4.grid(row=5,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.val0 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val1 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val2 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val3 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val4 = tkinter.StringVar(self.tempeditlines2)

        self.tempeditlines2.menu0 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val0,"Select Attribute",*self.attrnames)
        self.tempeditlines2.menu0.grid(row=1,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu1 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val1,"Select Attribute",*self.attrnames)
        self.tempeditlines2.menu1.grid(row=2,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu2 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val2,"Select Style",*self.drawstyles)
        self.tempeditlines2.menu2.grid(row=3,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu3 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val3,"Select Style",*self.linestyles)
        self.tempeditlines2.menu3.grid(row=4,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu4 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val4,"Select Color",*self.linecolors)
        self.tempeditlines2.menu4.grid(row=5,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.tempedit.add(self.tempeditlines,text="Lines",compound=tkinter.CENTER)

        self.tempedit.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH,padx=(0,1))

        buttonname = "Add Template" if tempid is None else "Edit Template"

        self.temptop.button = tkinter.ttk.Button(self.temptop,text=buttonname,width=20,command=lambda: self.temptopapply(tempid))
        self.temptop.button.pack(side=tkinter.TOP,expand=1,anchor=tkinter.E,padx=(0,1),pady=(1,1))

        self.temptop.button.bind('<Return>',lambda event: self.temptopapply(tempid,event))

        self.temptop.mainloop()

    def set_temptopdict(self):
        pass
        # self.tempeditgeneral0.tempname.insert(0,curtemp.get("name"))
        # naxrows,naxcols = self.curtemp.get("subplots")

        # self.tempeditgeneral1.naxrows.insert(0,naxrows)
        # self.tempeditgeneral1.naxcols.insert(0,naxcols)

        # for index in range(naxrows*naxcols):
        #     self.tempeditaxes0.listbox.insert(tkinter.END,"Axis {}".format(index))
        #     self.tempeditlines0.listbox.insert(tkinter.END,"Axis {}".format(index))

        # self.tempeditaxes1.entry00.set(self.curtemp.get("twinx")[0])
        # self.tempeditaxes1.entry01.set(self.curtemp.get("title")[0])
        # self.tempeditaxes1.enrty02.set(self.curtemp.get("xlabel")[0])
        # self.tempeditaxes1.enrty03.set(self.curtemp.get("ylabel")[0])
        # self.tempeditaxes1.enrty04.set(self.curtemp.get("ylabel")[1])
        # self.tempeditaxes1.entry05.set(self.curtemp.get("sublines")[0])
        # self.tempeditaxes1.entry06.set(self.curtemp.get("sublines")[1])
        # self.tempeditaxes1.entry07.set(self.curtemp.get("legends")[0])
        # self.tempeditaxes1.entry08.set(self.curtemp.get("xticks")[0])
        # self.tempeditaxes1.entry09.set(self.curtemp.get("yticks")[0])
        # self.tempeditaxes1.entry10.set(self.curtemp.get("yticks")[1])
        # self.tempeditaxes1.entry11.set(self.curtemp.get("grids")[0])

        # for index in range(curtemp.get("sublines")[0][0]):
        #     self.tempeditlines1.listbox1.insert(tkinter.END,"Line {}".format(index))

        # for index in range(curtemp.get("sublines")[0][1]):
        #     self.tempeditlines1.listbox2.insert(tkinter.END,"Line {}".format(index))

        # self.tempeditlines2.val0.set(self.headers[self.curtemp.get("xaxes")[0][0]])
        # self.tempeditlines2.val1.set(self.headers[self.curtemp.get("yaxes")[0][0]])
        # self.tempeditlines2.val2.set(self.drawstyles[self.curtemp.get("drawstyles")[0][0]])
        # self.tempeditlines2.val3.set(self.linestyles[self.curtemp.get("linestyles")[0][0]])
        # self.tempeditlines2.val4.set(self.linecolors[self.curtemp.get("linecolors")[0][0]])

    def set_temptopedits(self,input_):

        if input_=="rows" or input_=="columns":
            numx = self.tempeditgeneral1.naxval0.get()
            numy = self.tempeditgeneral1.naxval1.get()
            numx = int(numx) if numx else 1
            numy = int(numy) if numy else 1
            numa = numx*numy
            if numa>len(self.tempeditaxes0.listbox.get(0,tkinter.END)):
                self.tempeditaxes0.listbox.insert(tkinter.END,"Axis {}".format(numa))
                self.tempeditlines0.listbox.insert(tkinter.END,"Axis {}".format(numa))
        elif input_=="entry00":
            if self.tempeditaxes1.entry00.get():
                self.tempeditaxes1.label04.config(state=tkinter.NORMAL)
                self.tempeditaxes1.entry04.config(state=tkinter.NORMAL)
                self.tempeditaxes1.label06.config(state=tkinter.NORMAL)
                self.tempeditaxes1.spinb06.config(state=tkinter.NORMAL)
                self.tempeditaxes1.check10.config(state=tkinter.NORMAL)
            else:
                self.tempeditaxes1.label04.config(state=tkinter.DISABLED)
                self.tempeditaxes1.entry04.config(state=tkinter.DISABLED)
                self.tempeditaxes1.label06.config(state=tkinter.DISABLED)
                self.tempeditaxes1.spinb06.config(state=tkinter.DISABLED)
                self.tempeditaxes1.check10.config(state=tkinter.DISABLED)
        elif input_=="entry05":
            num1 = int(self.tempeditaxes1.entry05.get())
            if num1>len(self.tempeditlines1.listbox1.get(0,tkinter.END)):
                self.tempeditlines1.listbox1.insert(tkinter.END,"Line {}".format(num1))
        elif input_=="entry06":
            num2 = int(self.tempeditaxes1.entry06.get())
            if num2>len(self.tempeditlines1.listbox2.get(0,tkinter.END)):
                self.tempeditlines1.listbox2.insert(tkinter.END,"Line {}".format(num2))

        # if x.isdigit() or x=="":
        #     # print(prop)
        #     return True
        # else:
        #     return False

    def set_template(self,tempid=None,event=None):

        if event is not None and event.widget!=self.temptop.button:
            return

        if tempid is not None:
            names = [name for index,name in enumerate(self.curtemp.get("name")) if index!=tempid]
        else:
            names = self.curtemp.get("name")

        name = self.tempeditgeneral0.tempname.get()

        if name in names:
            tkinter.messagebox.showerror("Error","You have a template with the same name!",parent=self.temptop)
            return
        elif name.strip()=="":
            tkinter.messagebox.showerror("Error","You have not named the template!",parent=self.temptop)
            return

        if tempid is None:
            tempid = len(self.temps.get("names"))
        else:
            self.tempbox.listbox.delete(tempid)
            self.curtemp.get("name").pop(tempid)
            # self.curtemp.get("naxrows").pop(tempid)
            # self.curtemp.get("naxcols").pop(tempid)
        
        self.tempbox.listbox.insert(tempid,name)

        self.curtemp.get("name").insert(tempid,name)

        try:
            naxrows = int(self.tempeditgeneral1.naxrows.get())
        except ValueError:
            naxrows = 1

        # self.curtemp.get("naxrows").insert(tempid,naxrows)

        try:
            naxcols = int(self.tempeditgeneral1.naxcols.get())
        except ValueError:
            naxcols = 1

        # self.curtemp.get("naxcols").insert(tempid,naxcols)

        self.temptop.destroy()

class WorkFlow():
    """
    1. for resolving time conflicts between production and completion
    2. production allocation
    3. quick well test analysis
    """

    def __init__(self):

        pass

# DATA INTERPRETATION

class allocate():

    def __init__(self):

        pass

class buildup():

    def __init__(self):

        pass

class drawdown():

    def __init__(self):

        pass

if __name__ == "__main__":

    # import unittest

    # from tests.wellbore import schedfile

    # unittest.main(schedfile)

    print(library["status"]["prospect"])

    for key,value in library["status"].items():
        print(f"{key}-{value['abbreviation']}")

    # import unittest

    # from tests import pipes
    # from tests import formations
    # from tests import fractures
    # from tests import wells

    # unittest.main(pipes)
    # unittest.main(formations)
    # unittest.main(fractures)
    # unittest.main(wells)

    """
    For numpy.datetime64, the issue with following deltatime units
    has been solved by considering self.vals:

    Y: year,
    M: month,
    
    For numpy.datetime64, following deltatime units
    have no inherent issue:

    W: week,
    D: day,
    h: hour,
    m: minute,
    s: second,
    
    For numpy.datetime64, also include:

    ms: millisecond,
    us: microsecond,
    ns: nanosecond,

    For numpy.datetime64, do not include:

    ps: picosecond,
    fs: femtosecond,
    as: attosecond,
    """