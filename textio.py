import contextlib
import copy
import datetime

from difflib import SequenceMatcher

import logging

import os
import re

import numpy
import openpyxl

if __name__ == "__main__":
    import setup

from core import column
from core import DataFrame
from core import any2column
from core import key2column

from cypy.vectorpy import str0type

# A File Front Information

class header():
    """It is a table of parameters, columns are fields."""

    def __init__(self,oneLineHeader=False,**kwargs):
        """parameters should be predefined, all entries must be string."""

        if len(kwargs)==0:
            raise ValueError("At least one field is required.")

        super().__setattr__("parameters",[param for param in kwargs.keys()])

        if oneLineHeader:
            fields = [str(field) for field in kwargs.values()]

        else:

            fields = []

            for field in kwargs.values():

                if isinstance(field,list) or isinstance(field,tuple):
                    field = [str(data) for data in field]
                else:
                    field = [str(field)]

                fields.append(field)

            sizes = [len(field) for field in fields]

            if len(set(sizes))!=1:
                raise ValueError("The lengths of field are not equal!")

        for parameter,field in zip(kwargs.keys(),fields):
            super().__setattr__(parameter,field)

    def extend(self,row):

        if len(self.parameters)!=len(row):
            raise ValueError("The lengths of 'fields' and 'row' are not equal!")

        if isinstance(row,list) or isinstance(row,tuple):
            toextend = header(**dict(zip(self.parameters,row)))
        elif isinstance(row,dict):
            toextend = header(**row)
        elif isinstance(row,header):
            toextend = row

        for parameter,field in toextend.items():
            getattr(self,parameter).extend(field)

    def __setattr__(self,key,vals):

        raise AttributeError(f"'Header' object has no attribute '{key}'.")

    def __getitem__(self,key):

        if not isinstance(key,str):
            raise TypeError("key must be string!")

        for row in self:
            if row[0].lower()==key.lower():
                break
        
        return header(oneLineHeader=True,**dict(zip(self.parameters,row)))

    def __repr__(self):

        if len(self)==1:
            return repr(tuple(self.fields))

        fstring = ""
        
        underline = []

        for parameter,field in zip(self.parameters,self.fields):

            field_ = list(field)
            field_.append(parameter)

            count_ = max([len(value) for value in field_])

            fstring += f"{{:<{count_}}}   "
            
            underline.append("-"*count_)

        fstring += "\n"

        text = fstring.format(*[parm.capitalize() for parm in self.parameters])
        
        text += fstring.format(*underline)
        
        for row in self:
            text += fstring.format(*row)

        return text

    def __iter__(self):

        return iter([row for row in zip(*self.fields)])

    def __len__(self):

        if isinstance(self.fields[0],str):
            return 1
        else:
            return len(self.fields[0])

    def items(self):

        return iter([(p,f) for p,f in zip(self.parameters,self.fields)])

    @property
    def fields(self):

        return [getattr(self,parm) for parm in self.parameters]

# A File Creating Classes

class regtxt():

    def __init__(self,frame):

        self.frame = frame

    def write(self,filepath,fstring=None,**kwargs):
        """It writes text form of DataFrame."""

        header_fstring = ("{}\t"*len(self._headers))[:-1]+"\n"

        if fstring is None:
            running_fstring = ("{}\t"*len(self._headers))[:-1]+"\n"
        else:
            running_fstring = fstring

        vprint = numpy.vectorize(lambda *args: running_fstring.format(*args))

        with open(filepath,"w",encoding='utf-8') as wfile:
            wfile.write(header_fstring.format(*self._headers))
            for line in vprint(*self._running):
                wfile.write(line)

    def writeb(self,filename):
        """It writes binary form of DataFrame."""

        filepath = self.get_abspath(f"{filename}.npz",homeFlag=True)

        for header,column_ in zip(self._headers,self._running):
            kwargs[header] = column_

        numpy.savez_compressed(filepath,**kwargs)

    def _not_merged_to_dataframe_yet_read_writeb(self):

        A = numpy.random.randint(0,1000,1_000_000)
        B = numpy.random.randint(0,1000,1_000_000)
        C = numpy.random.randint(0,1000,1_000_000)

        ##A = numpy.random.rand(1_000_000)
        ##B = numpy.random.rand(1_000_000)
        ##C = numpy.random.rand(1_000_000)

        ## WRITING TEXT FILE

        Z = numpy.empty((A.size,3))
        Z[:,0] = A
        Z[:,1] = B
        Z[:,2] = C
        numpy.savetxt("data.txt",Z.astype(int),fmt="%i",header="a b c")

        ## WRITING BINARY NPZ FILE
        numpy.savez_compressed('data.npz', a=A, b=B, c=C)


        ## READING TEXT FILE
        T = numpy.loadtxt("data.txt",dtype=int)

        ## READING BINARY NPZ FILE
        B = numpy.load('data.npz')

        for key in B.keys():
            print(key)

