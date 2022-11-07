import numpy

class slot():

    def __init__(self):

        pass

class trajectory():

    def __init__(self,headers=["X","Y","Z","MD"],**kwargs):

        super().__init__(headers=headers,**kwargs)

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

    def get_track(self,wellname=None):

        pass

class completion():

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

class production():

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

class formtop():

    def __init__(self):

        pass

class stock():

    itemnames = []                 # well names
    statuses = []
    radii = []
    flowconds = []

    def __init__(self,number=0,wnamefstr=None,**kwargs):

        super().__init__(**kwargs)

        self.number = number                # number of wells

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

if __name__ == "__main__":

    pass

    # import unittest

    # from tests import pipes
    # from tests import formations
    # from tests import fractures
    # from tests import wells

    # unittest.main(pipes)
    # unittest.main(formations)
    # unittest.main(fractures)
    # unittest.main(wells)
