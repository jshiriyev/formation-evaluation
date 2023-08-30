# BorePy

BorePy contains a set of modules used in integrated formation evaluation and reservoir performance monitoring. Test the commitments (python -m unittest discover -v).

**DATA ANALYSIS**

Petrophysics \# Core Analysis and Well Logging Interpretations

- Core Analysis
- Well log Analysis

Production \# Well Diary

- Well Test Analysis
- Decline Curve Analysis

**RESERVOIR MODELING**

GModel \# Geomodeling and Geostatistical Calculations:

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

FModel \# Fluid Modeling Reference: Tarek Ahmed chapter 2

- Compositional Fluid Model
- Modified Black Oil
- Black Oil
- Dead Oil
- Dry Gas
- Water

PorMed \# Reservoir Simulation:

- OnePhase, TwoPhase, ThreePhase Simulators. Reference: Balhoff's book

**BOREHOLE MODELING**

Geomechanical Modeling \# Geomechanical Modeling:

- **wstab:** Wellbore stability

Electromagnetic Modeling \# Electomagnetic Waves Modeling, conductivity measurements with induction logging tools:

- **AHM:** 2D wellbore conductivity simulation with axial hybrid method
- **SIE:** 2D plane simulation with surface integral equations
- **VIE:** 3D layer simulation volume integral equations