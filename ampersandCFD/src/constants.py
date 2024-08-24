# Default values for the constants used in the ampersandCFD library
meshSettings = {
    'name': 'meshSettings',
    'scale': 1.0,
    'domain': {'minx': 0.0,
        'maxx': 1.0,
        'miny': 0.0,
        'maxy': 1.0,
        'minz': 0.0,
        'maxz': 1.0,
        'nx': 20,
        'ny': 20,
        'nz': 1},
    
    'patches': [
        {'left': 'inlet', 'type': 'patch','faces': [0, 1, 5, 4]},
        {'right': 'outlet', 'type': 'patch','faces': [2, 3, 7, 6]},
        {'front': 'front', 'type': 'wall','faces': [0, 3, 7, 4]},
        {'back': 'back', 'type': 'wall','faces': [1, 2, 6, 5]},
        {'bottom': 'bottom', 'type': 'wall','faces': [0, 1, 2, 3]},
        {'top': 'top', 'type': 'wall','faces': [4, 5, 6, 7]},
    ],
    'snappyHexSteps': {'castellatedMesh': True,
                       'snap': True,
                        'addLayers': True},

    'geometry': [{'name': 'stl1.stl','type':'triSurfaceMesh', 'refineMin': 1, 'refineMax': 3, 
                     'featureEdges':True,'nLayers':3},],

    'castellatedMeshControls': {'maxLocalCells': 2_000_000,
                                'maxGlobalCells': 5_000_000,
                                'minRefinementCells': 5,
                                'maxLoadUnbalance': 0.10,
                                'nCellsBetweenLevels': 5,
                                'features': [],
                                'refinementSurfaces': [],
                                'resolveFeatureAngle': 30,
                                'refinementRegions': [],
                                'locationInMesh': [0, 0, 0],
                                'allowFreeStandingZoneFaces': True},

    'snapControls': {'nSmoothPatch': 3,
                        'tolerance': 2.0,
                        'nSolveIter': 100,
                        'nRelaxIter': 8,
                        'nFeatureSnapIter': 10,
                        'implicitFeatureSnap': False,
                        'explicitFeatureSnap': True,
                        'multiRegionFeatureSnap': False},

    'addLayersControls': {'relativeSizes': True,
                            'expansionRatio': 1.2,
                            'finalLayerThickness': 0.3,
                            'minThickness': 0.001,
                            'nGrow': 0,
                            'featureAngle': 180,
                            'nRelaxIter': 5,
                            'nSmoothSurfaceNormals': 1,
                            'nSmoothNormals': 3,
                            'nSmoothThickness': 10,
                            'maxFaceThicknessRatio': 0.5,
                            'maxThicknessToMedialRatio': 0.3,
                            'minMedianAxisAngle': 90,
                            'nBufferCellsNoExtrude': 0,
                            'nLayerIter': 10,
                            'nRelaxIter': 5},

    'meshQualityControls': {'maxNonOrtho': 75,
                            'maxBoundarySkewness': 4,
                            'maxInternalSkewness': 4,
                            'maxConcave': 180,
                            'minTetQuality': 0.5,
                            'minVol': 1e-30,
                            'minArea': 1e-30,
                            'minTwist': 0.001,
                            'minDeterminant': 0.001,
                            'minFaceWeight': 0.01,
                            'minVolRatio': 0.01,
                            'minTriangleTwist': -1},
}



