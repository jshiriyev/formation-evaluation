import contextlib
import copy
import datetime

from difflib import SequenceMatcher

import logging

import os
import re

import numpy
import openpyxl

from ._browser import Browser

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
