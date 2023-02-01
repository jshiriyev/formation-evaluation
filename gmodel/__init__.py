import os,sys,json

filedir = os.path.dirname(__file__)

wellspath = os.path.join(filedir,"_wells.json")

with open(wellspath,"r") as wellsfile:
    json_wells = json.load(wellsfile)

zonespath = os.path.join(filedir,"_zones.json")

with open(zonespath,"r") as zonesfile:
    json_zones = json.load(zonesfile)

from ._items import Slot
from ._items import Zone
from ._items import Fault
from ._items import Fracture
from ._items import Segment

from ._wellsurvey import Survey
from ._welldiagram import Diagram
from ._wellstock import Stock
from ._formation import Formation
from ._faultsystem import FaultSystem
from ._fracturenetwork import FractureNetwork
from ._reservoir import Reservoir