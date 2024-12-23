import os
from pathlib import Path
import shutil
from typing import Union

import yaml
from src.generators.blockMeshDict import create_blockMeshDict
from src.generators.boundaryConditionsDict import create_boundary_conditions
from src.generators.controlDict import createControlDict
from src.generators.decomposeParDict import createDecomposeParDict
from src.models.settings import SimulationSettings
from src.generators.numericalSettingsDict import create_fvSchemesDict, create_fvSolutionDict
from src.generators.postProcessDict import PostProcess
from src.utils.common import crlf_to_LF
from src.utils.data_input import IOUtils
from src.project import AmpersandProject
from src.generators.scriptGenerator import ScriptGenerator
from src.generators.snappyHexMeshDict import create_snappyHexMeshDict
from src.generators.surfaceExtractorDict import create_surfaceDict
from src.generators.transportAndTurbulenceDict import create_transportPropertiesDict, create_turbulencePropertiesDict


class ProjectService:
    @staticmethod
    def create_project(project_path: Union[str, Path]):
        """Create the project directory structure for an OpenFOAM case.
        
        Args:
            project_path: Path where the project should be created, can be string or Path

        Raises:
            ValueError: If project_path is None
            OSError: If there are issues creating directories or changing directory
        """
        project = AmpersandProject(project_path)

        IOUtils.print("Creating the project")

        if project_path is None:
            raise ValueError("No project path provided")

        project_path = Path(project_path)
        
        # Create required OpenFOAM directories 
        required_dirs = [
            project_path / "0",
            project_path / "constant",
            project_path / "system",
            project_path / "constant" / "triSurface"
        ]

        try:
            for directory in required_dirs:
                if not directory.exists():
                    directory.mkdir(parents=True)
                    IOUtils.print(f"Created {directory} directory")
        except OSError as e:
            raise OSError(f"Failed to create OpenFOAM directory structure: {e}")
        
        ProjectService.write_settings(project)

        return project

    @staticmethod
    def load_project(project_path: Union[str, Path]):
        IOUtils.print(f"Loading project from path: {project_path}")
        settings = SimulationSettings.model_validate(yaml.safe_load(f"{project_path}/project_settings.yaml"))
        project = AmpersandProject(project_path, settings)

        ProjectService.validate_project(project)

        IOUtils.print("Project loaded successfully")
        return project

    @staticmethod
    def write_project(project: AmpersandProject):
        ProjectService.write_settings(project)
        ProjectService.write_openfoam_files(project)

    @staticmethod
    def write_settings(project: AmpersandProject):
        IOUtils.print("Writing settings to project_settings.yaml")
        Path(project.project_path / "project_settings.yaml").write_text(
            yaml.dump(project.settings.model_dump(), default_flow_style=False, sort_keys=False)
        )
    @staticmethod
    def write_openfoam_files(project: AmpersandProject):
        if (not project.project_path.exists()):
            raise FileNotFoundError(f"Project not found at: {project.project_path}")

        create_boundary_conditions(project.settings.mesh, project.settings.boundaryConditions, f"{project.project_path}/0")

        # go inside the constant directory
        IOUtils.print("Creating physical properties and turbulence properties")
        # create transportProperties file
        tranP = create_transportPropertiesDict(project.settings.physicalProperties)
        # create turbulenceProperties file
        turbP = create_turbulencePropertiesDict(project.settings.physicalProperties)
        Path(f"{project.project_path}/constant/transportProperties").write_text(tranP)
        Path(f"{project.project_path}/constant/turbulenceProperties").write_text(turbP)

        # create the controlDict file
        IOUtils.print("Creating the system files")
        controlDict = createControlDict(project.settings.control)
        Path(f"{project.project_path}/system/controlDict").write_text(controlDict)
        
        blockMeshDict = create_blockMeshDict(project.settings.mesh)
        Path(f"{project.project_path}/system/blockMeshDict").write_text(blockMeshDict)
        
        snappyHexMeshDict = create_snappyHexMeshDict(project.settings.mesh)
        Path(f"{project.project_path}/system/snappyHexMeshDict").write_text(snappyHexMeshDict)
        
        surfaceFeatureExtractDict = create_surfaceDict(project.settings.mesh, "surfaceFeatureExtractDict")
        Path(f"{project.project_path}/system/surfaceFeatureExtractDict").write_text(surfaceFeatureExtractDict)
        
        fvSchemesDict = create_fvSchemesDict(project.settings.numerical)
        Path(f"{project.project_path}/system/fvSchemes").write_text(fvSchemesDict)
        
        fvSolutionDict = create_fvSolutionDict(project.settings.numerical, project.settings.solver)
        Path(f"{project.project_path}/system/fvSolution").write_text(fvSolutionDict)
        
        decomposeParDict = createDecomposeParDict(project.settings.parallel)
        Path(f"{project.project_path}/system/decomposeParDict").write_text(decomposeParDict)
        
        FODict = PostProcess.create_FOs(project.settings.mesh, project.settings.postProcess, useFOs=project.useFOs)
        Path(f"{project.project_path}/system/FOs").write_text(FODict)

        # create mesh script
        IOUtils.print("Creating scripts for meshing and running the simulation")
        meshScript = ScriptGenerator.create_mesh_script(project.settings.simulationFlow)
        Path(f"{project.project_path}/mesh").write_text(meshScript)
        
        # create simulation script
        simulationScript = ScriptGenerator.create_mesh_script(project.settings.simulationFlow)
        Path(f"{project.project_path}/run").write_text(simulationScript)
        
        crlf_to_LF(f"{project.project_path}/mesh")
        crlf_to_LF(f"{project.project_path}/run")
        
        mesh_script = Path(project.project_path) / "mesh"
        run_script = Path(project.project_path) / "run"
        if os.name != 'nt':
            mesh_script.chmod(0o755)
            run_script.chmod(0o755)
        
        IOUtils.print("\n-----------------------------------")
        IOUtils.print("Project files created successfully!")
        IOUtils.print("-----------------------------------\n")



    @staticmethod
    def validate_project(project: Union[AmpersandProject, str, Path]):
        project_path = Path(project) if isinstance(project, (str, Path)) else project.project_path
        ProjectService.check_directory(project_path / "0", project_path / "0.orig", copy=True)
        ProjectService.check_directory(project_path / "constant")
        ProjectService.check_directory(project_path / "system")
        ProjectService.check_directory(project_path / "constant/triSurface", check_files=True)



    @staticmethod
    def check_directory(path: Union[Path, str], fallback=None, copy=False, check_files=False):
        path = Path(path)
        if not path.exists():
            if fallback and Path(fallback).exists() and copy:
                IOUtils.print(f"{fallback} directory found. Copying to {path}")
                shutil.copytree(fallback, path)
            else:
                raise FileNotFoundError(f"{path} directory not found.")
        if check_files:
            if not list(path.iterdir()):
                raise FileNotFoundError(f"No files found in {path}.")

    @staticmethod
    def check_log_files(project_path: Union[str, Path]):
        project_path = Path(project_path)
        log_files = list(project_path.iterdir())
        if 'log.simpleFoam' in [f.name for f in log_files] or 'log.pimpleFoam' in [f.name for f in log_files]:
            IOUtils.print("Simulation log file found")
            return True
        IOUtils.print("No simulation log files found.")
        return False

    @staticmethod
    def check_post_process_files(project_path: Union[str, Path]):
        project_path = Path(project_path)
        post_process_path = project_path / "postProcessing/probe/0"
        if not post_process_path.exists():
            IOUtils.print(f"{post_process_path} directory does not exist.")
            return False
        files = [f.name for f in post_process_path.iterdir()]
        if 'U' not in files or 'p' not in files:
            IOUtils.print("Required files 'U' and 'p' not found in postProcessing.")
            return False
        return True

    @staticmethod
    def check_forces_files(project_path: Union[str, Path]):
        project_path = Path(project_path)
        forces_path = project_path / "postProcessing/forces/0"
        if not forces_path.exists():
            IOUtils.print(f"{forces_path} directory does not exist.")
            return False
        files = [f.name for f in forces_path.iterdir()]
        if 'force.dat' not in files:
            IOUtils.print("force.dat file not found in forces directory.")
            return False
        return True
