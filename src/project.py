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
import shutil
from typing import Optional, Union, cast
from src.models.inputs import FluidPhysicalProperties
from src.primitives import AmpersandUtils, AmpersandIO, AmpersandDataInput
from src.models.settings import SimulationSettings, TriSurfaceMeshGeometry, RefinementAmount, PatchPurpose
from src.utils.stl_analysis import StlAnalysis


class AmpersandProject:  # ampersandProject class to handle the project creation and manipulation
    # this class will contain the methods to handle the logic and program flow
    def __init__(self, project_path: Union[str, Path], settings: Optional[SimulationSettings] = None):
        self.settings = settings or SimulationSettings()
        self.settings.mesh.geometry = AmpersandUtils.treat_bounds(
            self.settings.mesh.geometry
        )

        self.project_path = Path(project_path)
        self.current_stl_file = None   # current stl file being processed
    
        self.internalFlow = False  # default is external flow
        self.on_ground = False  # default is off the ground
        self.halfModel = False  # default is full model
        self.transient = False  # default is steady state
        self.ref_amount = 0  # 0: coarse, 1: medium, 2: fine
        self.useFOs = False  # default is not to use function objects
        self.current_modification = None  # current modification to the project settings
        # flag to check if the current working directory is the project directory
        # self.bbox = BoundingBox(minx=-1e-3, maxx=1e-3, miny=-1e-3, maxy=1e-3, minz=-1e-3, maxz=1e-3)
        # self.minX, self.maxX, self.minY, self.maxY, self.minZ, self.maxZ = -1e-3, 1e-3, -1e-3, 1e-3, -1e-3, 1e-3
    # --------------------------------------------------------------------
    # Methods to handle the project summary and changes
    # --------------------------------------------------------------------

    @property
    def name(self):
        return self.project_path.name

    def summarize_boundary_conditions(self):
        return AmpersandUtils.list_boundary_conditions(self.settings.mesh)


    def summarize_project(self):
        trueFalse = {True: 'Yes', False: 'No'}
        AmpersandIO.show_title("Project Summary")

        AmpersandIO.printMessage(f"Internal Flow: {trueFalse[self.internalFlow]}")
        if (self.internalFlow == False):
            AmpersandIO.printMessage(f"On Ground: {trueFalse[self.on_ground]}")
        AmpersandIO.printMessage(f"Transient: {trueFalse[self.transient]}")
        self.summarize_background_mesh()
        # TODO: maybe turn this back on later
        # AmpersandUtils.list_stl_files(self.stl_files)
        

    # this will show the details of the background mesh
    def summarize_background_mesh(self):
        minX = self.settings.mesh.domain.minx
        maxX = self.settings.mesh.domain.maxx
        minY = self.settings.mesh.domain.miny
        maxY = self.settings.mesh.domain.maxy
        minZ = self.settings.mesh.domain.minz
        maxZ = self.settings.mesh.domain.maxz
        nx = self.settings.mesh.domain.nx
        ny = self.settings.mesh.domain.ny
        nz = self.settings.mesh.domain.nz
        AmpersandIO.printMessage(f"Domain size:{'X':>10}{'Y':>10}{'Z':>10}")
        AmpersandIO.printMessage(f"Min         {minX:>10.3f}{minY:>10.3f}{minZ:>10.3f}")
        AmpersandIO.printMessage(f"Max         {maxX:>10.3f}{maxY:>10.3f}{maxZ:>10.3f}")
        AmpersandIO.printMessage(f"Background mesh size: {nx}x{ny}x{nz} cells")
        AmpersandIO.printMessage(f"Background cell size: {self.settings.mesh.maxCellSize} m")

    # TODO: fix this later
    def change_boundary_condition(self, bcName: str, newBC: str):
        if not self.internalFlow:  # if it is external flow
            bcPatches = self.settings.mesh.patches
            for name, aPatch in self.settings.mesh.patches.items():
                if bcName == name:
                    aPatch.type = newBC
                    AmpersandIO.printMessage(
                        f"Boundary condition {bcName} changed to {newBC}")
                    return 0
            if bcName in bcPatches:
                self.settings.mesh.patches[bcName].type = newBC
                self.settings.mesh.patches[bcName].purpose = newBC
                newProperty = self.get_property(newBC)
                self.settings.mesh.patches[bcName].property = newProperty
                AmpersandIO.printMessage(
                    f"Boundary condition {bcName} changed to {newBC}")
                return 0
            else:
                AmpersandIO.printMessage(
                    "Boundary condition not found in the list")
        for name, geometry in self.settings.mesh.geometry:
            if name == bcName:
                geometry.purpose = newBC
                newProperty = self.get_property(newBC)
                self.settings.mesh.patches[bcName].property = newProperty
                AmpersandIO.printMessage(
                    f"Boundary condition of {bcName} changed to {newBC}")
                return 0
        return -1

    def change_stl_refinement_level(self, stl_name: str):
        AmpersandIO.printMessage("Changing refinement level")
        refMin = AmpersandIO.get_input_int("Enter new refMin: ")
        refMax = AmpersandIO.get_input_int("Enter new refMax: ")
        
        stl_geoemtry = self.settings.mesh.geometry[stl_name]
        assert isinstance(stl_geoemtry, TriSurfaceMeshGeometry), "Geometry is not a TriSurfaceMeshGeometry"
        stl_geoemtry.refineMin = refMin
        stl_geoemtry.refineMax = refMax
        stl_geoemtry.featureLevel = refMax



    def add_stl_file(self, stl_path: Union[str, Path], purpose: PatchPurpose='wall'):
        # Convert paths to Path objects
        stl_path = Path(stl_path)
        stl_name=stl_path.name
        dest_path = self.project_path / "constant" / "triSurface" / stl_name

        # Validate input file
        if not stl_path.exists():
            raise FileNotFoundError(f"STL file {stl_path} does not exist")
            
        if dest_path.exists():
            raise ValueError(f"STL file {stl_name} already exists in project")


        # Get purpose and properties
        property = None if AmpersandIO.GUIMode else AmpersandDataInput.get_property(purpose)


        StlAnalysis.update_settings(self.settings, stl_path, purpose, property)


        # Copy STL file to project
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stl_path, dest_path)
            AmpersandIO.printMessage(f"Copied {dest_path.name} to {dest_path}")
        except OSError as e:
            raise RuntimeError(f"Failed to copy STL file: {e}")

        # Set solid name in STL file
        try:
            StlAnalysis.set_stl_solid_name(dest_path)
        except Exception as e:
            raise RuntimeError(f"Failed to set STL solid name: {e}")

        self.current_stl_file = dest_path


    def list_stl_paths(self, project_path: Union[str, Path]):
        stl_dir = Path(project_path) / "constant" / "triSurface"
        if not stl_dir.exists():
            return []
        return list(stl_dir.glob("*.stl"))


    def set_flow_type(self, is_internal_flow=False):
        self.internalFlow = is_internal_flow
        self.settings.mesh.internalFlow = is_internal_flow

    def set_half_model(self, is_half_model: bool):
        self.halfModel = is_half_model
        self.settings.mesh.halfModel = is_half_model

        if is_half_model:
            self.settings.mesh.patches['back'].type = 'symmetry'




    def set_inlet_values(self, U: Optional[tuple[float, float, float]] = None):
        if (not self.internalFlow):  # external flow
            assert U is not None, "Inlet velocity is not set, required for external flow"
            self.settings.inletValues.U = U
            self.settings.boundaryConditions.velocityInlet.u_value = U
        else:  # internal flow
            # Use inlet values from the stl file
            AmpersandIO.printMessage("Setting inlet values for various inlet boundaries")
            # TODO: check this out and ensure it sets once
            for geometry in self.settings.mesh.geometry.values():
                if isinstance(geometry, TriSurfaceMeshGeometry) and geometry.purpose == 'inlet':
                    U_stl = cast(tuple[float, float, float], geometry.property or U)
                    self.settings.boundaryConditions.velocityInlet.u_value = U_stl
                    self.settings.inletValues.U = U_stl

    def set_fluid_properties(self, fluid: FluidPhysicalProperties):
        self.settings.physicalProperties.rho = fluid.rho
        self.settings.physicalProperties.nu = fluid.nu

    def set_parallel(self, n_core: int):
        self.settings.parallel.numberOfSubdomains = n_core

    # setting the purpose of a patch. Used for setting the boundary conditions
    def set_purpose(self, patch, purpose='wall'):
        purposes = ['wall', 'inlet', 'outlet', 'refinementRegion', 'refinementSurface',
                    'cellZone', 'baffles', 'symmetry', 'cyclic', 'empty']
        # purposes = ['wall', 'inlet','outlet', 'refinementRegion', 'refinementSurface', 'cellZone', 'baffles']
        if purpose not in purposes:
            AmpersandIO.printMessage(
                "Invalid purpose. Setting purpose to wall")
            purpose = 'wall'
        patch.purpose = purpose

    # set the turbulence model for the simulation
    def set_turbulence_model(self, turbulence_model='kOmegaSST'):
        self.settings.physicalProperties.turbulenceModel = turbulence_model

    def set_transient_settings(self, is_transient: bool):
        self.transient = is_transient

        if self.transient:
            AmpersandIO.printMessage("Transient simulation settings")
            self.settings.control.transient = True
            self.settings.control.application = 'pimpleFoam'
            self.settings.simulationFlow.solver = 'pimpleFoam'
            self.settings.control.endTime = AmpersandIO.get_input_float("End time: ")
            self.settings.control.writeInterval = AmpersandIO.get_input_float("Write interval: ")
            self.settings.control.deltaT = AmpersandIO.get_input_float("Time step: ")
            self.settings.control.adjustTimeStep = 'no'
            self.settings.control.maxCo = 0.9
            self.settings.numerical.ddtSchemes.default = 'Euler'
            # if steady state, SIMPLEC is used. If transient, PIMPLE is used
            # for PIMPLE, the relaxation factors are set to 0.7 and p = 0.3
            self.settings.numerical.relaxationFactors.p = 0.3

    def set_on_ground(self, on_ground: bool):
        self.on_ground = on_ground
        self.settings.mesh.onGround = on_ground
        # TODO: ground doesn't exist
        # if on_ground:
        #     self.settings.mesh.patches['ground'].type = 'wall'

    def set_refinement_amount(self, ref_amount: RefinementAmount):
        self.ref_amount = ref_amount
        self.settings.mesh.refAmount = ref_amount


    def set_post_process_settings(self, useFOs: bool):
        self.useFOs = useFOs
        self.settings.postProcess.FOs = useFOs

        meshPoint = list(self.settings.mesh.castellatedMeshControls.locationInMesh)
        self.settings.postProcess.massFlow = True
        self.settings.postProcess.minMax = True
        self.settings.postProcess.yPlus = True
        self.settings.postProcess.forces = True
        # the default probe location for monitoring of flow variables
        self.settings.postProcess.probeLocations.append(meshPoint)



    # TODO: this function is not used here
    # def remove_stl_file(self, stl_file_number=0):
    #     stl_file_number = AmpersandIO.get_input(
    #         "Enter the number of the file to remove: ")
    #     try:
    #         stl_file_number = int(stl_file_number)
    #     except ValueError:
    #         AmpersandIO.printMessage("Invalid input. Aborting operation")
    #         return -1
    #     if stl_file_number < 0 or stl_file_number > len(self.stl_files):
    #         AmpersandIO.printMessage("Invalid file number. Aborting operation")
    #         return -1
    #     stl_file = self.stl_files[stl_file_number]
    #     stl_name = stl_file.name
    #     self.stl_files.remove(stl_file)
    #     stl_path = os.path.join(self.project_path, "constant", "triSurface", stl_name)
    #     try:
    #         os.remove(stl_path)
    #     except OSError as error:
    #         AmpersandIO.printError(error)
    #         return -1
    #     return 0



    # Add a stl file to the project settings (self.settings.mesh)
    # def add_stl_to_mesh_settings(self, stl_name, refMin=0, refMax=0, featureEdges=True,
    #                              featureLevel=1, purpose='wall', property=None, bounds=None, nLayers=3):
    #     # Purpose is wall by default
    #     # Other purposes are patch, refinementRegion, refinementSurface, cellZone, baffles

    #     if self.refinement == 0:
    #         nLayers = 3
    #     elif self.refinement == 1:
    #         nLayers = 5
    #     else:
    #         nLayers = 7

    #     stl_geometry = {'name': stl_name, 'type': 'triSurfaceMesh', 'purpose': purpose, 'refineMin': refMin, 'refineMax': refMax,
    #             'featureEdges': featureEdges, 'featureLevel': featureLevel, 'nLayers': nLayers, 'property': property, 'bounds': bounds}


    #     stl_path = self.get_stl_path(stl_geometry.name)
    #     self.settings.mesh.geometry.append(stl_geometry)

    #     if not stl_path.exists():
    #         self.stl_files.append(stl_geometry)
    #         self.settings.mesh.geometry.append(stl_geometry)
    #     else:
    #         self.stl_files[idx] = stl_geometry



    # def set_max_domain_size(self, domain_size: Sequence[float], nx: int, ny: int, nz: int):
    #     self.minX = min(domain_size[0], self.minX)
    #     self.maxX = max(domain_size[1], self.maxX)
    #     self.minY = min(domain_size[2], self.minY)
    #     self.maxY = max(domain_size[3], self.maxY)
    #     self.minZ = min(domain_size[4], self.minZ)
    #     self.maxZ = max(domain_size[5], self.maxZ)

    #     self.settings.mesh.domain.nx = nx
    #     self.settings.mesh.domain.ny = ny
    #     self.settings.mesh.domain.nz = nz

    # TODO: not used here
    # def adjust_domain_size(self):
    #     # adjust the domain size based on the bounding box of the stl files
    #     AmpersandIO.printMessage(
    #         "Adjusting domain size based on the bounding box of the stl files")
    #     for geometry in self.settings.mesh.geometry:
    #         stl_name = geometry.name
    #         stl_path = os.path.join(self.project_path, "constant", "triSurface", stl_name)
    #         stlBoundingBox = StlAnalysis.compute_bounding_box(stl_path)
    #         xmin, xmax, ymin, ymax, zmin, zmax = stlBoundingBox
    #         self.minX = min(xmin, self.minX)
    #         self.maxX = max(xmax, self.maxX)
    #         self.minY = min(ymin, self.minY)
    #         self.maxY = max(ymax, self.maxY)
    #         self.minZ = min(zmin, self.minZ)
    #         self.maxZ = max(zmax, self.maxZ)
    #         # self.settings.mesh = stlAnalysis.set_mesh_location(self.settings.mesh, stl_path,self.internalFlow)
    #     # if the flow is internal, the domain size should be adjusted to include the entire geometry

    #     self.settings.mesh.domain.minX = self.minX
    #     self.settings.mesh.domain.maxX = self.maxX
    #     self.settings.mesh.domain.minY = self.minY
    #     self.settings.mesh.domain.maxY = self.maxY
    #     self.settings.mesh.domain.minZ = self.minZ
    #     self.settings.mesh.domain.maxZ = self.maxZ