class ulas():

    def __init__(self,frame):

        self.frame = frame

    def _version(self):

        pass

    def _well(self):

        pass

    def _parameter(self):

        pass

    def _data(self):

        pass

    def write(self,filepath,mnemonics,data,units=None,descriptions=None,values=None):

        import lasio

        """
        filepath:       It will write a lasio.LASFile to the given filepath

        kwargs:         These are mnemonics, data, units, descriptions, values
        """

        lasmaster = lasio.LASFile()

        lasmaster.well.DATE = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        depthExistFlag = False

        for mnemonic in mnemonics:
            if mnemonic=="MD" or mnemonic=="DEPT" or mnemonic=="DEPTH":
                depthExistFlag = True
                break

        if not depthExistFlag:
            curve = lasio.CurveItem(
                mnemonic="DEPT",
                unit="",
                value="",
                descr="Depth index",
                data=numpy.arange(data[0].size))
            lasmaster.append_curve_item(curve)            

        for index,(mnemonic,datum) in enumerate(zip(mnemonics,data)):

            if units is not None:
                unit = units[index]
            else:
                unit = ""

            if descriptions is not None:
                description = descriptions[index]
            else:
                description = ""

            if values is not None:
                value = values[index]
            else:
                value = ""

            curve = lasio.CurveItem(mnemonic=mnemonic,data=datum,unit=unit,descr=description,value=value)

            lasmaster.append_curve_item(curve)

        with open(filepath, mode='w') as filePathToWrite:
            lasmaster.write(filePathToWrite)

class wellsched():

    def __init__(self,frame):

        self.frame = frame

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

class xlbook():

    def __init__(self,frame):

        self.frame = frame

    def write(self,filepath,title):

        wb = openpyxl.Workbook()

        sheet = wb.active

        if title is not None:
            sheet.title = title

        for line in running:
            sheet.append(line)

        wb.save(filepath)

# Directory Management

