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

import os
from pathlib import Path
from typing import Union
import vtk
import numpy as np
import math
from src.models.settings import BoundingBox, Domain, MeshSettings, SearchableBoxGeometry, SimulationSettings, TriSurfaceMeshGeometry, RefinementAmount, PatchPurpose, PatchProperty
from src.thirdparty.stlToOpenFOAM import find_inside_point, is_point_inside, read_stl_file
from src.thirdparty.stlToOpenFOAM import extract_curvature_data, compute_curvature
from src.utils.data_input import IOUtils


class StlAnalysis:
    @staticmethod
    def calc_domain_bbox(stl_bbox: BoundingBox, size_factor=1.0, on_ground=False, internal_flow=False, is_half_model=False):
        max_length = stl_bbox.max_length
        max_size_factor = max_length*size_factor

        if (internal_flow):
            domain_bbox = stl_bbox.scale_dimensions(-0.1*size_factor, 0.1*size_factor, -0.1*size_factor, 0.1*size_factor, -0.1*size_factor, 0.1*size_factor)
        else:
            domain_bbox = stl_bbox.scale_dimensions(-3*max_size_factor, 9*max_size_factor, -2*max_size_factor, 2*max_size_factor, -2*max_size_factor, 2*max_size_factor)


        if on_ground:  # the the body is touching the ground
            domain_bbox.minz = stl_bbox.minz
            domain_bbox.maxz = stl_bbox.maxz + 4.0*max_size_factor
        
        if is_half_model:
            domain_bbox.maxy = (domain_bbox.maxy+domain_bbox.miny)/2.
        return domain_bbox


    # to calculate the refinement box for snappyHexMeshDict
    @staticmethod
    def get_refinement_box(stl_bbox: BoundingBox):
        return stl_bbox.scale_dimensions(-0.7, 15.0, -1.0, 1.0, -1.0, 1.0)

    @staticmethod
    def get_refinement_box_close(stl_bbox: BoundingBox):
        return stl_bbox.scale_dimensions(-0.2, 3.0, -0.45, 0.45, -0.45, 0.45)

    # to add refinement box to mesh settings
    @staticmethod
    def get_refinement_boxes(stl_bbox: BoundingBox, boxName='refinementBox', ref_level=2, is_internal_flow=False) -> dict[str, SearchableBoxGeometry]:
        if (is_internal_flow):
            return {}
        box = StlAnalysis.get_refinement_box(stl_bbox)
        fineBox = StlAnalysis.get_refinement_box_close(stl_bbox)
        return {
            boxName: SearchableBoxGeometry(
                type='searchableBox',
                purpose="refinementRegion",
                bbox=box,
                refineMax=ref_level-1
            ), 
            "fineBox": SearchableBoxGeometry(
                type='searchableBox',
                purpose='refinementRegion',
                bbox=fineBox,
                refineMax=ref_level
            )
        }
       
    # refinement box for the ground for external automotive flows
    @staticmethod
    def get_ground_refinement_box(mesh_settings: MeshSettings, stl_bbox: BoundingBox, refLevel=2):
        z = mesh_settings.domain.minz
        z_delta = 0.2*(stl_bbox.maxz-stl_bbox.minz)
        box = BoundingBox(minx=-1000.0, maxx=1000., miny=-1000, maxy=1000, minz=z-z_delta, maxz=z+z_delta)
        return SearchableBoxGeometry(
            type='searchableBox',
            purpose='refinementRegion', 
            bbox=box,
            refineMax=refLevel
        )

    # to calculate nearest wall thickness for a target yPlus value
    @staticmethod
    def calc_y(nu=1e-6, rho=1000., L=1.0, U_val=1.0, target_yPlus=200):
        # rho = fluid_properties.rho
        # nu = fluid_properties.nu
        Re = U_val*L/nu
        Cf = 0.0592*Re**(-1./5.)
        tau = 0.5*rho*Cf*U_val**2.
        uStar = np.sqrt(tau/rho)
        y = target_yPlus*nu/uStar
        return y

    # to calculate yPlus value for a given first layer thickness
    @staticmethod
    def calc_yPlus(nu=1e-6, L=1.0, u=1.0, y=0.001):
        Re = u*L/nu
        Cf = 0.0592*Re**(-1./5.)
        tau = 0.5*Cf*u**2.
        uStar = np.sqrt(tau)
        yPlus = uStar*y/nu
        return yPlus

    # calculate nearest cell size for a given expansion ratio and layer count
    @staticmethod
    def calc_cell_size(y_=0.001, nLayers=5, expRatio=1.2, thicknessRatio=0.3):
        max_y = y_*expRatio**(nLayers)
        return max_y/thicknessRatio

    @staticmethod
    def calc_refinement_levels(max_cell_size=0.1, target_cell_size=0.001):
        size_ratio = max_cell_size / target_cell_size
        n = np.log(size_ratio)/np.log(2.)
        # print(n)
        return int(np.ceil(n))

    @staticmethod
    def calc_nx_ny_nz(domain_bbox: BoundingBox, target_cell_size: float):
        nx = (domain_bbox.maxx-domain_bbox.minx)/target_cell_size
        ny = (domain_bbox.maxy-domain_bbox.miny)/target_cell_size
        nz = (domain_bbox.maxz-domain_bbox.minz)/target_cell_size
        nx, ny, nz = int(math.ceil(nx)), int(math.ceil(ny)), int(math.ceil(nz))
        # it is better to have even number of cells
        if nx % 2:  # if nx is odd
            nx += 1
        if ny % 2:  # if ny is odd
            ny += 1
        if nz % 2:  # if nz is odd
            nz += 1
        return (nx, ny, nz)

    # Function to read STL file and compute bounding box
    @staticmethod
    def compute_bounding_box(mesh: vtk.vtkPolyData):
        # Calculate the bounding box
        bounds = mesh.GetBounds()
        return BoundingBox(minx=bounds[0], maxx=bounds[1], miny=bounds[2], maxy=bounds[3], minz=bounds[4], maxz=bounds[5])

    # this is the wrapper function to check if a point is inside the mesh
    @staticmethod
    def is_point_inside(stl_file_path, point):
        # Check if the file exists
        if not os.path.exists(stl_file_path):
            raise FileNotFoundError(
                f"File not found: {stl_file_path}. Make sure the file exists.")
        # Create a reader for the STL file
        reader = vtk.vtkSTLReader()
        reader.SetFileName(stl_file_path)
        reader.Update()

        # Get the output data from the reader
        poly_data = reader.GetOutput()
        # Calculate the bounding box
        bounds = poly_data.GetBounds()
        # Check if the point is inside the bounding box
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        if point[0] < xmin or point[0] > xmax:
            return False
        if point[1] < ymin or point[1] > ymax:
            return False
        if point[2] < zmin or point[2] > zmax:
            return False
        # Check if the point is inside the mesh
        return is_point_inside(poly_data, point)

    @staticmethod
    def calc_nLayer(yFirst=0.001, targetCellSize=0.1, expRatio=1.2):
        n = np.log(targetCellSize*0.4/yFirst)/np.log(expRatio)
        return int(np.ceil(n))

    @staticmethod
    def calc_delta(U=1.0, nu=1e-6, L=1.0):
        Re = U*L/nu
        delta = 0.37*L/Re**(0.2)
        return delta

    @staticmethod
    # calculates N layers and final layer thickness
    # yFirst: first layer thickness
    # delta: boundary layer thickness
    # expRatio: expansion ratio
    def calc_layers(yFirst=0.001, delta=0.01, expRatio=1.2):
        currentThickness = yFirst*2.0  # initial thickness. Twice the yPlus value
        currentDelta = 0
        N = 0
        for i in range(1, 50):
            currentThickness = currentThickness*expRatio**(i)
            currentDelta = currentDelta + currentThickness
            if (currentDelta > delta):
                N = i
                break
        finalLayerThickness = currentThickness

        return N, finalLayerThickness


    # this function calculates the smallest curvature of the mesh
    # This function calls stlToOpenFOAM functions to read the mesh and calculate curvature

    @staticmethod
    def calc_smallest_curvature(mesh: vtk.vtkPolyData):
        curved_mesh = compute_curvature(mesh, curvature_type='mean')
        curvature_values = extract_curvature_data(curved_mesh)
        return np.min(curvature_values)

    @staticmethod
    def calc_background_cell_size(refinement_amount: RefinementAmount, domain_bbox: BoundingBox, maxCellSize: float, internalFlow: bool):
        max_length = domain_bbox.max_length
        min_length = domain_bbox.min_length
        
        if (refinement_amount == "coarse"):
            if (internalFlow):
                if max_length/min_length > 10:  # if the geometry is very slender
                    return min(max_length/50., maxCellSize)
                else:
                    return min(min_length/8., maxCellSize)
            else:
                # this is the size of largest blockMesh cells
                return min(min_length/3., maxCellSize)
        elif (refinement_amount == "medium"):
            if (internalFlow):
                if max_length/min_length > 10:  # if the geometry is very slender
                    return min(max_length/70., maxCellSize)
                else:
                    return min(min_length/12., maxCellSize)
            else:
                return min(min_length/5., maxCellSize)
        else:
            if (internalFlow):
                if max_length/min_length > 10:  # if the geometry is very slender
                    return min(max_length/90., maxCellSize)
                else:
                    return min(min_length/16., maxCellSize)
            else:
                return min(min_length/7., maxCellSize)



    @staticmethod
    def calc_domain(stl_bbox: BoundingBox, settings: SimulationSettings, max_cell_size=2.0, size_factor=1.0):
        characteristic_length = stl_bbox.max_length

        if (max_cell_size < 0.001):
            max_cell_size = characteristic_length/4.

        domain_size = StlAnalysis.calc_domain_bbox(stl_bbox, size_factor, settings.mesh.onGround, settings.mesh.internalFlow, settings.mesh.halfModel)
        if (max_cell_size < 0.001):
            max_cell_size = characteristic_length/4.
        background_cell_size = StlAnalysis.calc_background_cell_size(settings.mesh.refAmount, domain_size, max_cell_size, settings.mesh.internalFlow)
        nx, ny, nz = StlAnalysis.calc_nx_ny_nz(domain_size, background_cell_size)
        return Domain.from_bbox(domain_size, nx, ny, nz)


    @staticmethod
    def calc_num_layers(stl_bbox: BoundingBox, domain: Domain, settings: SimulationSettings, ref_level: int):
        characteristic_length = stl_bbox.max_length

        target_yPlus = {
            "coarse": 70,
            "medium": 50,
            "fine": 30,
        }[settings.mesh.refAmount]
        
        background_cell_size = (domain.maxx-domain.minx)/domain.nx
        # this is the thickness of closest cell
        target_y = StlAnalysis.calc_y(
            settings.physicalProperties.nu, 
            settings.physicalProperties.rho, 
            characteristic_length, 
            U_val=max(settings.inletValues.U), 
            target_yPlus=target_yPlus
        )
        
        target_cell_size = background_cell_size/2.**ref_level
        first_layer_thickness = target_y*2.0
        final_layer_thickness = target_cell_size*0.35

        return max(1, int(np.log(final_layer_thickness / first_layer_thickness)/np.log(settings.mesh.addLayersControls.expansionRatio)))


    @staticmethod
    def calc_center_of_mass(mesh: vtk.vtkPolyData):
        center_of_mass_filter = vtk.vtkCenterOfMass()
        center_of_mass_filter.SetInputData(mesh)
        center_of_mass_filter.Update()
        center_of_mass = center_of_mass_filter.GetCenter()
        return center_of_mass

    @staticmethod
    def get_location_in_mesh(mesh: vtk.vtkPolyData, is_internal_flow: bool) -> tuple[float, float, float]:
        center_of_mass = StlAnalysis.calc_center_of_mass(mesh)
        outside_point = StlAnalysis.get_outside_point(mesh)
        inside_point = find_inside_point(mesh, center_of_mass, min_bounds=None, max_bounds=None)
        return tuple(inside_point if is_internal_flow else outside_point) # type: ignore
        
    @staticmethod 
    def set_stl_solid_name(stl_file: Union[str, Path]) -> int:
        stl_path = Path(stl_file)
        IOUtils.print(f"Setting solid name for {stl_path}")
        
        if not stl_path.exists():
            raise FileNotFoundError(f"STL file not found: {stl_path}")

        if not stl_path.is_file():
            raise ValueError(f"Path is not a file: {stl_path}")

        # Extract solid name from filename without extension
        solid_name = stl_path.stem

        # Read and process file contents
        lines = stl_path.read_text().splitlines()
        new_lines = []
        for line in lines:
            if 'endsolid' in line.lower():
                line = f"endsolid {solid_name}"
            elif line.lower().lstrip().startswith('solid'):
                line = f"solid {solid_name}"
            new_lines.append(line + '\n')
        
        # Write back to file
        stl_path.write_text(''.join(new_lines))
        return 0

    

    @staticmethod
    def get_outside_point(mesh: vtk.vtkPolyData):
        stl_bbox = StlAnalysis.compute_bounding_box(mesh)
        outsideX = stl_bbox.maxx + 0.05*(stl_bbox.maxx-stl_bbox.minx)
        outsideY = stl_bbox.miny*0.95  # (stlMaxY - stlMinY)/2.
        outsideZ = (stl_bbox.maxz - stl_bbox.minz)/2.
        outsidePoint = (outsideX, outsideY, outsideZ)
        return outsidePoint


    # to set mesh settings for blockMeshDict and snappyHexMeshDict
    # TODO: make this apply for multiple stl files
    @staticmethod
    def update_settings(settings: SimulationSettings, stl_path: Union[str, Path], purpose: PatchPurpose, property: PatchProperty):
        stl_name = Path(stl_path).name
        stl_mesh = read_stl_file(str(stl_path))
        stl_bbox = StlAnalysis.compute_bounding_box(stl_mesh)

        # Skip feature edges for refinement regions
        feature_edges = purpose not in ('refinementRegion', 'refinementSurface')
        
        ref_level = {
            "coarse": 2,
            "medium": 4,
            "fine": 6,
        }[settings.mesh.refAmount]

        settings.mesh.domain = StlAnalysis.calc_domain(stl_bbox, settings)
        num_layers = StlAnalysis.calc_num_layers(stl_bbox, settings.mesh.domain, settings, ref_level)

        settings.mesh.geometry[stl_name] = TriSurfaceMeshGeometry(
            purpose=purpose,
            refineMin=0,
            refineMax=0,
            featureEdges=feature_edges,
            featureLevel=1,
            nLayers=num_layers,
            property=property,
            bounds=stl_bbox
        )

        refMin = max(1, ref_level)
        refMax = max(2, ref_level)
        for geometry in settings.mesh.geometry.values():
            if isinstance(geometry, TriSurfaceMeshGeometry):
                geometry.refineMin = refMin
                geometry.refineMax = refMax
                geometry.featureLevel = max(ref_level, 1)
                geometry.nLayers = num_layers

        settings.mesh.castellatedMeshControls.locationInMesh = StlAnalysis.get_location_in_mesh(stl_mesh, settings.mesh.internalFlow)
        
        box_ref_level = max(2, ref_level-3)
        refinement_boxes = StlAnalysis.get_refinement_boxes(stl_bbox, ref_level=box_ref_level, is_internal_flow=settings.mesh.internalFlow)
        settings.mesh.geometry.update(refinement_boxes)
        if (not settings.mesh.internalFlow and settings.mesh.onGround):
            # if the flow is external and the geometry is on the ground, add a ground refinement box
            settings.mesh.geometry["groundBox"] = StlAnalysis.get_ground_refinement_box(settings.mesh, stl_bbox, box_ref_level)
        
        # set the layer thickness to 0.5 times the cell size
        settings.mesh.addLayersControls.finalLayerThickness = 0.5
        minThickness = max(0.0001, settings.mesh.addLayersControls.finalLayerThickness/100.)
        settings.mesh.addLayersControls.minThickness = minThickness

        # store the background mesh size for future reference
        settings.mesh.maxCellSize = abs((settings.mesh.domain.maxx-settings.mesh.domain.minx)/settings.mesh.domain.nx)

        return settings.mesh




        # # print the summary of results
        # AmpersandIO.printMessage(
        #     "\n-----------------Mesh Settings-----------------")
        # AmpersandIO.printMessage(f"Domain size: {domain_size.size}")
        # AmpersandIO.printMessage(f"Nx Ny Nz: {nx},{ny},{nz}")
        # AmpersandIO.printMessage(f"Max cell size: {backgroundCellSize}")
        # AmpersandIO.printMessage(f"Min cell size: {targetCellSize}")
        # AmpersandIO.printMessage(f"Refinement Level:{ref_level}")

        # AmpersandIO.printMessage(
        #     "\n-----------------Turbulence-----------------")
        # AmpersandIO.printMessage(f"Target yPlus:{target_yPlus}")
        # AmpersandIO.printMessage(f'Reynolds number:{U*L/nu}')
        # AmpersandIO.printMessage(f"Boundary layer thickness:{delta}")
        # AmpersandIO.printMessage(f"First layer thickness:{adjustedNearWallThickness}")
        # AmpersandIO.printMessage(f"Final layer thickness:{finalLayerThickness}")
        # AmpersandIO.printMessage(f"YPlus:{adjustedYPlus}")
        # AmpersandIO.printMessage(f"Number of layers:{nLayers}")