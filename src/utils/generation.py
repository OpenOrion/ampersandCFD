from typing import Sequence


AMPERSAND_HEADER ="""
-------------------------------------------------------------------------------
  ***    *     *  ******   *******  ******    *****     ***    *     *  ******   
 *   *   **   **  *     *  *        *     *  *     *   *   *   **    *  *     *  
*     *  * * * *  *     *  *        *     *  *        *     *  * *   *  *     *  
*******  *  *  *  ******   ****     ******    *****   *******  *  *  *  *     *  
*     *  *     *  *        *        *   *          *  *     *  *   * *  *     *  
*     *  *     *  *        *        *    *   *     *  *     *  *    **  *     *  
*     *  *     *  *        *******  *     *   *****   *     *  *     *  ******   
-------------------------------------------------------------------------------
"""


class GenerationUtils:
    @staticmethod
    def createDimensions(M=1, L=1, T=1):
        return f"\ndimensions      [{M} {L} {T} 0 0 0 0];"

    @staticmethod
    def createInternalFieldScalar(type="uniform", value=0.0):
        return f"""\ninternalField   {type} {value};"""

    @staticmethod
    def createInternalFieldVector(type="uniform", value=[0.0, 0.0, 0.0]):
        return f"""\ninternalField   {type} ({value[0]} {value[1]} {value[2]});"""

    @staticmethod
    def createScalarFixedValue(patch_name="inlet", value=0):
        return f"""\n{patch_name}
        {{
            type            fixedValue;
            value           uniform {value};
        }};"""

    @staticmethod
    def createScalarZeroGradient(patch_name="inlet"):
        return f"""\n{patch_name}
        {{
            type            zeroGradient;
        }};"""

    @staticmethod
    def createVectorFixedValue(patch_name="inlet", value=[0, 0, 0]):
        return f"""\n{patch_name}
        {{
            type            fixedValue;
            value           uniform ("{value[0]} {value[1]} {value[2]})";
        }};"""

    @staticmethod
    def createVectorZeroGradient(patch_name="inlet"):
        return f"""\n{patch_name}
        {{
            type            zeroGradient;
        }};"""

    # This file contains the basic primitives used in the generation of OpenFOAM casefiles

    @staticmethod
    def createFoamHeader(className="dictionary", objectName="blockMeshDict"):
        header = f"""/*--------------------------------*- C++ -*----------------------------------*\\
    {AMPERSAND_HEADER}
    This file is part of OpenFOAM casefiles automatically generated by AmpersandCFD*/

    FoamFile
    {{
    version     2.0;
    format      ascii;
    class       {className};
    object      {objectName};
    }}"""
        return header

    @staticmethod
    def create_field_header(className: str, objectName: str, dimensions: tuple, fieldType: str, fieldValue: float):
        header = GenerationUtils.createFoamHeader(
            className=className, objectName=objectName)
        dims = GenerationUtils.createDimensions(M=dimensions[0], L=dimensions[1], T=dimensions[2])
        internalField = GenerationUtils.createInternalFieldScalar(fieldType, fieldValue)
        return f"{header}{dims}{internalField}\n"

    @staticmethod
    def createTupleString(seq: Sequence):
        return f"({seq[0]} {seq[1]} {seq[2]})"