class dirmaster():
    """Base directory class to manage files in the input & output directories."""

    def __init__(self,homedir=None,filedir=None,filepath=None):
        """Initializes base directory class with home & file directories."""

        self.set_homedir(homedir)
        self.set_filedir(filedir)

        self.set_filepath(filepath)

    def set_homedir(self,path=None):
        """Sets the home directory to put outputs."""

        if path is None:
            path = os.getcwd()

        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(os.getcwd(),path))

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        super().__setattr__("homedir",path)

    def set_filedir(self,path=None):
        """Sets the file directory to get inputs."""

        if path is None:
            path = self.homedir

        if not os.path.isabs(path):
            path = self.get_abspath(path,homeFlag=True)

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        super().__setattr__("filedir",path)

    def set_filepath(self,path=None):
        """Sets the file path for the cases when it is working on a single file."""

        if path is None:
            return

        if os.path.isabs(path):
            self.set_filedir(path)
        else:
            path = self.get_abspath(path)

        if os.path.isdir(path):
            return

        super().__setattr__("filepath",path)

    def get_abspath(self,path,homeFlag=False):
        """Returns absolute path for a given relative path."""

        if os.path.isabs(path):
            return path
        elif homeFlag:
            return os.path.normpath(os.path.join(self.homedir,path))
        else:
            return os.path.normpath(os.path.join(self.filedir,path))

    def file_exists(self,path,homeFlag=False):

        path = self.get_abspath(path,homeFlag=homeFlag)

        return os.path.exists(path)

    def get_dirpath(self,path,homeFlag=False):
        """Returns absolute directory path for a given relative path."""

        path = self.get_abspath(path,homeFlag=homeFlag)

        if os.path.isdir(path):
            return path
        else:
            return os.path.dirname(path)

    def get_fnames(self,path=None,homeFlag=False,prefix=None,extension=None,returnAbsFlag=False,returnDirsFlag=False):
        """Return directory(folder)/file names for a given relative path."""

        if path is None:
            path = self.filedir if homeFlag is False else self.homedir
        else:
            path = self.get_dirpath(path,homeFlag=homeFlag)

        fnames = os.listdir(path)

        fpaths = [self.get_abspath(fname,homeFlag=homeFlag) for fname in fnames]

        if returnDirsFlag:

            foldernames = [fname for (fname,fpath) in zip(fnames,fpaths) if os.path.isdir(fpath)]
            folderpaths = [fpath for fpath in fpaths if os.path.isdir(fpath)]

            if prefix is None:
                if returnAbsFlag:
                    return folderpaths
                else:
                    return foldernames
            else:
                if returnAbsFlag:
                    return [folderpath for (folderpath,foldername) in zip(folderpaths,foldernames) if foldername.startswith(prefix)]
                else:
                    return [foldername for foldername in foldernames if foldername.startswith(prefix)]
        else:

            filenames = [fname for (fname,fpath) in zip(fnames,fpaths) if not os.path.isdir(fpath)]
            filepaths = [fpath for fpath in fpaths if not os.path.isdir(fpath)]

            if prefix is None and extension is None:
                if returnAbsFlag:
                    return filepaths
                else:
                    return filenames
            elif prefix is None and extension is not None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.endswith(extension)]
            elif prefix is not None and extension is None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix)]
            else:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix) and filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix) and filename.endswith(extension)]

    @property
    def basename(self):
        return os.path.basename(self.filepath)

    @property
    def rootname(self):
        return os.path.splitext(self.basename)[0]

    @property
    def extension(self):
        return os.path.splitext(self.filepath)[1]

# A File Input Function & Assistsing Classes

def loadtxt(filepath,**kwargs):

    return _loadtxt(filepath,**kwargs)

def loadlas(filepath,**kwargs):

    return _loadlas(filepath,**kwargs)

def loadsched(filepath,**kwargs):

    return _loadsched(filepath,**kwargs)

def loadxlbook(filepath,**kwargs):

    return _loadxlbook(filepath,**kwargs)

class _loadtxt(dirmaster):

    def __init__(self,filepath,homedir=None,filedir=None,headline=None,comments="#",delimiter=None,skiprows=0):

        self.headline   = headline
        self.comments   = comments
        self.delimiter  = delimiter
        self.skiprows   = skiprows

        super().__init__(homedir,filedir)
        
        with loadtxt.textopen(filepath) as filemaster:
            frame = self.text(filemaster)

        self.frame = frame

    def seekrow(self,filemaster,row):

        filemaster.seek(0)

        countrows = 0

        while True:

            if countrows >= row:
                break

            next(filemaster)

            countrows += 1

    def heads(self,filemaster):

        if self.headline is None:
            return key2column(size=self.numcols,dtype='str').vals

        self.seekrow(filemaster,self.headline)

        line = next(filemaster).strip()

        if self.delimiter is None:
            heads_ = re.sub(r"\s+"," ",line).split(" ")
        else:
            heads_ = line.split(self.delimiter)

        return heads_

    def types(self,filemaster):

        self.seekrow(filemaster,self.skiprows)

        while True:

            line = next(filemaster).strip()

            if len(line)<1:
                continue
            
            if line.startswith(self.comments):
                continue

            break

        if self.delimiter is None:
            row = re.sub(r"\s+"," ",line).split(" ")
        else:
            row = line.split(self.delimiter)

        types_ = [str0type(value) for value in row]

        return types_

    def text(self,filemaster):

        types = self.types(filemaster)

        if self.headline is None:
            self.numcols = len(types)

        dtypes = [numpy.dtype(type_) for type_ in types]

        floatFlags = [True if type_ is float else False for type_ in types]

        self.seekrow(filemaster,self.skiprows)

        if all(floatFlags):
            cols = numpy.loadtxt(filemaster,comments=self.comments,delimiter=self.delimiter,unpack=True)
        else:
            cols = numpy.loadtxt(filemaster,comments=self.comments,delimiter=self.delimiter,unpack=True,dtype=str)

        heads = self.heads(filemaster)

        running = [column(col,head=head,dtype=dtype) for col,head,dtype in zip(cols,heads,dtypes)]

        return DataFrame(*running)

    @contextlib.contextmanager
    def textopen(filepath):

        if hasattr(filepath,'read'):
            yield filepath
        else:
            self.set_filepath(filepath)
            filemaster = open(self.filepath,"r")
            try:
                yield filemaster
            finally:
                filemaster.close()

