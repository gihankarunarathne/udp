#!/usr/bin/python3

import os, json, datetime, sys, math
from os.path import join as pjoin

SKIP_META_LINES = 6
# FLO2D cells to longitude, latitude mapping file location
CADPTS_DAT_FILE = 'META_FLO2D/CADPTS.DAT'
CWD = os.getcwd()
CADPTS_DAT_FILE_PATH = pjoin(CWD, CADPTS_DAT_FILE)

def getWaterLevelGrid(lines) :
    waterLevels = []
    for line in lines[6:] :
        if line == '\n' :
            break
        v = line.split()
        # Get flood level (Elevation)
        # waterLevels.append('%s %s' % (v[0], v[1]))
        # Get flood depth (Depth)
        waterLevels.append('%s %s' % (v[0], v[2]))

    return waterLevels


def getGridBoudary(gap=250.0) :
    "longitude  -> x : larger value" 
    "latitude   -> y : smaller value"

    long_min = 1000000000.0
    lat_min = 1000000000.0
    long_max = 0.0
    lat_max = 0.0

    with open(CADPTS_DAT_FILE_PATH) as f:
        lines = f.readlines()
        for line in lines :
            values = line.split()
            long_min = min(long_min, float(values[1]))
            lat_min = min(lat_min, float(values[2]))

            long_max = max(long_max, float(values[1]))
            lat_max = max(lat_max, float(values[2]))

    return {
        'long_min': long_min,
        'lat_min': lat_min,
        'long_max': long_max,
        'lat_max': lat_max
    }


def getCellGrid(boudary, gap=250.0) :
    CellMap = {}

    with open(CADPTS_DAT_FILE_PATH) as f:
        lines = f.readlines()
        for line in lines :
            v = line.split()
            i = int((float(v[1]) - boudary['long_min']) / gap)
            j = int((float(v[2]) - boudary['lat_min']) / gap)
            if i >= 0 or j >= 0 :
                CellMap[int(v[0])] = (i, j)

    return CellMap


def getEsriGrid(waterLevels, boudary, CellMap, gap=250.0, missingVal=-9999) :
    "Esri GRID format : https://en.wikipedia.org/wiki/Esri_grid"
    "ncols         4"
    "nrows         6"
    "xllcorner     0.0"
    "yllcorner     0.0"
    "cellsize      50.0"
    "NODATA_value  -9999"
    "-9999 -9999 5 2"
    "-9999 20 100 36"
    "3 8 35 10"
    "32 42 50 6"
    "88 75 27 9"
    "13 5 1 -9999"

    EsriGrid = []

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap))
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap))

    Grid = [[-9999 for x in range(cols)] for y in range(rows)]

    for level in waterLevels :
        v = level.split()
        i, j = CellMap[int(v[0])]
        Grid[i][j] = float(v[1])

    EsriGrid.append('%s\t%s\n' % ('ncols', cols))
    EsriGrid.append('%s\t%s\n' % ('nrows', rows))
    EsriGrid.append('%s\t%s\n' % ('xllcorner', boudary['long_min']))
    EsriGrid.append('%s\t%s\n' % ('yllcorner', boudary['lat_min']))
    EsriGrid.append('%s\t%s\n' % ('cellsize', gap))
    EsriGrid.append('%s\t%s\n' % ('NODATA_value', missingVal))

    for i in range(0, rows) :
        arr = []
        for j in range(0, cols) :
            arr.append(Grid[i][j])

        EsriGrid.append('%s\n' % (' '.join(str(x) for x in arr)))

    return EsriGrid












