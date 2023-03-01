# BorePy

BorePy contains a set of modules used in integrated formation evaluation and reservoir performance monitoring. Test the commitments (python -m unittest discover -v).

SComp \# scientific computing

- interpolate: 
- integrate: Gauss
- optimize: Root Find, Scalar (Univariate), Local (Multivariate), Global
- regression: Linear, Correlation
- mlearn: 

TextIO \# Text Input and Output

- Array: Special, Curve, Frame
- Datum: Binary, Header, Raster
- Browser: 
- TxtFile: 
- XlBook: 
- LasFile: 
- Schedule:
- vtk file format

DataBase Management

PetroPhysics \# Core Analysis and Well Logging Interpretations

- LasBrief
- LasBatch
- BulkModel
- DepthView
- CorrView
- WorkFlow

WellTest \#

- WorkFlow

Diary \# Well Diary

- Completion
- Production
- TimeView
- WorkFlow: allocate

FluidModel \# Reference: Tarek Ahmed chapter 2

- Compositional Fluid Model
- Modified Black Oil
- Black Oil
- Dead Oil
- Dry Gas
- Water

GeoModel \# Elements of GeoModel:

- Items: Slot, Zone, Fault, Fracture, Segment
- Survey: 
- Diagram: 
- Stock: 
- Surface:
- Fractures: 
- Faults: 
- Formation: 
- Reservoir: 
- Mbal:
- Mesh: line, rectangle, ellipse, cuboid, cylinder, sphere
- Gstats: heterogeneity, variogram, kriging, simulation

Flow \# Fluid FLow Modeling:

- **Plates:** flow including plates, falling film, parallel plates with stationary plates, parallel plates with one moving plate
- **Orifice:** flow through orifice, nozzle
- **Pipes:** one and two phase flow
- **PorScale:** pore scale flow
- **PorMed:** OnePhase, TwoPhase, ThreePhase. Reference: Balhoff's book

GMech \# Geomechanical Modeling:

- **ppest:** Pore Pressure Estimation
- **wstab:** Wellbore stability
- **sandprod:** Sand Production
- **hfprop:** Hydraulic Fracture Propagation

EMW \# Electomagnetic Waves Modeling, conductivity measurements with induction logging tools:

- **AHM:** 2D wellbore conductivity simulation with axial hybrid method
- **SIE:** 2D plane simulation with surface integral equations
- **VIE:** 3D layer simulation volume integral equations