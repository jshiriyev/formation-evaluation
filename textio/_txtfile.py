import contextlib
import copy
import datetime

from difflib import SequenceMatcher

import logging

import os
import re

import numpy

from ._browser import Browser

class TxtFile(Browser):

    def __init__(self,dataframe=None,**kwargs):

        super().__init__(**kwargs)

        if dataframe is None:
            self.frame = frame()
        else:
            self.frame = dataframe

        # self.header = header(
        #     heads=self.frame.heads,
        #     units=self.frame.units,
        #     infos=self.frame.infos,
        #     )

    def write(self,filepath,comment=None,**kwargs):
        """It writes text form of frame."""

        if comment is None:
            comment = "# "

        with open(filepath,"w",encoding='utf-8') as txtmaster:

            txtmaster.write(self.header.__str__(comment=comment))
            txtmaster.write(f"{comment}\n")
            txtmaster.write(self.frame.__str__(limit=self.frame.shape[0],comment=comment,**kwargs))

        # numpy.savetxt("data.txt",Z,fmt="%s",header=header,footer=footer,comments="")

    def writeb(self,filepath):
        """It writes binary form of frame."""

        for header,datacolumn in zip(self._headers,self._running):
            kwargs[header] = datacolumn

        numpy.savez_compressed(filepath,**kwargs)

        # numpy.savez_compressed('data.npz', a=A, b=B, c=C)

def loadtxt(filepath,**kwargs):
    """
    Returns an instance of textio.txtfile for the given filepath.
    
    Arguments:
        filepath {str} -- path to the given txt file

    Keyword Arguments:
        homedir {str} -- path to the home (output) directory
        filedir {str} -- path to the file (input) directory
    
    Returns:
        textio.txtfile -- an instance of textio.txtfile filled with LAS file text.

    """

    # It creates an empty textio.txtfile instance.
    nullfile = txtfile(filepath=filepath,**kwargs)

    # It reads LAS file and returns textio.lasfile instance.
    return txtworm(nullfile).item

class TxtWorm():

    def __init__(self,filepath,headline=None,comments="#",delimiter=None,skiprows=0):

        self.headline   = headline
        self.comments   = comments
        self.delimiter  = delimiter
        self.skiprows   = skiprows
        
        with loadtxt.textopen(filepath) as filemaster:
            dataframe = self.text(filemaster)

        self.frame = dataframe

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

        return strtype(row)

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

        return frame(*running)

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

