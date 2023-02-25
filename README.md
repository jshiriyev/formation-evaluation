# BorePy

BorePy contains a set of modules used in integrated formation evaluation and reservoir performance monitoring. Test the commitments (python -m unittest discover -v).

SComp \# scientific computing

- arrays: Special, Curve, Bundle
- datum: Binary, Header, Raster
- regression: Linear, Correlation
- mlearn: 
- optimize: Root Find, Scalar (Univariate), Local (Multivariate), Global
- integrate: Gauss
- interpolate: 
- mesh: line, rectangle, ellipse, cuboid, cylinder, sphere

TextIO \# Text Input and Output

- Browser
- TxtFile
- XlSheet
- XlBook

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
- Gstats: heterogeneity, variogram, kriging, simulation

Agenda \# Well Agenda

- TimeCurve
- Completion
- Production
- Schedule
- TimeView
- WorkFlow: allocate, 

PetroPhysics \#

- LasCurve
- LasFile
- LasBrief
- LasBatch
- BulkModel
- DepthView
- CrossView
- WorkFlow

WellTest \#

- WorkFlow

Fluid \# Reference: Tarek Ahmed chapter 2

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

Subjects \# Subjects to Study:

- data structures and algorithms, spatial arrays
- software development fundamentals (python packaging, git, bash, shell)
- vtk file format
- database SQL, sqlite
- data analysis (statistics)
- machine learning