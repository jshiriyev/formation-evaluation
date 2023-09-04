import os,sys,json

filedir = os.path.dirname(__file__)

filepath = os.path.join(filedir,"_pphys.json")

with open(filepath,"r") as jsonfile:
    library = json.load(jsonfile)

from dataclasses import dataclass

from ._lasbrief import NanView
from ._lasbrief import TableView

from ._lasbatch import LasBatch

from ._bulkmodel import BulkModel

from ._depthview import DepthView
from ._depthview import DepthViewLasio #must be depreciated later once I fully prepare las file reader

from ._corrview import CorrView

from . import logan

@dataclass
class Archie:
    """It is an Archie's parameter dictionary."""
    a  : float = 1.00 # tortuosity constant
    m  : float = 2.00 # cementation exponent
    n  : float = 2.00 # saturation exponent

    def ffactor(self,porosity):
        """Calculates formation factor based on Archie's equation."""
        return self.a/(porosity**self.m)

    def saturation(self,porosity,rwater,rtotal):
        """Calculates water saturation based on Archie's equation."""
        return self.ffactor(porosity)*rwater/rtotal