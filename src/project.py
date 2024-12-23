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
from typing import Optional, Union, cast
from src.models.inputs import FluidProperties
from src.models.settings import SimulationSettings, TriSurfaceMeshGeometry, RefinementAmount
from src.utils.data_input import IOUtils


class AmpersandProject: 
    def __init__(self, project_path: Union[str, Path], settings: Optional[SimulationSettings] = None):
        self.settings = settings or SimulationSettings()
        self.project_path = Path(project_path)
    
    @property
    def name(self):
        return self.project_path.name

    # TODO: fix this later
    def change_boundary_condition(self, bcName: str, newBC: str):
        if not self.settings.mesh.internalFlow:  # if it is external flow
            bcPatches = self.settings.mesh.patches
            for name, aPatch in self.settings.mesh.patches.items():
                if bcName == name:
                    aPatch.type = newBC
                    IOUtils.print(
                        f"Boundary condition {bcName} changed to {newBC}")
                    return 0
            if bcName in bcPatches:
                self.settings.mesh.patches[bcName].type = newBC
                self.settings.mesh.patches[bcName].purpose = newBC
                newProperty = self.get_property(newBC)
                self.settings.mesh.patches[bcName].property = newProperty
                IOUtils.print(
                    f"Boundary condition {bcName} changed to {newBC}")
                return 0
            else:
                IOUtils.print(
                    "Boundary condition not found in the list")
        for name, geometry in self.settings.mesh.geometry:
            if name == bcName:
                geometry.purpose = newBC
                newProperty = self.get_property(newBC)
                self.settings.mesh.patches[bcName].property = newProperty
                IOUtils.print(
                    f"Boundary condition of {bcName} changed to {newBC}")
                return 0
        return -1

    def change_stl_refinement_level(self, stl_name: str):
        IOUtils.print("Changing refinement level")
        refMin = IOUtils.get_input_int("Enter new refMin: ")
        refMax = IOUtils.get_input_int("Enter new refMax: ")
        
        stl_geoemtry = self.settings.mesh.geometry[stl_name]
        assert isinstance(stl_geoemtry, TriSurfaceMeshGeometry), "Geometry is not a TriSurfaceMeshGeometry"
        stl_geoemtry.refineMin = refMin
        stl_geoemtry.refineMax = refMax
        stl_geoemtry.featureLevel = refMax
    

    def set_flow_type(self, is_internal_flow=False):
        self.settings.mesh.internalFlow = is_internal_flow

    def set_half_model(self, is_half_model: bool):
        self.settings.mesh.halfModel = is_half_model

        if is_half_model:
            self.settings.mesh.patches['back'].type = 'symmetry'

    def set_inlet_values(self, U: Optional[tuple[float, float, float]] = None):
        if (not self.settings.mesh.internalFlow):  # external flow
            assert U is not None, "Inlet velocity is not set, required for external flow"
            self.settings.inletValues.U = U
            self.settings.boundaryConditions.velocityInlet.u_value = U
        else:  # internal flow
            # Use inlet values from the stl file
            IOUtils.print("Setting inlet values for various inlet boundaries")
            # TODO: check this out and ensure it sets once
            for geometry in self.settings.mesh.geometry.values():
                if isinstance(geometry, TriSurfaceMeshGeometry) and geometry.purpose == 'inlet':
                    U_stl = cast(tuple[float, float, float], geometry.property or U)
                    self.settings.boundaryConditions.velocityInlet.u_value = U_stl
                    self.settings.inletValues.U = U_stl

    def set_fluid_properties(self, fluid: FluidProperties):
        self.settings.physicalProperties.fluid = fluid

    def set_parallel(self, n_core: int):
        self.settings.parallel.numberOfSubdomains = n_core

    # set the turbulence model for the simulation
    def set_turbulence_model(self, turbulence_model='kOmegaSST'):
        self.settings.physicalProperties.turbulenceModel = turbulence_model

    def set_is_transient(self, is_transient: bool):
        self.settings.control.transient = is_transient

    def set_transient_settings(self, is_transient: bool, end_time: int, write_interval: int, time_step: int):
        self.set_is_transient(is_transient)
        if is_transient:
            IOUtils.print("Transient simulation settings")
            self.settings.control.application = 'pimpleFoam'
            self.settings.simulationFlow.solver = 'pimpleFoam'
            self.settings.control.endTime = end_time
            self.settings.control.writeInterval = write_interval
            self.settings.control.deltaT = time_step
            self.settings.control.adjustTimeStep = 'no'
            self.settings.control.maxCo = 0.9
            self.settings.numerical.ddtSchemes.default = 'Euler'
            # if steady state, SIMPLEC is used. If transient, PIMPLE is used
            # for PIMPLE, the relaxation factors are set to 0.7 and p = 0.3
            self.settings.numerical.relaxationFactors.p = 0.3

    def set_on_ground(self, on_ground: bool):
        self.settings.mesh.onGround = on_ground
        # TODO: ground doesn't exist
        # if on_ground:
        #     self.settings.mesh.patches['ground'].type = 'wall'

    def set_refinement_amount(self, ref_amount: RefinementAmount):
        self.settings.mesh.refAmount = ref_amount


    def set_post_process_settings(self, useFOs: bool):
        self.settings.postProcess.FOs = useFOs
        meshPoint = list(self.settings.mesh.castellatedMeshControls.locationInMesh)
        self.settings.postProcess.massFlow = True
        self.settings.postProcess.minMax = True
        self.settings.postProcess.yPlus = True
        self.settings.postProcess.forces = True
        # the default probe location for monitoring of flow variables
        self.settings.postProcess.probeLocations.append(meshPoint)


    def summarize_project(self):
        IOUtils.show_title("Project Summary")

        IOUtils.print(f"Internal Flow: {self.settings.mesh.internalFlow}")
        if (self.settings.mesh.internalFlow == False):
            IOUtils.print(f"On Ground: {self.settings.mesh.onGround}")
        IOUtils.print(f"Transient: {self.settings.control.transient}")
        IOUtils.print(self.settings.mesh.domain.__repr__())
        # TODO: maybe turn this back on later
        # AmpersandUtils.list_stl_files(self.stl_files)
        

    def summarize_boundary_conditions(self):
        i = 1
        boundaries = []
        IOUtils.show_title("Boundary Conditions")
        IOUtils.print(f"{'No.':<5}{'Name':<20}{
                                 'Purpose':<20}{'Value':<15}")
        # for external flows, show the boundary conditions for domain first
        if self.settings.mesh.internalFlow == False:
            for patch_name in self.settings.mesh.patches.keys():
                patch = self.settings.mesh.patches[patch_name]
                if patch.property == None:
                    property = "None"
                elif isinstance(patch.property, list):
                    property = f"[{patch.property[0]} {
                        patch.property[1]} {patch.property[2]}]"
                elif isinstance(patch.property, tuple):
                    property = f"[{patch.property[0]} {
                        patch.property[1]} {patch.property[2]}]"
                else:
                    property = patch.property
                IOUtils.print(f"{i:<5}{patch_name:<20}{patch.purpose:<20}{property:<15}")
                i += 1
                boundaries.append(patch_name)
        for patch_name, patch in self.settings.mesh.geometry.items():
            if patch.purpose != 'refinementRegion' and patch.purpose != 'refinementSurface':
                if patch.property == None:
                    property = "None"
                elif isinstance(patch.property, list):
                    property = f"[{patch.property[0]} {
                        patch.property[1]} {patch.property[2]}]"
                elif isinstance(patch.property, tuple):
                    property = f"[{patch.property[0]} {
                        patch.property[1]} {patch.property[2]}]"
                else:
                    property = "None"
                IOUtils.print(f"{i:<5}{patch_name:<20}{patch.purpose:<20}{property:<15}")
                i += 1
                boundaries.append(patch_name)
        return boundaries  # return the number of boundarys


    def list_stl_files(self):
        if IOUtils.GUIMode:
            for i, (geometry_name, geometry) in enumerate(self.settings.mesh.geometry.items()):
                if isinstance(geometry, TriSurfaceMeshGeometry):
                    IOUtils.print(f"{i+1}. {geometry_name}")
            return
        IOUtils.show_title("STL Files")

        IOUtils.print(f"{'No.':<5}{'Name':<20}{'Purpose':<20}{'RefineMent':<15}{'Property':<15}")
        for i, (geometry_name, geometry) in enumerate(self.settings.mesh.geometry.items()):
            if isinstance(geometry, TriSurfaceMeshGeometry):
                if (geometry.property == None):
                    stl_property = "None"
                    if geometry.purpose == 'wall':
                        stl_property = f"nLayers: {geometry.nLayers}"
                    else:
                        stl_property = "None"
                elif isinstance(geometry.property, list):
                    stl_property = f"[{geometry.property[0]} {
                        geometry.property[1]} {geometry.property[2]}]"
                elif isinstance(geometry.property, tuple):
                    if geometry.purpose == 'inlet':
                        stl_property = f"U: [{geometry.property[0]} {
                            geometry.property[1]} {geometry.property[2]}]"
                    elif geometry.purpose == 'cellZone':
                        stl_property = f"Refinement: {geometry.property[0]}"
                else:
                    stl_property = geometry.property
                IOUtils.print(f"{i+1:<5}{geometry_name:<20}{geometry.purpose:<20}({geometry.refineMin} {geometry.refineMax}{')':<11}{stl_property:<15}")
        IOUtils.print_line()


    def get_stl_paths(self, project_path: Union[str, Path]):
        stl_dir = Path(project_path) / "constant" / "triSurface"
        if not stl_dir.exists():
            return []
        return list(stl_dir.glob("*.stl"))