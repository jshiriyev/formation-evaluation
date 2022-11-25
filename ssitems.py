import calendar

from datetime import datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta

import os
import re

import warnings

import numpy as np

if __name__ == "__main__":
    import dirsetup

from geometries import Rectangle
from geometries import Ellipse
from geometries import Cuboid 
from geometries import Cylinder

class PoreRock():

    def __init__(self,*args,workdir=None,**kwargs):

        super().__init__(*args,**kwargs)

        if workdir is None:
            self.workdir = workdir

    def set_depth(self,depth):

        self.depth = depth

    def set_porosity(self,porosity,homogeneous=True,X=None,Y=None,Z=None):

        if isinstance(porosity,float):
            porosity = np.array([porosity])
        elif isinstance(porosity,int):
            porosity = np.array([porosity])
        elif isinstance(porosity,tuple):
            porosity = np.array(porosity)

        if homogeneous and self.gridFlag:
            self.porosity = np.ones(self.grid_numtot)*porosity
        else:
            self.porosity = porosity

    def set_permeability(self,permeability,isotropy=True,homogeneous=True,X=None,Y=None,Z=None):

        if isinstance(permeability,float):
            permeability = np.array([permeability])
        elif isinstance(permeability,int):
            permeability = np.array([permeability])
        elif isinstance(permeability,tuple):
            permeability = np.array(permeability)

        if homogeneous and isotropy:

            if self.gridFlag:
                self.permeability = np.ones((self.grid_numtot,3))*permeability
            else:
                self.permeability = permeability
            
        elif not homogeneous and isotropy:
            
            self.permeability = np.repeat(permeability,3).reshape((-1,3))
            
        elif homogeneous and not isotropy:
            
            if self.gridFlag:
                self.permeability = np.repeat(permeability,self.grid_numtot).reshape((3,-1)).T
            else:
                self.permeability = permeability
            
        elif not homogeneous and not isotropy:
            
            self.permeability = permeability

    def set_compressibility(self,compressibility):

        self.compressibility = compressibility

    def get_tops(self,formations,wellname=None):

        pass

    def vtkwrite(res,frac,well,time,sol):
        
        # % deleteing files in results file
        # delete 'results\*.fig'
        # delete 'results\*.vtk'

        # % writing time values
        # for j = 1:time.numTimeStep

        # fid = fopen(['results\fracPressure',num2str(j),'.vtk'],'w');

        # fprintf(fid,'# vtk DataFile Version 1.0\r\n');
        # fprintf(fid,'FRACTURE FLOW ANALYTICAL SOLUTION\r\n');
        # fprintf(fid,'ASCII\r\n');

        # fprintf(fid,'\r\nframe UNSTRUCTURED_GRID\r\n');

        # fprintf(fid,'\r\nPOINTS %d FLOAT\r\n',frac.numAnode*2);

        # for i = 1:frac.numAnode
        #     fprintf(fid,'%f %f %f\r\n',frac.nodeCoord(i,:));
        # end

        # for i = 1:frac.numAnode
        #     fprintf(fid,'%f %f %f\r\n',[frac.nodeCoord(i,1:2),0]);
        # end

        # fprintf(fid,'\r\nCELLS %d %d\r\n',frac.numAfrac,5*frac.numAfrac);

        # for i = 1:frac.numAfrac
        #     fprintf(fid,'%d %d %d %d %d\r\n',[4,frac.map(i,:)-1,frac.map(i,:)+frac.numAnode-1]);
        # end

        # fprintf(fid,'\r\nCELL_TYPES %d\r\n',frac.numAfrac);

        # for i = 1:frac.numAfrac
        #     fprintf(fid,'%d\r\n',8);
        # end

        # fprintf(fid,'\r\nCELL_DATA %d\r\n',frac.numAfrac);
        # fprintf(fid,'SCALARS pressure float\r\n');
        # fprintf(fid,'LOOKUP_TABLE default\r\n');

        # for i = 1:frac.numAfrac
        #     fprintf(fid,'%f\r\n',sol.pressure(i,j));
        # end

        # fclose(fid);

        # end

        pass

    def drawmap(self,axis):

        # axis.scatter3D(*self.edge_vertices.T)

        # for line in self.boundaries:
        #     axis.plot3D(*line,color='grey')

        # axis.scatter3D(*self.grid_centers.T)

        # axis.set_box_aspect(self.lengths)

        # axis.set_axis_off()
        # plt.axis("off")
        
        # function node(frac,prop)
            
        #     switch nargin
        #         case 1
        #             plot(frac.nodeCoord(:,1),frac.nodeCoord(:,2),'.');
        #         case 2
        #             plot(frac.nodeCoord(:,1),frac.nodeCoord(:,2),'.',prop);
        #     end
            
        # end
        
        # function fracture(frac,prop)
            
        #     switch nargin
        #         case 1
        #             plot([frac.point1.Xcoord,frac.point2.Xcoord]',...
        #                  [frac.point1.Ycoord,frac.point2.Ycoord]');
        #         case 2
        #             plot([frac.point1.Xcoord,frac.point2.Xcoord]',...
        #                  [frac.point1.Ycoord,frac.point2.Ycoord]',prop);
        #     end
            
        # end
        
        # function well(frac,well,prop)
            
        #     switch nargin
        #         case 2
        #             plot(frac.center.Xcoord(well.wellID),...
        #                  frac.center.Ycoord(well.wellID),'x');
        #         case 3
        #             plot(frac.center.Xcoord(well.wellID),...
        #                  frac.center.Ycoord(well.wellID),'x',prop);
        #     end
            
        # end
        
        # function pressure1D(obs,pressure,time)
            
        #     time.snapTime = time.snapTime/inpput.convFactorDetermine('time');
            
        #     if length(unique(obs.Xcoord))>1
        #         xaxis = obs.Xcoord;
        #     elseif length(unique(obs.Ycoord))>1
        #         xaxis = obs.Ycoord;
        #     end
            
        #     figName = 'Reservoir Pressure';
            
        #     figure('Name',figName,'NumberTitle','off')
            
        #     plot(xaxis,pressure); hold on
            
        #     xlim([min(xaxis),max(xaxis)]);
        #     ylim([2000,4500]);
            
        #     xlabel('distance [m]');
        #     ylabel('pressure [psi]');
            
        #     legend('0.1 day','10 day','1000 day','Location','SouthEast');
            
        #     savefig(gcf,['results/',figName,'.fig'])
        #     close(gcf)
            
        # end
            
        # function pressure2D(obs,pressure,frac,time,interp)
            
        #     time.snapTime = time.snapTime/inpput.convFactorDetermine('time');
            
        #     for i = 1:time.numSnaps
                
        #         switch nargin
        #             case 4
        #                 OBS = obs;
        #                 vq = reshape(pressure(:,i),obs.Ynum,obs.Xnum);
        #             case 5
        #                 OBS = plotAll.calc2Dnodes(...
        #                     [min(obs.Xcoord),max(obs.Xcoord),interp(1)],...
        #                     [min(obs.Ycoord),max(obs.Ycoord),interp(2)]);
        #                 vq = griddata(obs.Xcoord,obs.Ycoord,pressure(:,i),...
        #                       OBS.Xcoord,OBS.Ycoord,'natural');
        #                 vq = reshape(vq,OBS.Ynum,OBS.Xnum);
        #         end
            
        #         figName = ['time ',num2str(time.snapTime(i)),' days'];

        #         figure('Name',figName,'NumberTitle','off')

        #         imagesc(OBS.Xcoord,OBS.Ycoord,vq);

        #         set(h,'EdgeColor','none');
        #         shading interp

        #         colormap(jet)
        #         colorbar
        #         caxis([2000,4200])

        #         xlim([min(OBS.Xcoord),max(OBS.Xcoord)]);
        #         ylim([min(OBS.Ycoord),max(OBS.Ycoord)]);

        #         hold on

        #         prop.Color = 'w';
        #         prop.Linethickness = 1;

        #         plotAll.fracture(frac,prop);

        #         savefig(gcf,['results/',figName,'.fig'])
                
        #         close(gcf)
            
        #     end
                
        # end
        
        # function obs = calc1Dnodes(Lmin,Lmax,Ndata)
            
        #     switch nargin
        #         case 1
        #             obs.num = 1;
        #             obs.range = Lmin;
        #         case 2
        #             obs.num = 20;
        #             obs.range = linspace(Lmin,Lmax,obs.num);
        #         case 3
        #             obs.num = Ndata;
        #             obs.range = linspace(Lmin,Lmax,obs.num);
        #     end
            
        # end
        
        # function obs = calc2Dnodes(X,Y)
            
        #     % xnum and ynum are the number of nodes
        #     % number of elements = number of nodes - 1
            
        #     if length(X) == 1
        #         XX = plotAll.calc1Dnodes(X(1));
        #     elseif length(X) == 2
        #         XX = plotAll.calc1Dnodes(X(1),X(2));
        #     elseif length(X) == 3
        #         XX = plotAll.calc1Dnodes(X(1),X(2),X(3));
        #     end
            
        #     if length(Y) == 1
        #         YY = plotAll.calc1Dnodes(Y(1));
        #     elseif length(Y) == 2
        #         YY = plotAll.calc1Dnodes(Y(1),Y(2));
        #     elseif length(Y) == 3
        #         YY = plotAll.calc1Dnodes(Y(1),Y(2),Y(3));
        #     end
            
        #     [Xmat,Ymat] = meshgrid(XX.range,YY.range);
            
        #     obs.Xnum = XX.num;
        #     obs.Ynum = YY.num;
            
        #     obs.Xcoord = Xmat(:);
        #     obs.Ycoord = Ymat(:);
        #     obs.Zcoord = ones((XX.num)*(YY.num),1);
            
        # end
        
        # function pressure = calcPressure(sol,res,time,green)
            
        #     gterm = green*time.deltaTime;
            
        #     pressure = zeros(size(green,1),time.numSnaps);
            
        #     for i = 1:time.numSnaps
                
        #         P = res.initPressure-...
        #          solver.convolution(gterm,sol.fracflux,1,time.idxSnapTime(i));
                
        #         pressure(:,i) = P/inpput.convFactorDetermine('pressure');
        pass

