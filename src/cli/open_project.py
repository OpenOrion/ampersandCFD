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
from src.utils.data_input import AmpersandDataInput, IOUtils

from src.services.project_service import ProjectService

def open_project():
    IOUtils.print("Please select the project directory to open")
    
    parent_directory = IOUtils.ask_for_directory()
    project_name = IOUtils.get_input("Enter the project name: ")
    project_path = Path(f"{parent_directory}/{project_name}")


    project = ProjectService.load_project(project_path)

    IOUtils.print("Project loaded successfully")
    project.summarize_project()
    modify_project = IOUtils.get_input_bool("Do you want to modify the project settings (y/N)?: ")
   
    while modify_project:
        modification_type = AmpersandDataInput.choose_modification_categorized()
        ModService.modify_project(project, modification_type)
        ProjectService.write_settings(project)
        
        modify_project = IOUtils.get_input_bool("Do you want to modify another settings (y/N)?: ")
    
    if modify_project:  # if the project is modified at least once
        IOUtils.print("Generating the project files based on the new settings")
        ProjectService.write_project(project)

    else:
        IOUtils.print("No modifications were made to the project settings")
