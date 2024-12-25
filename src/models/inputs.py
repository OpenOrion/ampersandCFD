from pathlib import Path
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field
from src.models.settings import RefinementAmount, FluidProperties, PatchType, PatchProperty, TransientInput

PathLike = Union[str, Path]



FLUID_PYSICAL_PROPERTIES = {
    "Air": FluidProperties(rho= 1.225, nu= 1.5e-5),
    "Water": FluidProperties(rho= 1000, nu= 1e-6),
}

class StlInput(BaseModel):
    stl_path: PathLike
    purpose: PatchType
    property: Optional[PatchProperty] = None


class CreateProjectInput(BaseModel):
    refinement_amount: RefinementAmount
    is_internal_flow: bool
    on_ground: Optional[bool] = None
    fluid: FluidProperties
    inlet_values: tuple[float, float, float]
    transient: Union[Literal[False], TransientInput]
    n_core: int
    is_half_model: bool
    use_function_objects: bool
    stl_files: list[StlInput] = Field(default_factory=list)