class Fractures():

    # % The fracture segment is defined as a plane joining two node points
    # % (point1 and point2). The heigth of fracture plane is taken the same
    # % as reservoir thickness (it is not diffcult to model shorter planes).
    # % z-coordinate of the points is given as the reservoir depth.

    # fileDir
    # nodeCoord
    # map
    # permeability
    # thickness
    # fracID
    # nodeID
    # numAfrac
    # numAnode
    # conductivity
    # point1
    # point2
    # Length
    # areatoreservoir
    # areatofracture
    # volume
    # center
    # signX
    # signY
    # azimuth

    def __init__(self):

        super().__init__()

        pass

class View3D():

    def __init__(self,window,**kwargs):

        super().__init__(**kwargs)

        self.dirname = os.path.dirname(__file__)

        self.root = window

    def set_plot(self):

        self.pane_EW = tkinter.ttk.PanedWindow(self.root,orient=tkinter.HORIZONTAL)

        self.frame_side = tkinter.ttk.Frame(self.root)

        self.pane_EW.add(self.frame_side,weight=1)

        self.frame_plot = tkinter.ttk.Frame(self.root)

        self.pane_EW.add(self.frame_plot,weight=1)

        self.pane_EW.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.frame_plot.columnconfigure(0,weight=1)
        self.frame_plot.columnconfigure(1,weight=0)

        self.frame_plot.rowconfigure(0,weight=1)
        self.frame_plot.rowconfigure(1,weight=0)

        self.figure = pyplot.Figure()
        self.canvas = FigureCanvasTkAgg(self.figure,self.frame_plot)

        self.plotbox = self.canvas.get_tk_widget()
        self.plotbox.grid(row=0,column=0,sticky=tkinter.NSEW)        

        self.plotbar = VerticalNavigationToolbar2Tk(self.canvas,self.frame_plot)
        self.plotbar.update()
        self.plotbar.grid(row=0,column=1,sticky=tkinter.N)

        self.itembox = AutocompleteEntryListbox(self.frame_side,height=250,padding=0)

        self.itembox.content = self.itemnames.tolist()
        self.itembox.config(completevalues=self.itembox.content,allow_other_values=True)

        self.itembox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_object(event))

        self.itembox.pack(expand=1,fill=tkinter.BOTH)

    def set_object(self,event):

        pass

if __name__ == "__main__":

    pass

    # import unittest

    # from tests import pipes
    # from tests import formations
    # from tests import fractures
    # from tests import wells

    # unittest.main(pipes)
    # unittest.main(formations)
    # unittest.main(fractures)
    # unittest.main(wells)
