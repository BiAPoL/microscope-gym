# how might this work?

```
from microscopegym.micromanager import .... ?
```

long term: installable packages

`pip install microscope-gym-micromanager`

## 1st approach

```python
from microscope_gym_micromanager import microscope_factory
required_components = ['camera', 'stage', 'laser_cutter', 'objectives', 'lasers', 'filters']
my_microscope = microscope_factory(required_components)

```
*then* factory initializes components as below in 2nd approach and returns a Microscope object
components are attributes of microscope object
or...???

## 2nd approach:

```python
from microscope_gym.interface import Objective, Microscope, Axis, Camera, CameraSettings, Stage, microscope_handler_factory
my_handler = microscope_handler_factory()
my_objective = Objective(my_handler)
my_stage = Stage(my_handler)
my...etc
```
if 2nd option, how we initialize the components (Objective, Stage, Camera, etc)  becomes part of api init fxn signature becomes part of api
if 1st (microscope factory creates microscope object) then only the microscope is part of public interfacee (and some public methods of components -- objectve, stage, etc).
    