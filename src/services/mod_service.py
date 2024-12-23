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


from typing import Literal
from src.models.settings import BoundingBox, Domain
from src.utils.data_input import AmpersandDataInput, IOUtils
from src.project import AmpersandProject
from src.utils.stl_analysis import StlAnalysis

ModificationType = Literal["Background Mesh", "Mesh Point", "Add Geometry", "Refinement Levels", "Boundary Conditions", "Fluid Properties", "Numerical Settings", "Simulation Control Settings", "Turbulence Model", "Post Processing Settings"]

# A collection of functions that are used to modify the project
class ModService:
    @staticmethod
    def modify_project(project: AmpersandProject, modification_type: ModificationType):
        if modification_type == "Background Mesh":
            ModService.change_background_mesh(project)
        elif modification_type == "Mesh Point":
            ModService.change_mesh_point(project)
        elif modification_type == "Add Geometry":
            ModService.add_geometry(project)
        elif modification_type == "Refinement Levels":
            ModService.change_refinement_levels(project)
        elif modification_type == "Boundary Conditions":
            ModService.change_boundary_conditions(project)
        elif modification_type == "Fluid Properties":
            ModService.change_fluid_properties(project)
        elif modification_type == "Numerical Settings":
            ModService.change_numerical_settings(project)
        elif modification_type == "Simulation Control Settings":
            ModService.change_simulation_settings(project)
        elif modification_type == "Turbulence Model":
            ModService.change_turbulenc_model(project)
        elif modification_type == "Post Processing Settings":
            ModService.change_post_process_settings(project)
        
        raise ValueError("Invalid option. Aborting operation")


    @staticmethod
    # this is to change the global refinement level of the mesh
    def change_macro_refinement_level(project: AmpersandProject):
        ref_amounts = ["coarse", "medium", "fine"]
        IOUtils.print(f"Current refinement level: {ref_amounts[project.settings.mesh.refAmount]}")
        ref_amount_index = IOUtils.get_input_int("Enter new refinement level (0:coarse, 1:medium, 2:fine): ")
        if (ref_amount_index < 0 or ref_amount_index > 2):
            IOUtils.print("Invalid refinement level, please enter the value again")
            ModService.change_refinement_levels(project)
        project.settings.mesh.refAmount = ref_amounts[ref_amount_index]

    @staticmethod
    def change_domain_size(project: AmpersandProject, bounds: BoundingBox):
        IOUtils.print(f"Domain size: {bounds.size} m")
        project.settings.mesh.domain = Domain.update(project.settings.mesh.domain, bounds)
        
    @staticmethod
    def change_mesh_size(project: AmpersandProject, cellSize: float):
        nx, ny, nz = StlAnalysis.calc_nx_ny_nz(project.settings.mesh.domain, cellSize)
        if (nx > 500 or ny > 500 or nz > 500):
            IOUtils.print("Warning: Mesh is too fine. Consider increasing the cell size")
        project.settings.mesh.domain.nx = nx
        project.settings.mesh.domain.ny = ny
        project.settings.mesh.domain.nz = nz


    @staticmethod
    def change_stl_purpose(geometry, meshSettings):
        stlFile = geometry.file
        IOUtils.print(f"Current STL file purpose: {geometry.purpose}")
        purpose = IOUtils.get_input("Enter new STL file purpose: ")
        geometry.purpose = purpose
        return geometry

    # this will allow the user to change the details of the stl file if necessary
    # TODO: fix this
    @staticmethod
    def change_stl_details(project, stl_file_number=0):
        project.list_stl_files()
        change_purpose = IOUtils.get_input("Change any STL files (y/N)?: ")
        if change_purpose.lower() != 'y':
            IOUtils.print("No change in STL files properties")
            return 0
        stl_file_number = IOUtils.get_input(
            "Enter the number of the file to change purpose: ")
        try:
            stl_file_number = int(stl_file_number)
        except ValueError:
            IOUtils.print("Invalid input. Please try again.")
            ModService.change_stl_details()
            # return -1
        if stl_file_number < 0 or stl_file_number > len(project.stl_files):
            IOUtils.print("Invalid input. Please try again.")
            ModService.change_stl_details()

        stl_file = project.stl_files[stl_file_number]
        stl_name = stl_file.name
        purpose = AmpersandDataInput.get_purpose()
        # self.add_purpose_(stl_name,purpose)
        return 0

    # add purpose to the stl file. currently not used
    @staticmethod
    def add_purpose_(stl_files, stl_name, purpose='wall'):
        IOUtils.print(f"Setting purpose of {stl_name} to")
        for stl in stl_files:
            if stl.name == stl_name:
                IOUtils.print(
                    f"Setting purpose of {stl_name} to {purpose}")
                stl.purpose = purpose
                return stl_files
        IOUtils.print(
            f"STL file {stl_name} not found in the project")
        return -1

    @staticmethod
    def change_stl_refinement_level(project: AmpersandProject, stl_name: str):
        project.change_stl_refinement_level(stl_name)

    # ---------------------------------------------------------------------#
    # The functions called when modifications are to be made project #

    @staticmethod
    def change_background_mesh(project: AmpersandProject):
        IOUtils.print("Current background mesh")
        project.summarize_background_mesh()
        # ask whether to change domain size
        change_domain_size = IOUtils.get_input_bool(
            "Change domain size (y/N)?: ")
        # ask new domain size
        if change_domain_size:
            bounds = AmpersandDataInput.get_domain_size()
            ModService.change_domain_size(project, bounds)
            IOUtils.print("Domain size changed")
        # ask new cell size
        change_mesh_size = IOUtils.get_input_bool(
            "Change cell size (y/N)?: ")
        if change_mesh_size:
            cellSize = AmpersandDataInput.get_cell_size()
            project.settings.mesh.maxCellSize = cellSize
            # calculate new mesh size
            ModService.change_mesh_size(project, cellSize)
            IOUtils.print("Cell size changed")
        if change_domain_size or change_mesh_size:
            project.summarize_background_mesh()
        else:
            IOUtils.print("No change in background mesh")

    # TODO: fix this function
    @staticmethod
    def add_geometry(project: AmpersandProject):
        IOUtils.print("Adding geometry")

        yN = IOUtils.get_input("Add STL file to the project (y/N)?: ")
        while yN.lower() == 'y':
            stl_path = IOUtils.get_file( [("STL Geometry", "*.stl"), ("OBJ Geometry", "*.obj")])
            purpose = AmpersandDataInput.get_purpose()
            project.add_stl_file(stl_path, purpose)
            yN = IOUtils.get_input("Add another STL file to the project (y/N)?: ")
        AmpersandUtils.list_stl_files(project.stl_files)

    # TODO: fix this function
    @staticmethod
    def change_refinement_levels(project: AmpersandProject):
        IOUtils.print("Changing refinement levels")
        # TODO: Implement this function
        AmpersandUtils.list_stl_files(project.stl_files)

        stl_file_number = IOUtils.get_input("Enter the number of the file to change refinement level: ")
        try:
            stl_file_number = int(stl_file_number)
        except ValueError:
            IOUtils.print("Invalid input. Please try again.")
        if stl_file_number <= 0 or stl_file_number > len(project.stl_files):
            IOUtils.print("Invalid input. Please try again.")
        else:
            ModService.change_stl_refinement_level(project, stl_file_number-1)
        AmpersandUtils.list_stl_files(project.stl_files)

    @staticmethod
    def change_mesh_point(project: AmpersandProject):
        IOUtils.print("Changing mesh points")
        currentMeshPoint = project.settings.mesh.castellatedMeshControls.locationInMesh
        IOUtils.print(
            f"Current mesh points: ({currentMeshPoint[0]},{currentMeshPoint[1]},{currentMeshPoint[2]})")

        x, y, z = IOUtils.get_input_vector("Enter new mesh points: ")
        project.settings.mesh.castellatedMeshControls.locationInMesh = (x, y, z)
        IOUtils.print(
            f"New mesh points: ({currentMeshPoint[0]},{currentMeshPoint[1]},{currentMeshPoint[2]})")

    # TODO: fix this function
    @staticmethod
    def change_boundary_conditions(project: AmpersandProject):
        IOUtils.print("Changing boundary conditions")
        # TODO: Implement this function
        bcs = project.summarize_boundary_conditions()
        # ampersandIO.printMessage("Current boundary conditions")
        # ampersandIO.printMessage(bcs)

        bc_number = IOUtils.get_input( "Enter the number of the boundary to change: ")
        try:
            bc_number = int(bc_number)
        except ValueError:
            IOUtils.print("Invalid input. Please try again.")
        if bc_number <= 0 or bc_number > len(bcs):
            IOUtils.print("Invalid input. Please try again.")
        else:
            bc = bcs[bc_number-1]
            IOUtils.print(f"Changing boundary condition for patch: {bc}")
            newBcType = AmpersandDataInput.get_boundary_type()
            project.change_boundary_condition(bc, newBcType)

    @staticmethod
    def change_numerical_settings(project: AmpersandProject):
        IOUtils.print("Changing numerical settings")
        # TODO: Implement this function

    @staticmethod
    def change_simulation_settings(project: AmpersandProject):
        IOUtils.print("Changing simulation settings")
        # TODO: Implement this function

    @staticmethod
    def change_turbulenc_model(project: AmpersandProject):
        IOUtils.print("Changing turbulence model")
        # TODO: Implement this function

    @staticmethod
    def change_post_process_settings(project: AmpersandProject):
        IOUtils.print("Changing post process settings")
        # TODO: Implement this function

    @staticmethod
    def change_fluid_properties(project: AmpersandProject):
        IOUtils.print("Current fluid properties")
        IOUtils.print(f"Density: {project.settings.physicalProperties.rho}")
        IOUtils.print(f"Kinematic viscosity: {project.settings.physicalProperties.nu}")
        fluid = AmpersandDataInput.choose_fluid_properties()
        project.settings.physicalProperties.fluid = fluid


