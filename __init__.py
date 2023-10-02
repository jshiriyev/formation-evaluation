from .bhole import pphys
from .bhole import wtest
from .bhole import gmech
from .bhole import emsim

from . import prodn

from . import fmodel

from . import matbal

from . import gmodel
from . import pormed

from . import frame

from .frame.curve.array._ints import ints
from .frame.curve.array._floats import floats
from .frame.curve.array._strs import strs
from .frame.curve.array._dates import dates
from .frame.curve.array._times import times
from .frame.curve.array._datetimes import datetimes

from .frame.curve._linear import linear
from .frame.curve._curve import curve
from .frame.curve._udist import udist
from .frame.curve._utime import utime

from .frame._header import Header
from .frame._batch import Batch
from .frame._raster import Raster
from .frame._bundle import Bundle
from .frame._spatial import Spatial

from ._browser import Browser

from ._txtfile import TxtFile, loadtxt

from ._xlbook import XlBook, loadxl

aze_cyrilic_lower = [
    "а","б","ҹ","ч","д","е","я","ф","ҝ","ғ","һ","х","ы","и","ж","к",
    "г","л","м","н","о","ю","п","р","с","ш","т","у","ц","в","й","з"]

aze_latin_lower = [
    "a","b","c","ç","d","e","ə","f","g","ğ","h","x","ı","i","j","k",
    "q","l","m","n","o","ö","p","r","s","ş","t","u","ü","v","y","z"]

aze_cyrilic_upper = [
    "А","Б","Ҹ","Ч","Д","Е","Я","Ф","Ҝ","Ғ","Һ","Х","Ы","И","Ж","К",
    "Г","Л","М","Н","О","Ю","П","Р","С","Ш","Т","У","Ц","В","Й","З"]

aze_latin_upper = [
    "A","B","C","Ç","D","E","Ə","F","G","Ğ","H","X","I","İ","J","K",
    "Q","L","M","N","O","Ö","P","R","S","Ş","T","U","Ü","V","Y","Z"]