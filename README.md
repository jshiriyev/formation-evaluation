# BorePy

BorePy contains a set of modules used in integrated formation evaluation and reservoir performance monitoring. Test the commitments (python -m unittest discover -v).

SComp \# scientific computing

- arrays: Special, Curve, Bundle
- datum: BST, Spatial
- stats: Heterogeneity, Correlation, Hypothesis, Data Analysis WorkFLow
- optimize: RootFind, Univariate, Multivariate
- regression: Linear, 
- integrate: Gauss
- mesh: line, rectangle, ellipse, cuboid, cylinder, sphere
- gstats: variogram, kriging simple and ordinary, sequential gaussian simulation

TextIO \# Text Input and Output

- Header
- Browser
- TxtFile
- XlSheet
- XlBook

GeoModel \# Elements of GeoModel:

- Items: Slot, Zone, Fault, Fracture, Segment
- Survey
- Diagram
- Stock
- Surface
- Formation
- Reservoir

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
- LasBatch
- BulkModel
- DepthView
- BatchView
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