import contextlib
import copy
import datetime

from difflib import SequenceMatcher

import logging

import os
import re

import numpy
import openpyxl

from .folder._browser import Browser

class XlSheet(Browser):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

    def write(self,filepath,title):

        wb = openpyxl.Workbook()

        sheet = wb.active

        if title is not None:
            sheet.title = title

        for line in running:
            sheet.append(line)

        wb.save(filepath)

class XlBook(Browser):

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

            dataframe = loadbook(filepath,**kwargs)

            self.frames.append(dataframe)

            logging.info(f"Loaded {filepath} as expected.")

    def merge(self,cols=None,idframes=None,infosearch=False):
        """It merges all the frames as a single frame under the Excel class."""

        framemerged = frame()

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
                datacolumns = [datacolumn for datacolumn in dataframe.running]
            elif not infosearch:
                datacolumns = []
                for index in tuple(cols):
                    if type(index) is int:
                        datacolumns.append(dataframe.running[index])
                    elif type(index) is str:
                        datacolumns.append(dataframe[index])
                    else:
                        raise TypeError(f"cols type should be either int or str, not {type(index)}")
            else:
                datacolumns = []
                for index in tuple(cols):
                    if type(index) is str:
                        scores = [SequenceMatcher(None,info,index).ratio() for info in frame.infos]
                        datacolumns.append(dataframe.running[scores.index(max(scores))])
                    else:
                        raise TypeError(f"cols type should be str, not {type(index)}")

            framemerged._append(*datacolumns)

        return framemerged

def loadxl(filepath,sheetname=None,**kwargs):

    pass

class XlWorm():

    def __init__(self,filepath,homedir=None,filedir=None,**kwargs):

        with xlbatch.xlopen(filepath) as book:

            for sheet in sheets:

                print("Loading {} {}".format(filepath,sheet))

                dataframe = self.load(book,sheet,**kwargs)

                self.frames.append(dataframe)

    def load(self,book,sheet,sheetsearch=False,min_row=1,min_col=1,max_row=None,max_col=None,hrows=0):
        """It reads provided excel worksheet and returns it as a frame."""

        dataframe = frame()

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
                datacolumn = column(col[hrows:],head=heads_[index],info=info)
                dataframe._setup(datacolumn)

        return dataframe

    @contextlib.contextmanager
    def xlopen(filepath):
        xlbook = openpyxl.load_workbook(filepath,read_only=True,data_only=True)
        try:
            yield xlbook
        finally:
            xlbook._archive.close()