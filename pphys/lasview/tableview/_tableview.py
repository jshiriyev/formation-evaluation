import re

import lasio

from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

from matplotlib.backends.backend_pdf import PdfPages

from matplotlib.patches import Polygon
from matplotlib.patches import Rectangle

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import LogLocator
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy

class TableView():

    def __init__(self,lasfile,**kwargs):

        super().__init__(**kwargs)

        self.lasfile = lasfile

    def set_rows(self,fstring=None):

        if fstring is None:
            fstring = "{}"

        rows = []

        for curve in self.lasfile.curves:

            row = []

            top,bottom = self.get_limits(curve.data)

            row.append(fstring.format(self.lasfile[0][top]))

            row.append(fstring.format(self.lasfile[0][bottom]))

            row.append(curve.descr)

            rows.append(row)

        self.rows = rows

    def set_axis(self,axis=None,caption=False):

        self.show = True if axis is None else False

        if axis is None:

            self.figure = pyplot.figure()

            axis = self.figure.add_subplot()

        self.axis = axis

    def set_caption(self,axis,filename):

        axis.set_xlim((0,1))
        axis.set_ylim((0,1))

        axis.get_xaxis().set_visible(False)
        axis.get_yaxis().set_visible(False)

        axis.set_axis_off()

        axis.text(0.5,0.5,filename,
            horizontalalignment='center',
            verticalalignment='center',
            transform=axis.transAxes)

    def set_size(self,numlinechar=None):

        nrows = 0

        ncols = 10

        xticks = [0,1,2,3,ncols]
        yticks = [nrows]

        for row in reversed(self.rows):

            row[2],subrows = self.set_descr(row[2],numlinechar)

            nrows += subrows

            yticks.append(nrows)

        else:
            nrows += 2
            
            yticks.append(nrows)

        self.axis.set_xlim((0,ncols))
        self.axis.set_ylim((0,nrows))

        self.axis.set_axis_off()

        self.nrows = nrows
        self.ncols = ncols

        self.xticks = xticks
        self.yticks = yticks

    def set_descr(self,descr,numlinechar=None):

        descr = re.sub(' +',' ',descr)
        descr = re.sub('\n',' ',descr)

        descr = descr.strip()

        if numlinechar is None:
            return descr,1

        subrows_temp = len(descr)//numlinechar+1

        for index in range(1,subrows_temp):
            space_index = descr.find(" ",numlinechar*index,numlinechar*(index+1))

            if space_index!=-1:

                descr = list(descr)
                descr[space_index] = '\n'
                descr = "".join(descr)

        subrows = descr.count("\n")+1

        return descr,subrows
    
    def set_table(self):

        heads = list(reversed(self.lasfile.keys()))

        for index,row in enumerate(reversed(self.rows)):

            ysize = self.yticks[index+1]-self.yticks[index]

            self.axis.annotate(
                xy=(0.95,self.yticks[index]+ysize/2),
                text=heads[index],
                ha='right',va='center'
            )
            self.axis.annotate(
                xy=(1.5,self.yticks[index]+ysize/2),
                text=row[0],
                ha='center',va='center'
            )
            self.axis.annotate(
                xy=(2.5,self.yticks[index]+ysize/2),
                text=row[1],
                ha='center',va='center'
            )
            self.axis.annotate(
                xy=(3.05,self.yticks[index]+ysize/2),
                text=row[2],
                ha='left',va='center'
            )

    def set_header(self):

        self.axis.annotate(
            xy=(0.95,self.nrows-1),
            text='Curves',
            weight='bold',
            ha='right',va='center'
        )
        self.axis.annotate(
            xy=(1.5,self.nrows-1),
            text='Top',
            weight='bold',
            ha='center',va='center'
        )
        self.axis.annotate(
            xy=(2.5,self.nrows-1),
            text='Bottom',
            weight='bold',
            ha='center',va='center'
        )
        self.axis.annotate(
            xy=(3.05,self.nrows-1),
            text='Description',
            weight='bold',
            ha='left',va='center'
        )

    def set_lines(self):

        self.axis.plot(self.axis.get_xlim(),
            [self.nrows,self.nrows],lw=1.5,color='black',marker='',zorder=4)
        
        self.axis.plot(self.axis.get_xlim(),
            [0,0],lw=1.5,color='black',marker='',zorder=4)

        for index in self.yticks[1:-1]:
            self.axis.plot(self.axis.get_xlim(),
                [index,index],lw=1.15,color='gray',ls=':',zorder=3,marker='')

    def view(self,**kwargs):

        self.set_rows(fstring=pop(kwargs,"fstring"))
        self.set_axis(axis=pop(kwargs,"axis"))

        # self.set_caption()

        self.set_size(numlinechar=pop(kwargs,"numlinechar",40))
        self.set_table()
        self.set_header()
        self.set_lines()

        pyplot.tight_layout()

        if self.show:
            pyplot.show()

    def save(self,filepath,sizemult=0.4,**kwargs):

        self.set_rows(fstring=pop(kwargs,"fstring"))
        self.set_axis()

        # self.set_caption()

        self.set_size(numlinechar=pop(kwargs,"numlinechar",40))
        self.set_table()
        self.set_header()
        self.set_lines()

        self.figure.set_figwidth(sizemult*2*self.ncols)

        self.figure.set_figheight(sizemult*self.nrows)

        pyplot.tight_layout()

        self.figure.savefig(filepath)

        pyplot.close()

    @staticmethod
    def get_limits(array):

        isnotnan = ~numpy.isnan(array)

        index_top = numpy.argmax(isnotnan)

        index_bottom = array.size-numpy.argmax(numpy.flip(isnotnan))-1

        return index_top,index_bottom

    @property
    def wellname(self):

        return self.lasfile.well['WELL'].value