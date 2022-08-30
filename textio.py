import contextlib
import copy
import datetime

from difflib import SequenceMatcher

import logging

import os
import re

import numpy
import openpyxl
import pint
import lasio

if __name__ == "__main__":
    import setup

from core import column
from core import any2column
from core import key2column

from cypy.vectorpy import pytype

"""
1. DataFrame reading, writing
2. Finalize RegText reading, writing
3. Finalize LogASCII reading, writing
4. Finalize Excel writing
5. loadtext should be working well
"""

class DirBase():
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

class DataFrame(DirBase):
    """It stores equal-size one-dimensional numpy arrays in a list."""

    """INITIALIZATION"""

    def __init__(self,*args,**kwargs):
        """Initializes DataFrame with headers & running and parent class DirBase."""

        homedir = kwargs.get('homedir')
        filedir = kwargs.get('filedir')

        filepath = kwargs.get('filepath')

        super().__init__(homedir=homedir,filedir=filedir,filepath=filepath)

        if homedir is not None:
            kwargs.pop('homedir')

        if filedir is not None:
            kwargs.pop('filedir')

        if filepath is not None:
            kwargs.pop('filepath')

        super().__setattr__("running",[])

        self._setup(*args)

        for key,vals in kwargs.items():
            self.__setitem__(key,vals)

    def _setup(self,*args):

        for arg in args:

            if type(arg) is not column:
                raise TypeError(f"Argument/s need/s to be column type only!")

            if self.shape[1]!=0 and self.shape[0]!=arg.size:
                raise ValueError(f"Attached column size is not the same as of dataframe.")

            if arg.head in self.heads:
                self.running[self._index(arg.head)[0]] = arg
            else:
                self.running.append(arg)

    def _append(self,*args):

        if len(args)==0:
            return
        elif len(set([len(arg) for arg in args]))!=1:
            raise ValueError("columns have variable lenghts.")

        if self.shape[1]==0:
            self._setup(*args)
        elif self.shape[1]!=len(args):
            raise ValueError("Number of columns does not match columns in dataframe.")
        else:
            [col_.append(arg_) for col_,arg_ in zip(self.running,args)]

    """REPRESENTATION"""

    def __str__(self):
        """It prints to the console limited number of rows with headers."""

        print_limit = 20

        print_limit = int(print_limit)

        upper = int(numpy.ceil(print_limit/2))
        lower = int(numpy.floor(print_limit/2))

        if self.shape[0]>print_limit:
            rows = list(range(upper))
            rows.extend(list(range(-lower,0,1)))
        else:
            rows = list(range(self.shape[0]))

        frame_ = self[rows]

        headcount = [len(head) for head in frame_.heads]
        bodycount = [col_.maxchar() for col_ in frame_.running]
        charcount = [max(hc,bc) for (hc,bc) in zip(headcount,bodycount)]

        # print(headcount,bodycount,charcount)

        fstring = " ".join(["{{:>{}s}}".format(cc) for cc in charcount])
        fstring = "{}\n".format(fstring)

        heads_str = fstring.format(*frame_.heads)
        lines_str = fstring.format(*["-"*count for count in charcount])
        large_str = fstring.format(*[".." for _ in charcount])

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        bodycols = vprint(*[col_.tostring() for col_ in frame_.running]).tolist()

        if self.shape[0]>print_limit:
            [bodycols.insert(upper,large_str) for _ in range(3)]

        string = ""
        string += heads_str
        string += lines_str
        string += "".join(bodycols)

        return string

    """ATTRIBUTE ACCESS"""

    def __setattr__(self,key,vals):

        if isinstance(vals,FrontMatterTable):
            super().__setattr__(key,vals)
        else:
            raise AttributeError(f"'DataFrame' object has no attribute '{key}'.")

    """CONTAINER METHODS"""

    def pop(self,key):

        return self.running.pop(self._index(key)[0])

    def _index(self,*args):

        if len(args)==0:
            raise TypeError(f"Index expected at least 1 argument, got 0")

        if any([type(key) is not str for key in args]):
            raise TypeError(f"argument/s must be string!")

        if any([key not in self.heads for key in args]):
            raise ValueError(f"The dataframe does not have key specified in {args}.")

        return tuple([self.heads.index(key) for key in args])

    def __setitem__(self,key,vals):

        if not isinstance(key,str):
            raise TypeError(f"The key can be str, not type={type(key)}.")

        col_ = column(vals,head=key)

        self._setup(col_)

    def __delitem__(self,key):

        if isinstance(key,str):
            self.pop(key)
            return

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):
                [self.pop(_key) for _key in key]
                return
            elif any([type(_key) is str for _key in key]):
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        dataframe_ = copy.deepcopy(self)
        object.__setattr__(dataframe_,'running',
            [np.delete(col_,key) for col_ in self.running])

        return dataframe_
        
    def __iter__(self):

        return iter([row for row in zip(*self.running)])

    def __len__(self):

        return self.shape[0]

    def __getitem__(self,key):

        if isinstance(key,str):
            return self.running[self._index(key)[0]]

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):

                cols_ = [self.running[i] for i in self._index(*key)]

                dataframe_ = copy.deepcopy(self)

                object.__setattr__(dataframe_,'running',cols_)

                return dataframe_

            elif any([type(_key) is str for _key in key]):
                
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        cols_ = [col_[key] for col_ in self.running]

        dataframe_ = copy.deepcopy(self)

        object.__setattr__(dataframe_,'running',cols_)

        return dataframe_

    """CONVERSION METHODS"""

    def str2col(self,key=None,delimiter=None,maxsplit=None):
        """Breaks the column into new columns by splitting based on delimiter and maxsplit."""

        idcol_ = self._index(key)[0]

        col_ = self.pop(key)

        if maxsplit is None:
            maxsplit = numpy.char.count(col_,delimiter).max()

        heads = ["{}_{}".format(col_.head,index) for index in range(maxsplit+1)]

        running = []

        for index,string in enumerate(col_.vals):

            row = string.split(delimiter,maxsplit=maxsplit)

            if maxsplit+1>len(row):
                [row.append(col_.nones.str) for _ in range(maxsplit+1-len(row))]

            running.append(row)

        running = numpy.array(running,dtype=str).T

        for index,(vals,head) in enumerate(zip(running,heads),start=idcol_):
            col_new = col_[:]
            col_new.vals = vals
            col_new.head = head
            self.running.insert(index,col_new)

    def col2str(self,heads=None,headnew=None,fstring=None):

        if heads is None:
            heads = self.heads

        arr_ = [self[head].vals for head in heads]

        if fstring is None:
            fstring = ("{} "*len(arr_))[:-1]

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        arrnew = vprint(*arr_)

        if headnew is None:
            fstring = ("{}_"*len(arr_))[:-1]
            headnew = fstring.format(*heads)

        return column(arrnew,head=headnew)

    def tostruct(self):
        """Returns numpy structure of dataframe."""

        dtype_str_ = [col_.vals.dtype.str for col_ in self.running]

        dtypes_ = [dtype_ for dtype_ in zip(self.heads,dtype_str_)]

        return numpy.array([row for row in self],dtypes_)

    """ADVANCED METHODS"""
            
    def sort(self,heads,reverse=False,return_indices=False):
        """Returns sorted dataframe."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        cols_ = self[heads]

        match = numpy.argsort(cols_.tostruct(),axis=0,order=heads)

        if reverse:
            match = numpy.flip(match)

        if return_indices:
            return match
        else:
            dataframe_ = copy.deepcopy(self)
            running_ = [col_[match] for col_ in self.running]
            object.__setattr__(dataframe_,'running',running_)
            return dataframe_

    def flip(self):

        dataframe_ = copy.deepcopy(self)

        running_ = [col_.flip() for col_ in self.running]

        object.__setattr__(dataframe_,'running',running_)

    def filter(self,key,keywords=None,regex=None,return_indices=False):
        """Returns filtered dataframe based on keywords or regex."""

        col_ = self[key]

        match = col_.filter(keywords,regex,return_indices=True)

        if return_indices:
            return match
        else:
            dataframe_ = copy.deepcopy(self)
            object.__setattr__(dataframe_,'running',
                [col_[match] for col_ in self.running])
            return dataframe_

    def unique(self,heads):
        """Returns dataframe with unique entries of column/s.
        The number of columns will be equal to the length of heads."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        df = self[heads]

        npstruct = df.tostruct()

        npstruct = numpy.unique(npstruct,axis=0)

        dataframe_ = copy.deepcopy(self)

        object.__setattr__(dataframe_,'running',[])

        for head in heads:

            col_ = copy.deepcopy(self[head])

            col_.vals = npstruct[head]

            dataframe_.running.append(col_)

        return dataframe_

    """CONTEXT MANAGERS"""

    def loadtxt(path,classname=None,**kwargs):

        if classname is None:
            if path.lower().endswith(".txt"):
                obj = RegText()
            elif path.lower().endswith(".las"):
                obj = LogASCII()
            elif path.lower().endswith(".xlsx"):
                obj = Excel()
            elif path.lower().endswith(".vtk"):
                obj = VTKit()
            else:
                obj = IrrText()
        elif classname.lower()=="regtext":
            obj = RegText()
        elif classname.lower()=="logascii":
            obj = LogASCII()
        elif classname.lower()=="excel":
            obj = Excel()
        elif classname.lower()=="irrtext":
            obj = IrrText()
        elif classname.lower()=="wschedule":
            obj = WSchedule()
        elif classname.lower()=="vtkit":
            obj = VTKit()

        frame = obj.read(path,**kwargs)

        return frame

    def read(self):

        pass

    def readb(self):

        pass

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

    def _not_merged_to_dataframe_yet_read_write_b(self):

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

    """PROPERTY METHODS"""

    @property
    def shape(self):

        if len(self.running)>0:
            return (max([len(col_) for col_ in self.running]),len(self.running))
        else:
            return (0,0)

    @property
    def dtypes(self):

        return [col_.vals.dtype for col_ in self.running]

    @property
    def types(self):

        return [col_.vals.dtype.type for col_ in self.running]

    @property
    def heads(self):

        return [col_.head for col_ in self.running]

    @property
    def units(self):

        return [col_.unit for col_ in self.running]

    @property
    def infos(self):

        return [col_.info for col_ in self.running]

