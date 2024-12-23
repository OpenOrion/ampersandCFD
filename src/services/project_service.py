import os
from pathlib import Path
import shutil
from typing import Union
from src.blockMeshGenerator import create_blockMeshDict
from src.boundaryConditionsGenerator import create_boundary_conditions
from src.controlDictGenerator import createControlDict
from src.decomposeParGenerator import createDecomposeParDict
from src.models.settings import SimulationSettings
from src.numericalSettingsGenerator import create_fvSchemesDict, create_fvSolutionDict
from src.postProcess import PostProcess
from src.primitives import AmpersandIO, AmpersandUtils
from src.project import AmpersandProject
from src.scriptGenerator import ScriptGenerator
from src.snappyHexMeshGenerator import create_snappyHexMeshDict
from src.surfaceExtractor import create_surfaceDict
from src.transportAndTurbulence import create_transportPropertiesDict, create_turbulencePropertiesDict


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

        AmpersandIO.printMessage("Creating the project")

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
                    AmpersandIO.printMessage(f"Created {directory} directory")
        except OSError as e:
            raise OSError(f"Failed to create OpenFOAM directory structure: {e}")
        
        ProjectService.write_settings(project)

        return project

    @staticmethod
    def load_project(project_path: Union[str, Path]):
        AmpersandIO.printMessage(f"Loading project from path: {project_path}")
        settings = SimulationSettings.model_validate(AmpersandUtils.yaml_to_dict(f"{project_path}/project_settings.yaml"))
        project = AmpersandProject(project_path, settings)

        ProjectService.validate_project(project)

        AmpersandIO.printMessage("Project loaded successfully")
        return project

    @staticmethod
    def write_project(project: AmpersandProject):
        ProjectService.write_settings(project)
        ProjectService.write_openfoam_files(project)

    @staticmethod
    def write_settings(project: AmpersandProject):
        AmpersandIO.printMessage("Writing settings to project_settings.yaml")
        AmpersandUtils.dict_to_yaml(project.settings.model_dump(), f'{project.project_path}/project_settings.yaml')

    @staticmethod
    def write_openfoam_files(project: AmpersandProject):
        if (not project.project_path.exists()):
            raise FileNotFoundError(f"Project not found at: {project.project_path}")

        create_boundary_conditions(project.settings.mesh, project.settings.boundaryConditions, f"{project.project_path}/0")

        # go inside the constant directory
        AmpersandIO.printMessage("Creating physical properties and turbulence properties")
        # create transportProperties file
        tranP = create_transportPropertiesDict(project.settings.physicalProperties)
        # create turbulenceProperties file
        turbP = create_turbulencePropertiesDict(project.settings.physicalProperties)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/constant/transportProperties", tranP)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/constant/turbulenceProperties", turbP)

        # create the controlDict file
        AmpersandIO.printMessage("Creating the system files")
        controlDict = createControlDict(project.settings.control)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/controlDict", controlDict)
        
        blockMeshDict = create_blockMeshDict(project.settings.mesh)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/blockMeshDict", blockMeshDict)
        
        snappyHexMeshDict = create_snappyHexMeshDict(project.settings.mesh)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/snappyHexMeshDict", snappyHexMeshDict)
        
        surfaceFeatureExtractDict = create_surfaceDict(project.settings.mesh, "surfaceFeatureExtractDict")
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/surfaceFeatureExtractDict", surfaceFeatureExtractDict)
        
        fvSchemesDict = create_fvSchemesDict(project.settings.numerical)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/fvSchemes", fvSchemesDict)
        
        fvSolutionDict = create_fvSolutionDict(project.settings.numerical, project.settings.solver)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/fvSolution", fvSolutionDict)
        
        decomposeParDict = createDecomposeParDict(project.settings.parallel)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/decomposeParDict", decomposeParDict)
        
        FODict = PostProcess.create_FOs(project.settings.mesh, project.settings.postProcess, useFOs=project.useFOs)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/system/FOs", FODict)

        # create mesh script
        AmpersandIO.printMessage("Creating scripts for meshing and running the simulation")
        meshScript = ScriptGenerator.create_mesh_script(project.settings.simulationFlow)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/mesh", meshScript)
        
        # create simulation script
        simulationScript = ScriptGenerator.create_mesh_script(project.settings.simulationFlow)
        AmpersandUtils.write_dict_to_file(f"{project.project_path}/run", simulationScript)
        
        AmpersandUtils.crlf_to_LF(f"{project.project_path}/mesh")
        AmpersandUtils.crlf_to_LF(f"{project.project_path}/run")
        
        mesh_script = Path(project.project_path) / "mesh"
        run_script = Path(project.project_path) / "run"
        if os.name != 'nt':
            mesh_script.chmod(0o755)
            run_script.chmod(0o755)
        
        AmpersandIO.printMessage("\n-----------------------------------")
        AmpersandIO.printMessage("Project files created successfully!")
        AmpersandIO.printMessage("-----------------------------------\n")



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
                AmpersandIO.printMessage(f"{fallback} directory found. Copying to {path}")
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
            AmpersandIO.printMessage("Simulation log file found")
            return True
        AmpersandIO.printMessage("No simulation log files found.")
        return False

    @staticmethod
    def check_post_process_files(project_path: Union[str, Path]):
        project_path = Path(project_path)
        post_process_path = project_path / "postProcessing/probe/0"
        if not post_process_path.exists():
            AmpersandIO.printMessage(f"{post_process_path} directory does not exist.")
            return False
        files = [f.name for f in post_process_path.iterdir()]
        if 'U' not in files or 'p' not in files:
            AmpersandIO.printMessage("Required files 'U' and 'p' not found in postProcessing.")
            return False
        return True

    @staticmethod
    def check_forces_files(project_path: Union[str, Path]):
        project_path = Path(project_path)
        forces_path = project_path / "postProcessing/forces/0"
        if not forces_path.exists():
            AmpersandIO.printMessage(f"{forces_path} directory does not exist.")
            return False
        files = [f.name for f in forces_path.iterdir()]
        if 'force.dat' not in files:
            AmpersandIO.printMessage("force.dat file not found in forces directory.")
            return False
        return True
