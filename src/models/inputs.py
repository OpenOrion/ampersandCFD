from pathlib import Path
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field
from src.models.settings import RefinementAmount, FluidProperties

PathLike = Union[str, Path]



FLUID_PYSICAL_PROPERTIES = {
    "Air": FluidProperties(rho= 1.225, nu= 1.5e-5),
    "Water": FluidProperties(rho= 1000, nu= 1e-6),
}

class StlInputModel(BaseModel):
    stl_path: PathLike
    purpose: str

class TransientSettings(BaseModel):
    end_time: int
    time_step: int
    write_interval: int


class ProjectInputModel(BaseModel):
    project_path: PathLike
    refinement_amount: RefinementAmount
    is_internal_flow: bool
    on_ground: Optional[bool] = None
    fluid_properties: FluidProperties
    inlet_values: tuple[float, float, float]
    transient: Union[Literal[False], TransientSettings]
    n_core: int
    is_half_model: bool
    use_function_objects: bool
    stl_files: list[StlInputModel] = Field(default_factory=list)