class FrontMatterTable():
    """It is a table of fields, columns are fields, rows are data"""

    def __init__(self,**kwargs):

        self.matter = []

        class field: pass

        for name,data in kwargs.items():
            self.matter.append(setattr(field,name,data))

    def index(self,key):

        for field in matter:
            if field.name==key:
                return field

    def append(self,row):

        for field,value in zip(self.matter,row):
            field.data.append(value)

    def __getattr__(self,key):

        return self.index(key).data

    def __getitem__(self,key):

        if isinstance(key,str):
            for row in self:
                if row[0]==key:
                    return row
        else:
            return [field.data[key] for field in self.matter]

    def __repr__(self):

        fstring = ""
        
        underline = []

        for field in self.matter:
            
            column_ = field.data
            column_.append(field.name)
            
            char_count = max([len(str(value)) for value in column_])

            fstring += f"{{:<{char_count}}}   "
            
            underline.append("-"*char_count)

        fstring += "\n"

        text = fstring.format(*[name.capitalize() for name in self.names])
        
        text += fstring.format(*underline)
        
        for row in self:
            text += fstring.format(*row)

        return text

    def __iter__(self):

        return iter([row for row in zip(*self.matter)])

    def __len__(self):

        if len(self.matter)==0:
            return 0
        else:
            return len(self.matter[0])

    @property
    def names(self):
        return [field.name for field in self.matter]
    
