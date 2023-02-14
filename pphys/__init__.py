import os,sys,json

filedir = os.path.dirname(__file__)

filepath = os.path.join(filedir,"_pphys.json")

with open(filepath,"r") as jsonfile:
    library = json.load(jsonfile)

from ._lascurve import LasCurve
from ._lasfile import LasFile
from ._lasbatch import LasBatch
from ._bulkmodel import BulkModel

from ._depthview import DepthView
from ._depthview import DepthViewLasio #must be depreciated later once I fully prepare las file reader

from ._nanview import NanView #must be merged to lasfile later once I fully prepare las file reader

from ._batchview import BatchView

from ._batchsummary import WellSummary

from .wlogs import algorithms

# from ._workflow import WorkFlow

def pop(kwargs,key,default=None):

    try:
        return kwargs.pop(key)
    except KeyError:
        return default