class _loadlas(dirmaster):

    def __init__(self,filepath,homedir=None,filedir=None,**kwargs):

        super().__init__(homedir,filedir,filepath=filepath)

        self.sections = []

        with open(self.filepath,"r",encoding="latin1") as lasmaster:
            frame = self.text(lasmaster)

        self.frame = frame

    def seeksection(self,lasmaster,section=None):

        lasmaster.seek(0)

        self._seeksection(lasmaster,section)

    def _seeksection(self,lasmaster,section=None):

        if section is None:
            section = "~"

        while True:

            line = next(lasmaster).strip()

            if line.startswith(section):
                break

    def version(self,lasmaster):
        """It returns the version of file."""

        pattern = r"\s*VERS\s*\.\s+([^:]*)\s*:"

        program = re.compile(pattern)

        lasmaster.seek(0)

        self._seeksection(lasmaster,section="~V")

        while True:

            line = next(lasmaster).strip()

            if line.startswith("~"):
                break
            
            version = program.match(line)

            if version is not None:
                break

        return version.groups()[0].strip()

    def program(self,version="2.0"):
        """It returns the program that compiles the regular expression to retrieve parameter data."""

        """
        Mnemonic:

        LAS Version 2.0
        This mnemonic can be of any length but must not contain any internal spaces, dots, or colons.

        LAS Version 3.0
        Any length >0, but must not contain periods, colons, embedded spaces, tabs, {}, [], |
        (bar) characters, leading or trailing spaces are ignored. It ends at (but does not include)
        the first period encountered on the line.
        
        """

        if version in ["1.2","1.20"]:
            mnemonic = r"[^:\.\s]+"
        elif version in ["2.0","2.00"]:
            mnemonic = r"[^:\.\s]+"
        elif version in ["3.0","3.00"]:
            mnemonic = r"[^:\.\s\{\}\|\[\]]+"

        """
        Unit:
        
        LAS Version 2.0
        The units if used, must be located directly after the dot. There must be not spaces
        between the units and the dot. The units can be of any length but must not contain any
        colons or internal spaces.

        LAS Version 3.0
        Any length, but must not contain colons, embedded spaces, tabs, {} or | characters. If present,
        it must begin at the next character after the first period on the line. The Unitends at
        (but does not include) the first space or first colon after the first period on the line.
        
        """

        if version in ["1.2","1.20"]:
            unit = r"[^:\s]*"
        elif version in ["2.0","2.00"]:
            unit = r"[^:\s]*"
        elif version in ["3.0","3.00"]:
            unit = r"[^:\s\{\}\|]*"

        """
        Value:
        
        LAS Version 2.0
        This value can be of any length and can contain spaces or dots as appropriate, but must not contain any colons.
        It must be preceded by at least one space to demarcate it from the units and must be to the left of the colon.

        LAS Version 3.0
        Any length, but must not contain colons, {} or | characters. If the Unit field is present,
        at least one space must exist between the unit and the first character of the Value field.
        The Value field ends at (but does not include) the last colon on the line.
        
        """

        if version in ["1.2","1.20"]:
            value = r"[^:]*"
        elif version in ["2.0","2.00"]:
            value = r"[^:]*"
        elif version in ["3.0","3.00"]:
            value = r"[^:\{\}\|]*"
        
        """
        Description:

        LAS Version 2.0
        It is always located to the right of the colon. Its length is limited by the total
        line length limit of 256 characters which includes a carriage return and a line feed.
        
        LAS Version 3.0
        Any length, Begins as the first character after the last colon on the line, and ends at the
        last { (left brace), or the last | (bar), or the end of the line, whichever is encountered
        first.

        """

        description = r".*"

        pattern = f"\\s*({mnemonic})\\s*\\.({unit})\\s+({value})\\s*:\\s*({description})"

        program = re.compile(pattern)

        return program

    def headers(self,lasmaster):

        version = self.version(lasmaster)
        program = self.program(version)

        lasmaster.seek(0)

        while True:

            line = next(lasmaster).strip()

            if line.startswith("~A"):
                types = self._types(lasmaster)
                break

            if line.startswith("~"):

                sectioncode = line[:2]
                sectionhead = line[1:].split()[0].lower()
                sectionbody = self._header(lasmaster,program)

                self.sections.append(sectionhead)

                setattr(self,sectionhead,sectionbody)

                lasmaster.seek(0)

                self._seeksection(lasmaster,section=sectioncode)

        return types

    def _header(self,lasmaster,program):

        mnemonic,unit,value,description = [],[],[],[]

        mnemonic_parantheses_pattern = r'\([^)]*\)\s*\.'

        while True:

            line = next(lasmaster).strip()

            if len(line)<1:
                continue
            
            if line.startswith("#"):
                continue

            if line.startswith("~"):
                break

            line = re.sub(r'[^\x00-\x7F]+','',line)

            mpp = re.search(mnemonic_parantheses_pattern,line)

            if mpp is not None:
                line = re.sub(mnemonic_parantheses_pattern,' .',line) # removing the content in between paranthesis for mnemonics

            mnemonic_,unit_,value_,description_ = program.match(line).groups()

            if mpp is not None:
                mnemonic_ = f"{mnemonic_} {mpp.group()[:-1]}"

            mnemonic.append(mnemonic_.strip())

            unit.append(unit_.strip())

            value.append(value_.strip())

            description.append(description_.strip())

        section = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

        return section

    def types(self,lasmaster):

        lasmaster.seek(0)

        return self._types(lasmaster)

    def _types(self,lasmaster):

        while True:

            line = next(lasmaster).strip()

            if len(line)<1:
                continue
            
            if line.startswith("#"):
                continue

            break

        row = re.sub(r"\s+"," ",line).split(" ")

        types = [str0type(value) for value in row]

        return types

    def text(self,lasmaster):

        types = self.headers(lasmaster)

        value_null = float(self.well['NULL'].value)

        dtypes = [numpy.dtype(type_) for type_ in types]

        floatFlags = [True if type_ is float else False for type_ in types]

        lasmaster.seek(0)

        self._seeksection(lasmaster,section="~A")

        if all(floatFlags):
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1")
        else:
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1",dtype='str')

        iterator = zip(cols,self.curve.mnemonic,self.curve.unit,self.curve.description,dtypes)

        running = []

        for vals,head,unit,info,dtype in iterator:

            if dtype.type is numpy.dtype('float').type:
                vals[vals==value_null] = numpy.nan

            column_ = column(vals,head=head,unit=unit,info=info,dtype=dtype)

            running.append(column_)

        frame = DataFrame(*running)

        if not ulas._issorted(frame.running[0].vals):
            frame = frame.sort((frame.running[0].head,))

        return frame

    def issorted(self):

        depths_ = self.frame.running[0].vals

        return ulas._issorted(depths_)

    @staticmethod
    def _issorted(depths):

        if numpy.all(depths[:-1]<depths[1:]):
            return True
        else:
            return False

    def nanplot(self,axis):

        yvals = []
        zvals = []

        depth = self.frame.running[0].vals

        for index,column_ in enumerate(self.frame.running):

            isnan = numpy.isnan(column_.vals)

            L_shift = numpy.ones(column_.size,dtype=bool)
            R_shift = numpy.ones(column_.size,dtype=bool)

            L_shift[:-1] = isnan[1:]
            R_shift[1:] = isnan[:-1]

            lower = numpy.where(numpy.logical_and(~isnan,R_shift))[0]
            upper = numpy.where(numpy.logical_and(~isnan,L_shift))[0]

            zval = numpy.concatenate((lower,upper),dtype=int).reshape((2,-1)).T.flatten()

            yval = numpy.full(zval.size,index,dtype=float)
            
            yval[::2] = numpy.nan

            yvals.append(yval)
            zvals.append(zval)

        qvals = numpy.unique(numpy.concatenate(zvals))

        for (yval,zval) in zip(yvals,zvals):
            axis.step(numpy.where(qvals==zval.reshape((-1,1)))[1],yval)

        axis.set_xlim((-1,qvals.size))
        axis.set_ylim((-1,self.frame.shape[1]))

        axis.set_xticks(numpy.arange(qvals.size))
        axis.set_xticklabels(depth[qvals],rotation=90)

        axis.set_yticks(numpy.arange(self.frame.shape[1]))
        axis.set_yticklabels(self.frame.heads)

        axis.grid(True,which="both",axis='x')

        return axis

    def depths(self,top,bottom,curve=None):

        depth = self.frame.running[0].vals

        conds = numpy.logical_and(depth>=top,depth<=bottom)

        if curve is None:
            frame = copy.deepcopy(self.frame)
            return frame[conds]

        else:
            column_ = copy.deepcopy(self.frame[curve])
            return column_[conds]

    def resample(self,depths1,curve=None):
        """Resamples the frame data based on given depths1."""

        """
        depths1 :   The depth values where new curve data will be calculated;
        curve   :   The head of curve to resample; If None, all curves in the file will be resampled;

        """

        depths0 = self.frame.running[0].vals

        if curve is not None:
            values0 = self.frame[curve].vals

            column_ = copy.deepcopy(self.frame[curve])
            column_.vals = ulas._resample(depths1,depths0,values0)
            
            return column_

        if not ulas._issorted(depths1):
            raise ValueError("Input depths are not sorted.")

        outers_above = depths1<depths0.min()
        outers_below = depths1>depths0.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths1_inners_ = depths1[inners]

        lowers = numpy.empty(depths1_inners_.shape,dtype=int)
        uppers = numpy.empty(depths1_inners_.shape,dtype=int)

        lower = 0
        upper = 0

        for index,depth in enumerate(depths1_inners_):

            while depth>depths0[lower]:
                lower += 1

            while depth>depths0[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depths1 = depths1_inners_-depths0[lowers]
        delta_depths0 = depths0[uppers]-depths0[lowers]

        grads = delta_depths1/delta_depths0

        frame = copy.deepcopy(self.frame)

        for index,column_ in enumerate(self.frame.running):

            if index==0:
                frame[column_.head].vals = depths1
                continue

            delta_values = column_.vals[uppers]-column_.vals[lowers]

            frame[column_.head].vals = numpy.empty(depths1.shape,dtype=float)

            frame[column_.head].vals[outers_above] = numpy.nan
            frame[column_.head].vals[inners] = column_.vals[lowers]+grads*(delta_values)
            frame[column_.head].vals[outers_below] = numpy.nan

        return frame

    @staticmethod
    def _resample(depths1,depths0,values0):

        """
        depths1 :   The depths where new curve values will be calculated;
        depths0 :   The depths where the values are available;
        values0 :   The values to be resampled;

        """

        if not ulas._issorted(depths1):
            raise ValueError("Input depths are not sorted.")

        outers_above = depths1<depths0.min()
        outers_below = depths1>depths0.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths1_inners_ = depths1[inners]

        lowers = numpy.empty(depths1_inners_.shape,dtype=int)
        uppers = numpy.empty(depths1_inners_.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depths1_inners_):

            while depth>depths0[lower]:
                lower += 1

            while depth>depths0[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

            # diff = depths0-depth
            # lowers[index] = numpy.where(diff<0,diff,-numpy.inf).argmax()
            # uppers[index] = numpy.where(diff>0,diff,+numpy.inf).argmin()

        delta_depths1 = depths1_inners_-depths0[lowers]
        delta_depths0 = depths0[uppers]-depths0[lowers]
        delta_values0 = values0[uppers]-values0[lowers]

        grads = delta_depths1/delta_depths0

        values = numpy.empty(depths1.shape,dtype=float)

        values[outers_above] = numpy.nan
        values[inners] = values0[lowers]+grads*(delta_values0)
        values[outers_below] = numpy.nan

        return values

class _loadsched(dirmaster):

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

        for index,column_ in enumerate(self._running):
            self._running[index] = numpy.array(self._running[index][firstocc:][~match_index[firstocc:]])

        self.headers = self._headers
        self.running = [numpy.asarray(column_) for column_ in self._running]

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

class _loadxlbook(dirmaster):

    def __init__(self,filepath,homedir=None,filedir=None,**kwargs):

        with xlbatch.xlopen(filepath) as book:

            for sheet in sheets:

                print("Loading {} {}".format(filepath,sheet))

                frame = self.load(book,sheet,**kwargs)

                self.frames.append(frame)

    def load(self,book,sheet,sheetsearch=False,min_row=1,min_col=1,max_row=None,max_col=None,hrows=0):
        """It reads provided excel worksheet and returns it as a DataFrame."""

        frame = DataFrame()

        if sheet is None:
            sheetname = book.sheetnames[0]
        elif isinstance(sheet,int):
            sheetname = book.sheetnames[sheet]
        elif isinstance(sheet,str) and sheetsearch:
            srcscores = [SequenceMatcher(None,page,sheet).ratio() for page in book.sheetnames]
            sheetname = book.sheetnames[srcscores.index(max(srcscores))]
        elif isinstance(sheet,str):
            if sheet in book.sheetnames:
                sheetname = sheet
            else:
                raise ValueError(f"'{sheet}' could not be found in the xlbook, try sheetsearch=True.")
        else:
            raise TypeError(f"Expected sheet is either none, int or str, but the input type is {type(sheet[1])}.")

        # frame.sheetname = sheetname

        rows = book[sheetname].iter_rows(
            min_row=min_row,max_row=max_row,
            min_col=min_col,max_col=max_col,
            values_only=True)

        cols = []
    
        for index,row in enumerate(rows):
            if index==0:
                [cols.append([]) for _ in row]
            if any(row):
                [col.append(cell) for cell,col in zip(row,cols)]

        heads_ = key2column(size=(len(cols)+min_col-1),dtype='str')
        heads_ = heads_.vals[min_col-1:]

        for index,col in enumerate(cols):
            if any(col):
                info = " ".join([str(cell) for cell in col[:hrows] if cell is not None])
                column_ = column(col[hrows:],head=heads_[index],info=info)
                frame._setup(column_)

        return frame

    @contextlib.contextmanager
    def xlopen(filepath):
        xlbook = openpyxl.load_workbook(filepath,read_only=True,data_only=True)
        try:
            yield xlbook
        finally:
            xlbook._archive.close()

# Collective Data Input/Output Classes

class lasbatch(dirmaster):

    def __init__(self,filepaths=None,**kwargs):

        homedir = None if kwargs.get("homedir") is None else kwargs.pop("homedir")
        filedir = None if kwargs.get("filedir") is None else kwargs.pop("filedir")

        super().__init__(homedir=homedir,filedir=filedir)

        self.frames = []

        self.load(filepaths,**kwargs)

    def load(self,filepaths,**kwargs):

        if filepaths is None:
            return

        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:

            frame = loadlas(filepath,**kwargs)

            self.frames.append(frame)

            logging.info(f"Loaded {filepath} as expected.")

    def wells(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            frame = self.frames[index]

            print("\n\tWELL #{}".format(frame.well.get_row(mnemonic="WELL")["value"]))

            # iterator = zip(frame.well["mnemonic"],frame.well["units"],frame.well["value"],frame.well.descriptions)

            iterator = zip(*frame.well.get_columns())

            for mnem,unit,value,descr in iterator:
                print(f"{descr} ({mnem}):\t\t{value} [{unit}]")

    def curves(self,idframes=None,mnemonic_space=33,tab_space=8):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            frame = self.frames[index]

            iterator = zip(frame.headers,frame.units,frame.details,frame.running)

            # file.write("\n\tLOG NUMBER {}\n".format(idframes))
            print("\n\tLOG NUMBER {}".format(index))

            for header,unit,detail,column_ in iterator:

                if numpy.all(numpy.isnan(column_)):
                    minXval = numpy.nan
                    maxXval = numpy.nan
                else:
                    minXval = numpy.nanmin(column_)
                    maxXval = numpy.nanmax(column_)

                tab_num = int(numpy.ceil((mnemonic_space-len(header))/tab_space))
                tab_spc = "\t"*tab_num if tab_num>0 else "\t"

                # file.write("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}\n".format(
                #     curve.mnemonic,tab_spc,curve.unit,minXval,maxXval,curve.descr))
                print("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}".format(
                    header,tab_spc,unit,minXval,maxXval,detail))

    def merge(self,fileIDs,curveNames):

        if isinstance(fileIDs,int):

            try:
                depth = self.frames[fileIDs]["MD"]
            except KeyError:
                depth = self.frames[fileIDs]["DEPT"]

            xvals1 = self.frames[fileIDs][curveNames[0]]

            for curveName in curveNames[1:]:

                xvals2 = self.frames[fileIDs][curveName]

                xvals1[numpy.isnan(xvals1)] = xvals2[numpy.isnan(xvals1)]

            return depth,xvals1

        elif numpy.unique(numpy.array(fileIDs)).size==len(fileIDs):

            if isinstance(curveNames,str):
                curveNames = (curveNames,)*len(fileIDs)

            depth = numpy.array([])
            xvals = numpy.array([])

            for (fileID,curveName) in zip(fileIDs,curveNames):

                try:
                    depth_loc = self.frames[fileID]["MD"]
                except KeyError:
                    depth_loc = self.frames[fileID]["DEPT"]

                xvals_loc = self.frames[fileID][curveName]

                depth_loc = depth_loc[~numpy.isnan(xvals_loc)]
                xvals_loc = xvals_loc[~numpy.isnan(xvals_loc)]

                depth_max = 0 if depth.size==0 else depth.max()

                depth = numpy.append(depth,depth_loc[depth_loc>depth_max])
                xvals = numpy.append(xvals,xvals_loc[depth_loc>depth_max])

            return depth,xvals

class xlbatch(dirmaster):

    def __init__(self,filepaths=None,sheetnames=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.loadall(filepaths,sheetnames,**kwargs)

    def load(self,filepaths,sheetnames=None,**kwargs):
        """It add frames from the excel worksheet provided with filepaths and sheetnames."""

        if filepaths is None:
            return
        elif type(filepaths) is str:
            filepaths = (filepaths,)
        else:
            filepaths = tuple(filepaths)

        if sheetnames is None:
            sheets = (sheetnames,)
        elif type(sheetnames) is str:
            sheets = (sheetnames,)
        else:
            sheets = tuple(sheetnames)

        for filepath in filepaths:

            filepath = self.get_abspath(filepath)

            frame = loadxlbook(filepath,**kwargs)

            self.frames.append(frame)

            logging.info(f"Loaded {filepath} as expected.")

    def merge(self,cols=None,idframes=None,infosearch=False):
        """It merges all the frames as a single DataFrame under the Excel class."""

        frame_merged = DataFrame()

        if cols is None:
            pass
        elif type(cols) is int:
            cols = (cols,)
        elif type(cols) is str:
            cols = (cols,)
        else:
            cols = tuple(cols)

        if idframes is None:
            idframes = range(len(self.frames))
        elif type(idframes) is int:
            idframes = (idframes,)
        elif type(idframes) is str:
            idframes = (idframes,)
        else:
            idframes = tuple(idframes)

        for idframe in idframes:

            frame = self.frames[idframe]

            if cols is None:
                cols_ = [col_ for col_ in frame.running]
            elif not infosearch:
                cols_ = []
                for index in tuple(cols):
                    if type(index) is int:
                        cols_.append(frame.running[index])
                    elif type(index) is str:
                        cols_.append(frame[index])
                    else:
                        raise TypeError(f"cols type should be either int or str, not {type(index)}")
            else:
                cols_ = []
                for index in tuple(cols):
                    if type(index) is str:
                        scores = [SequenceMatcher(None,info,index).ratio() for info in frame.infos]
                        cols_.append(frame.running[scores.index(max(scores))])
                    else:
                        raise TypeError(f"cols type should be str, not {type(index)}")

            frame_merged._append(*cols_)

        return frame_merged

if __name__ == "__main__":

    import unittest

    from tests import textio_test

    unittest.main(textio_test)

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