# Collective Data Input/Output Classes

class RegText(DataFrame):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.read(filepaths,**kwargs)

    def read(self,filepaths,**kwargs):

        if filepaths is None:
            return
        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:
            self.frames.append(self._read(filepath,**kwargs))
            logging.info(f"Loaded {filepath} as expected.")

    def _read(self,filepath,delimiter="\t",comments="#",skiprows=None,nondigitflag=False):

        filepath = self.get_abspath(filepath)

        frame = DataFrame(filedir=filepath)

        frame.filepath = filepath

        with open(filepath,mode="r",encoding="latin1") as text:

            if skiprows is None:
                skiprows = 0
                line = next(text).split("\n")[0]
                while not line.split(delimiter)[0].isdigit():
                    skiprows += 1
                    line = next(text).split("\n")[0]
            else:
                for _ in range(skiprows):
                    line = next(text)

            line = next(text).split("\n")[0]

        if nondigitflag:
            row = line.split(delimiter)
            dtypes = [float if column_.isdigit() else str for column_ in row]
            columns = []
            for index,dtype in enumerate(dtypes):
                column_ = numpy.loadtxt(filepath,dtype=dtype,delimiter=delimiter,skiprows=skiprows,usecols=[index],encoding="latin1")
                columns.append(column_)
        else:
            data = numpy.loadtxt(filepath,comments="#",delimiter=delimiter,skiprows=skiprows,encoding="latin1")
            columns = [column_ for column_ in data.transpose()]

        frame.set_running(*columns,init=True)

        return frame

