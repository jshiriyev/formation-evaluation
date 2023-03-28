import os,sys,json

filedir = os.path.dirname(__file__)

filepath = os.path.join(filedir,"_pphys.json")

with open(filepath,"r") as jsonfile:
    library = json.load(jsonfile)

from ._lasbrief import NanView
from ._lasbrief import TableView

from ._lasbatch import LasBatch

from ._bulkmodel import BulkModel

from ._depthview import DepthView
from ._depthview import DepthViewLasio #must be depreciated later once I fully prepare las file reader

from ._corrview import CorrView

from . import logan