# %%
"""
-------------------------------------------------------------------------------
  ***    *     *  ******   *******  ******    *****     ***    *     *  ******   
 *   *   **   **  *     *  *        *     *  *     *   *   *   **    *  *     *  
*     *  * * * *  *     *  *        *     *  *        *     *  * *   *  *     *  
*******  *  *  *  ******   ****     ******    *****   *******  *  *  *  *     *  
*     *  *     *  *        *        *   *          *  *     *  *   * *  *     *  
*     *  *     *  *        *        *    *   *     *  *     *  *    **  *     *  
*     *  *     *  *        *******  *     *   *****   *     *  *     *  ******   
-------------------------------------------------------------------------------
 * AmpersandCFD is a minimalist streamlined OpenFOAM generation tool.
 * Copyright (c) 2024 THAW TAR
 * All rights reserved.
 *
 * This software is licensed under the GNU General Public License version 3 (GPL-3.0).
 * You may obtain a copy of the license at https://www.gnu.org/licenses/gpl-3.0.en.html
 */
"""

from pathlib import Path
from src.services.mod_service import ModService
from src.models.inputs import FLUID_PYSICAL_PROPERTIES, ProjectInputModel, StlInputModel
from src.utils.data_input import AmpersandDataInput, IOUtils
from src.services.project_service import ProjectService


def create_project():
    
    parent_directory = IOUtils.ask_for_directory()
    project_name = IOUtils.get_input("Enter the project name: ")
    project_path = Path(f"{parent_directory}/{project_name}")

    IOUtils.print(f"Project path: {project_path}")

    project = ProjectService.create_project(project_path)

    IOUtils.print("Preparing for mesh generation")

    refinement_amount = AmpersandDataInput.get_mesh_refinement_amount()
    project.set_refinement_amount(refinement_amount)

    ModService.add_geometry(project)

    # Before creating the project files, the settings are flushed to the project_settings.yaml file

    is_internal_flow = IOUtils.get_input("Internal or External Flow (I/E)?: ").lower() == 'i'
    project.set_flow_type(is_internal_flow)

    if (not is_internal_flow):
        on_ground_type = IOUtils.get_input_bool("Is the ground touching the body (y/N): ")
        project.set_on_ground(on_ground_type)

    IOUtils.print( "Fluid properties and inlet values are necessary for mesh size calculations")

    fluid = AmpersandDataInput.choose_fluid_properties()
    project.set_fluid_properties(fluid)

    U = AmpersandDataInput.get_inlet_values()
    project.set_inlet_values(U)

    is_transient = IOUtils.get_input("Transient or Steady State (T/S)?: ").lower() == 't'

    if (is_transient):
        endTime = IOUtils.get_input_int("End time: ")
        writeInterval = IOUtils.get_input_int("Write interval: ")
        deltaT = IOUtils.get_input_int("Time step: ")
        project.set_transient_settings(is_transient, endTime, writeInterval, deltaT)
    else:
        project.set_is_transient(is_transient)




    n_core = IOUtils.get_input_int("Number of cores for parallel simulation: ")
    project.set_parallel(n_core)

    half_model = IOUtils.get_input_bool("Half Model (y/N)?: ")
    project.set_half_model(half_model)


    useFOs = IOUtils.get_input_bool(
        "Use function objects for post-processing (y/N)?: ")
    project.set_post_process_settings(useFOs)

    project.summarize_project()

    ProjectService.write_project(project)


def write_project(project_input: ProjectInputModel):
    IOUtils.print(f"Creating project at {project_input.project_path}")
    project = ProjectService.create_project(project_input.project_path)
    project.set_refinement_amount(project_input.refinement_amount)

    
    project.set_flow_type(project_input.is_internal_flow)
    if project_input.on_ground is not None:
        project.set_on_ground(project_input.on_ground)

    project.set_fluid_properties(project_input.fluid_properties)
    project.set_inlet_values(project_input.inlet_values)
    if not project_input.transient:
        project.set_is_transient(False)
    else:
        project.set_transient_settings(True, project_input.transient.end_time, project_input.transient.write_interval, project_input.transient.time_step)
    project.set_parallel(project_input.n_core)
    project.set_half_model(project_input.is_half_model)
    
    for stl_file in project_input.stl_files:
        ProjectService.add_stl_file(project, stl_file.stl_path, stl_file.property, stl_file.purpose)

    
    project.set_post_process_settings(project_input.use_function_objects)

    project.summarize_project()
    ProjectService.write_project(project)


if __name__ == '__main__':
    input = ProjectInputModel(
        project_path=Path("/workspaces/ampersandCFD/foamProjects/hello"),
        refinement_amount="fine",
        on_ground=False,
        fluid_properties=FLUID_PYSICAL_PROPERTIES["Air"],
        inlet_values=(600,0,0),
        n_core=4,
        is_half_model=True,
        is_internal_flow=False,
        use_function_objects=True,
        transient=False,
        stl_files=[
            StlInputModel(stl_path=Path("/workspaces/ampersandCFD/stl/ahmed.stl"), purpose="wall")
        ]
    )
    write_project(input)

# %%