class LogASCII(DataFrame):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.read(filepaths,**kwargs)

    def read(self,filepaths,**kwargs):

        if filepaths is None:
            return

        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:

            frame = self._read(filepath,**kwargs)

            self.frames.append(frame)

            logging.info(f"Loaded {filepath} as expected.")

    def _read(self,filepath):

        frame = DataFrame(filepath=filepath)

        with open(frame.filepath,"r",encoding="latin1") as lasfile:

            version = self._read_version(lasfile)
            program = self._read_program(version)
            
            frame,skiprows,types = self._read_frontmatter(frame,lasfile,program)

        frame = self._read_columns(frame,skiprows,types)

        return frame

    def _read_version(self,lasfile):
        """It returns the version of file."""

        pattern = r"\s*VERS\s*\.\s+([^:]*)\s*:"

        program = re.compile(pattern)

        lasfile.seek(0)

        while True:

            line = next(lasfile).strip()

            if line.startswith("~V"):
                break

        line = next(lasfile).strip()

        version = program.match(line)

        while version is None:
            line = next(lasfile).strip()

            if line.startswith("~"):
                break
            else:
                version = program.match(line)

        if version is None:
            return
        else:
            return version.groups()[0].strip()

    def _read_program(self,version="2.0"):
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

        if version == "2.0":
            mnemonic = r"[^:\s\.]+"
        elif version == "3.0":
            mnemonic = r"[^:\{\}\|\s\[\]\.]+"

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

        if version == "2.0":
            unit = r"[^:\s]*"
        elif version == "3.0":
            unit = r"[^:\{\}\|\s]*"

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

        if version == "2.0":
            value = r"[^:]*"
        elif version == "3.0":
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

    def _read_frontmatter(self,frame,lasfile,program):

        lasfile.seek(0)

        while True:

            line = next(lasfile).strip()

            if line.startswith("~A"):
                break
            elif line.startswith("~"):
                title = line[1:].split()[0].lower()
                section = self._read_section(lasfile,program)
                setattr(frame,title,section)

        skiprows = self._read_skiprows(lasfile)

        types = self._read_types(lasfile)

        return frame,skiprows,types

    def _read_section(self,lasfile,program):

        mnemonic,unit,value,description = [],[],[],[]

        while True:

            line = next(lasfile).strip()

            if len(line)<1:
                pass
            
            if line.startswith("#"):
                pass

            if line.startswith("~"):
                break

            line = re.sub(r'[^\x00-\x7F]+','',line)

            mnemonic,unit,value,description = program.match(line).groups()

            mnemonics.append(mnemonic.strip())

            units.append(unit.strip())

            values.append(value.strip())

            descriptions.append(description.strip())

        section = FrontMatterTable(mnemonic=mnemonics,unit=units,value=values,description=descriptions)

        return section

    def _read_skiprows(self,lasfile):

        lasfile.seek(0)

        skiprows = 1

        while True:

            line = next(lasfile).strip()

            if line.startswith("~A"):
                break

            skiprows += 1

        return skiprows

    def _read_types(self,lasfile):

        while True:

            line = next(lasfile).strip()

            if len(line)<1:
                pass
            
            if line.startswith("#"):
                pass

            break

        row = re.sub(r"\s+"," ",line).split(" ")

        types = [pytype(value) for value in row]

        return types

    def _read_columns(self,frame,skiprows,types):

        value_null = float(frame.well['NULL'].value)

        floatFlag = all([pytype is float for pytype in types])

        dtypes = [np.dtype(pytype) for pytype in types]

        if floatFlag:
            matrix = numpy.loadtxt(frame.filepath,comments="#",skiprows=skiprows,encoding="latin1")
        else:
            matrix = numpy.loadtxt(frame.filepath,comments="#",skiprows=skiprows,encoding="latin1",dtype='str')

        for index,(vals,dtype) in enumerate(zip(matrix.transpose(),dtypes)):

            if dtype.type is numpy.dtype('float').type:
                vals[vals==value_null] = numpy.nan
            
            head = frame.curve.mnemonics[index]
            unit = frame.curve.units[index]
            info = frame.curve.info[index]

            frame._setup(column(vals,head=head,unit=unit,info=info))

        return frame

    def printwells(self,idframes=None):

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

    def printcurves(self,idframes=None,mnemonic_space=33,tab_space=8):

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

    def set_nangraph(self,idframe):

        self.fig_nan,self.axis_nan = plt.subplots()

        las = self.frames[idframe]

        yvals = []
        zvals = []

        depth = las.columns(0)

        for index,column in enumerate(las.running):

            isnan = np.isnan(column)

            L_shift = np.ones(column.shape,dtype=bool)
            R_shift = np.ones(column.shape,dtype=bool)

            L_shift[:-1] = isnan[1:]
            R_shift[1:] = isnan[:-1]

            lower = np.where(np.logical_and(~isnan,R_shift))[0]
            upper = np.where(np.logical_and(~isnan,L_shift))[0]

            zval = np.concatenate((lower,upper),dtype=int).reshape((2,-1)).T.flatten()

            yval = np.full(zval.size,index,dtype=float)
            
            yval[::2] = np.nan

            yvals.append(yval)
            zvals.append(zval)

        qvals = np.unique(np.concatenate(zvals))

        for (yval,zval) in zip(yvals,zvals):
            self.axis_nan.step(np.where(qvals==zval.reshape((-1,1)))[1],yval)

        self.axis_nan.set_xlim((-1,qvals.size))
        self.axis_nan.set_ylim((-1,len(las.running)))

        self.axis_nan.set_xticks(np.arange(qvals.size))
        self.axis_nan.set_xticklabels(depth[qvals],rotation=90)

        self.axis_nan.set_yticks(np.arange(len(las.running)))
        self.axis_nan.set_yticklabels(las.headers)

        self.axis_nan.grid(True,which="both",axis='x')

        self.fig_nan.tight_layout()

    def set_histogram(self,idframe,idcol,logscale=False):

        self.fig_hist,self.axis_hist = plt.subplots()

        las = self.frames[idframe]

        yaxis = las.running[idcol]

        if logscale:
            yaxis = np.log10(yaxis[np.nonzero(yaxis)[0]])

        try:
            unit = las.units[idcol]
        except IndexError:
            unit = "not-defined"

        try:
            descr = las.details[idcol]
        except IndexError:
            descr = las.headers[idcol]

        if logscale:
            xlabel = "log10(nonzero-{}) [{}]".format(descr,unit)
        else:
            xlabel = "{} [{}]".format(descr,unit)

        self.axis_hist.hist(yaxis,density=True,bins=30)  # density=False would make counts
        self.axis_hist.set_ylabel("Probability")
        self.axis_hist.set_xlabel(xlabel)

    def flip(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            columns = [numpy.flip(column_) for column_ in self.frames[index].running]

            self.frames[index].set_running(*columns,cols=range(len(columns)))
            
    def set_interval(self,top,bottom,idframes=None,inplace=False):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        self.top = top
        self.bottom = bottom

        self.gross_thickness = self.bottom-self.top

        for index in idframes:

            depth = self.frames[index].columns(0)

            depth_cond = numpy.logical_and(depth>self.top,depth<self.bottom)

            if inplace:
                self.frames[index]._running = [column_[depth_cond] for column_ in self.frames[index]._running]
                self.frames[index].running = [numpy.asarray(column_) for column_ in self.frames[index]._running]
            else:
                self.frames[index].running = [numpy.asarray(column_[depth_cond]) for column_ in self.frames[index]._running]

    def get_interval(self,top,bottom,idframes=None,curveID=None):

        returningList = []

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for idfile in idframes:

            las = self.frames[idfile]

            try:
                depth = las.columns("MD")
            except ValueError:
                depth = las.columns("DEPT")

            depth_cond = numpy.logical_and(depth>top,depth<bottom)

            if curveID is None:
                returningList.append(depth_cond)
            else:
                returningList.append(las.columns(curveID)[depth_cond])

        return returningList

    def get_resampled(self,depthsR,depthsO,dataO):

        lowerend = depthsR<depthsO.min()
        upperend = depthsR>depthsO.max()

        interior = numpy.logical_and(~lowerend,~upperend)

        depths_interior = depthsR[interior]

        indices_lower = numpy.empty(depths_interior.shape,dtype=int)
        indices_upper = numpy.empty(depths_interior.shape,dtype=int)

        for index,depth in enumerate(depths_interior):

            diff = depthsO-depth

            indices_lower[index] = numpy.where(diff<0,diff,-numpy.inf).argmax()
            indices_upper[index] = numpy.where(diff>0,diff,numpy.inf).argmin()

        grads = (depths_interior-depthsO[indices_lower])/(depthsO[indices_upper]-depthsO[indices_lower])

        dataR = numpy.empty(depthsR.shape,dtype=float)

        dataR[lowerend] = numpy.nan
        dataR[interior] = dataO[indices_lower]+grads*(dataO[indices_upper]-dataO[indices_lower])
        dataR[upperend] = numpy.nan

        return dataR

    def resample(self,depthsFID=None,depthsR=None,fileID=None,curveID=None):

        """

        depthsFID:  The index of file id from which to take new depthsR
                    where new curve data will be calculated;

        depthsR:    The numpy array of new depthsR
                    where new curve data will be calculated;
        
        fileID:     The index of file to resample;
                    If None, all files will be resampled;
        
        curveID:    The index of curve in the las file to resample;
                    If None, all curves in the file will be resampled;
                    Else if fileID is not None, resampled data will be returned;

        """

        if depthsFID is not None:
            try:
                depthsR = self.frames[depthsFID].columns("MD")
            except ValueError:
                depthsR = self.frames[depthsFID].columns("DEPT")

        if fileID is None:
            fileIDs = range(len(self.frames))
        else:
            fileIDs = range(fileID,fileID+1)

        for indexI in fileIDs:

            if depthsFID is not None:
                if indexI==depthsFID:
                    continue

            las = self.frames[indexI]

            try:
                depthsO = las.columns("MD")
            except ValueError:
                depthsO = las.columns("DEPT")

            lowerend = depthsR<depthsO.min()
            upperend = depthsR>depthsO.max()

            interior = numpy.logical_and(~lowerend,~upperend)

            depths_interior = depthsR[interior]

            diff = depthsO-depths_interior.reshape((-1,1))

            indices_lower = numpy.where(diff<0,diff,-numpy.inf).argmax(axis=1)
            indices_upper = numpy.where(diff>0,diff,numpy.inf).argmin(axis=1)

            grads = (depths_interior-depthsO[indices_lower])/(depthsO[indices_upper]-depthsO[indices_lower])

            if curveID is None:
                running = [depthsR]
                # self.frames[indexI].set_running(depthsR,cols=0,init=True)

            if curveID is None:
                curveIDs = range(1,len(las.running))
            else:
                curveIDs = range(curveID,curveID+1)

            for indexJ in curveIDs:

                curve = las.columns(indexJ)

                dataR = numpy.empty(depthsR.shape,dtype=float)

                dataR[lowerend] = numpy.nan
                dataR[interior] = curve[indices_lower]+grads*(curve[indices_upper]-curve[indices_lower])
                dataR[upperend] = numpy.nan

                if curveID is None:
                    running.append(dataR)

            heads = self.frames[indexI].headers

            if curveID is None:
                curveIDs = list(curveIDs)
                curveIDs.insert(0,0)
                self.frames[indexI].set_running(*running,cols=curveIDs,init=True)
                self.frames[indexI].set_headers(*heads,cols=curveIDs,init=False)
            elif fileID is not None:
                return dataR

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

    def write(self,filepath,mnemonics,data,idfile=None,units=None,descriptions=None,values=None):

        """
        filepath:       It will write a lasio.LASFile to the given filepath
        idfile:         The file index which to write to the given filepath
                        If idfile is None, new lasio.LASFile will be created

        kwargs:         These are mnemonics, data, units, descriptions, values
        """

        if idfile is not None:

            lasfile = self.frames[idfile]

        else:

            lasfile = lasio.LASFile()

            lasfile.well.DATE = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

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
                lasfile.append_curve_item(curve)            

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

            lasfile.append_curve_item(curve)

        with open(filepath, mode='w') as filePathToWrite:
            lasfile.write(filePathToWrite)

class Excel(DataFrame):

    def __init__(self,filepaths=None,sheetnames=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.read(filepaths,sheetnames,**kwargs)

    def read(self,filepaths,sheetnames=None,**kwargs):
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

            with Excel.xlopen(filepath) as book:

                for sheet in sheets:

                    print("Loading {} {}".format(filepath,sheet))

                    frame = self._read(book,sheet,**kwargs)

                    self.frames.append(frame)

    def _read(self,book,sheet,sheetsearch=False,min_row=1,min_col=1,max_row=None,max_col=None,hrows=0):
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

        frame.sheetname = sheetname

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
                col_ = column(col[hrows:],head=heads_[index],info=info)
                frame._setup(col_)

        return frame

    def merge(self,cols=None,idframes=None,infosearch=False):
        """It merges all the frames as a single DataFrame under the Excel class."""

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

            self._append(*cols_)

    def write(self,filepath,title):

        wb = openpyxl.Workbook()

        sheet = wb.active

        if title is not None:
            sheet.title = title

        for line in running:
            sheet.append(line)

        wb.save(filepath)

    @contextlib.contextmanager
    def xlopen(filepath):
        xlbook = openpyxl.load_workbook(filepath,read_only=True,data_only=True)
        try:
            yield xlbook
        finally:
            xlbook._archive.close()

class IrrText(DataFrame):

    def __init__(self,filepath,**kwargs):

        super().__init__(**kwargs)

        if filepath is not None:
            self.filepath = self.get_abspath(filepath,homeFlag=False)

    def read(self,filepaths):

        self.filepaths = filepaths

    def _read(self,skiprows=0,headerline=None,comment="--",endline="/",endfile="END"):

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

        self._running = [numpy.asarray(column_) for column_ in nparray]

        self.running = [numpy.asarray(column_) for column_ in self._running]

    def merge(self):

        pass

    def write(self):

        pass

class WSchedule(DataFrame):

    # KEYWORDS: DATES,COMPDATMD,COMPORD,WCONHIST,WCONINJH,WEFAC,WELOPEN 

    headers    = ["DATE","KEYWORD","DETAILS",]

    dates      = " {} / "#.format(date)
    welspecs   = " '{}'\t1*\t2* / "
    compdatop  = " '{}'\t1*\t{}\t{}\tMD\t{}\t2*\t0.14 / "#.format(wellname,top,bottom,optype)
    compdatsh  = " '{}'\t1*\t{}\t{}\tMD\t{} / "#.format(wellname,top,bottom,optype)
    compord    = " '{}'\tINPUT\t/ "#.format(wellname)
    prodhist   = " '{}'\tOPEN\tORAT\t{}\t{}\t{} / "#.format(wellname,oilrate,waterrate,gasrate)
    injhist    = " '{}'\tWATER\tOPEN\t{}\t7*\tRATE / "#.format(wellname,waterrate)
    wefac      = " '{}'\t{} / "#.format(wellname,efficiency)
    welopen    = " '{}'\tSHUT\t3* / "#.format(wellname)

    def __init__(self):

        pass

    def read(self):

        pass

    def _read(self):

        pass

    def set_subheaders(self,header_index=None,header=None,regex=None,regex_builtin="INC_HEADERS",title="SUB-HEADERS"):

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

    def get_wells(self,wellname=None):

        pass

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

class VTKit(DataFrame):

    def __init__(self):

        pass

    def read(self,):

        pass

    def _read(self):

        pass

    def write(self,):

        pass

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