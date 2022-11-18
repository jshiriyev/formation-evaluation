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
    import dirsetup

from cypy.vectorpy import strtype

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

    def __repr__(self,comment=None):

        return self.__str__(comment)

    def __str__(self,comment=None):

        if len(self)==1:
            return repr(tuple(self.fields))

        if comment is None:
            comment = ""

        fstring = comment
        
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

class dirview():

    def __init__(self,dirpath):

        self.dirpath = dirpath

    def draw(self,window,func=None):

        self.root = window

        self.scrollbar = tkinter.ttk.Scrollbar(self.root)

        self.tree = tkinter.ttk.Treeview(self.root,show="headings tree",selectmode="browse",yscrollcommand=self.scrollbar.set)

        self.tree.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.scrollbar.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.scrollbar.config(command=self.tree.yview)

        self.tree.bind("<Button-1>",lambda event: self.set_path(func,event))

        self.refill()

    def refill(self):

        self.tree.heading("#0",text="")

        self.tree.delete(*self.tree.get_children())

        iterator = os.walk(self.dirpath)

        parents_name = []
        parents_link = []

        counter  = 0

        while True:

            try:
                root,dirs,frames = next(iterator)
            except StopIteration:
                break

            if counter==0:
                dirname = os.path.split(root)[1]
                self.tree.heading("#0",text=dirname,anchor=tkinter.W)
                parents_name.append(root)
                parents_link.append("")
            
            parent = parents_link[parents_name.index(root)]

            for directory in dirs:
                link = self.tree.insert(parent,'end',iid=counter,text=directory)
                counter += 1

                parents_name.append(os.path.join(root,directory))
                parents_link.append(link)

            for file in frames:            
                self.tree.insert(parent,'end',iid=counter,text=file)
                counter += 1

    def set_path(self,func=None,event=None):

        if event is not None:
            region = self.tree.identify("region",event.x,event.y)
        else:
            return

        if region!="tree":
            return

        item = self.tree.identify("row",event.x,event.y)

        path = self.tree.item(item)['text']

        while True:

            item = self.tree.parent(item)

            if item:
                path = os.path.join(self.tree.item(item)['text'],path)
            else:
                path = os.path.join(self.dirpath,path)
                break

        if func is not None:
            func(path)
        else:
            print(path)

if __name__ == "__main__":

    import unittest

    from tests import textio_test

    unittest.main(textio_test)