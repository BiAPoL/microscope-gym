'''Microscope objective class.

Since the objective does not have any methods, it is not implemented as an interface, but as a real class.'''
from pydantic import BaseModel, Field


class Objective(BaseModel):
    '''Microscope objectiveb data class.'''
    name: str = Field(..., description="name of the objective")
    magnification: float = Field(..., description="magnification factor")
    working_distance: float = Field(..., description="working distance in mm")
    numerical_aperture: float = Field(...,
                                      description="numerical aperture - NA = sin(θ) (θ = half angle of cone of light captured by objective)")
    immersion: str = Field(..., description="immersion medium (e.g. 'air', 'oil', 'water', 'glycerol', 'silicone oil')")
