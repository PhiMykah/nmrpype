import gemmi
from utils import catchError
import numpy as np
import json

FDDIMORDER = [2,1,3,4]

def load_ccp4_map(file : str) -> tuple[dict, np.ndarray]:
    """
    fn load_ccp4_map

    Loads electron density map into nmrPype format using gemmi

    Parameters
    ----------
    file : str
        .map file path 

    Returns
    -------
    dic, map_array : tuple[dict, np.ndarray]
        Returns the dictionary and ndarray to be added to dataframe
    """
    # Attempt to load ccp4 map but return error otherwise
    try:
        ccp4_map = gemmi.read_ccp4_map(file)
    except Exception as e:
        catchError(e, msg='Failed to read ccp4 map input file!', ePrint=False)
    
    map_array = np.array(ccp4_map.grid, copy=False)
    dic = init_ccp4_header(ccp4_map, map_array)

    return dic, map_array

def init_ccp4_header(ccp4_map : gemmi.Ccp4Map, array : np.ndarray) -> dict:
    """
    fn init_ccp4_header

    Creates a header based in nmrPype format using a ccp4 file

    Parameters
    ----------
    ccp4_map : gemmi.Ccp4Map
        Target ccp4 map data
    array : np.ndarray
        Array generated from ccp4_map grid
    """
    # initialize header dictionary
    dic = HEADER_TEMPLATE

    # Identify how many dimensions there are
    dim_count = array.ndim

    for dim in range(1,dim_count+1):
        size = float(array.shape[-1*dim])
        # set NDSIZE, APOD, SW to SIZE
        # OBS is default 1
        # CAR is 0
        # ORIG is 0
        size_param = paramSyntax('NDSIZE', dim)
        apod_param = paramSyntax('NDAPOD', dim)
        sw_param = paramSyntax('NDSW', dim)
        ft_flag = paramSyntax('NDFTFLAG', dim)

        # Set parameters in the dictionary
        dic[size_param] = size
        dic[apod_param] = size
        if dim == 1:
            dic['FDREALSIZE'] = size
        dic[sw_param] = size

        # Consider the data in frequency domain, 1 for frequency
        dic[ft_flag] = 1 

    # Miscellaneous parameters
    slices = np.prod(array.shape[:-1])
    dic['FDSLICECOUNT'] = slices if slices != 1 else 0
    dic['FDSLICECOUNT1'] = slices if slices != 1 else 0

    dic['FDDIMCOUNT'] = float(dim_count)

    dic['FDMAX'] = float(np.max(array))
    dic['FDMIN'] = float(np.min(array))

    dic['FDMAX'] = float(np.max(array))
    dic['FDMIN'] = float(np.min(array))
    
    # Update pipe flag for dim 3 or higher
    if dim_count >= 3:
        dic['FDPIPEFLAG'] = 1
        
    return dic


def paramSyntax(param : str, dim : int) -> str :
    """
    fn paramSyntax

    local verison of updateHeaderSyntax found in DataFrame.py

    Parameters
    ----------
    param : str
        Starter parameter string before modification

    dim : int
        Target parameter dimension

    Returns
    -------
    param : str
        Parameter string with updated syntax
    """
    if dim:
        # The try clause is omitted because we expect the paramter to exist
        # Since this function is not meant to be user-accessed
        dim = int(dim-1)
        if param.startswith('ND'):
            dimCode =  int(FDDIMORDER[dim])
            param = 'FDF' + str(dimCode) + param[2:]
    else:
        # If unspecified dimension for nd, then set dimension
        if param.startswith('ND'):
            dimCode =  int(FDDIMORDER[0])
            param = 'FDF' + str(dimCode) + param[2:]

    # Check if the param ends with size and fix to match sizes
    if param.endswith('SIZE'):
        match param:
            case 'FDF2SIZE':
                param = 'FDSIZE'
            case 'FDF1SIZE':
                param = 'FDSPECNUM'
    return param

# Originally I was going to load with json, but I am unsure which is better to itilize
HEADER_TEMPLATE = {"FDMAGIC": 0.0,
"FDFLTFORMAT": 4008636160.0,
"FDFLTORDER": 2.3450000286102295,
"FDSIZE": 0.0,
"FDREALSIZE": 0.0,
"FDSPECNUM": 1.0,
"FDQUADFLAG": 1.0,
"FD2DPHASE": 3.0,
"FDTRANSPOSED": 0.0,
"FDDIMCOUNT": 1.0,
"FDDIMORDER": [2.0, 1.0, 3.0, 4.0],
"FDDIMORDER1": 2.0,
"FDDIMORDER2": 1.0,
"FDDIMORDER3": 3.0,
"FDDIMORDER4": 4.0,
"FDNUSDIM": 0.0,
"FDPIPEFLAG": 0.0,
"FDCUBEFLAG": 0.0,
"FDPIPECOUNT": 0.0,
"FDSLICECOUNT": 0.0,
"FDSLICECOUNT1": 0.0,
"FDFILECOUNT": 1.0,
"FDTHREADCOUNT": 0.0,
"FDTHREADID": 0.0,
"FDFIRSTPLANE": 0.0,
"FDLASTPLANE": 0.0,
"FDPARTITION": 0.0,
"FDPLANELOC": 0.0,
"FDMAX": 0.0,
"FDMIN": 0.0,
"FDSCALEFLAG": 1.0,
"FDDISPMAX": 0.0,
"FDDISPMIN": 0.0,
"FDPTHRESH": 0.0,
"FDNTHRESH": 0.0,
"FDUSER1": 0.0,
"FDUSER2": 0.0,
"FDUSER3": 0.0,
"FDUSER4": 0.0,
"FDUSER5": 0.0,
"FDUSER6": 0.0,
"FDLASTBLOCK": 0.0,
"FDCONTBLOCK": 0.0,
"FDBASEBLOCK": 0.0,
"FDPEAKBLOCK": 0.0,
"FDBMAPBLOCK": 0.0,
"FDHISTBLOCK": 0.0,
"FD1DBLOCK": 0.0,
"FDMONTH": 4.0,
"FDDAY": 27.0,
"FDYEAR": 2002.0,
"FDHOURS": 10.0,
"FDMINS": 23.0,
"FDSECS": 30.0,
"FDMCFLAG": 0.0,
"FDNOISE": 0.0,
"FDRANK": 0.0,
"FDTEMPERATURE": 0.0,
"FDPRESSURE": 0.0,
"FD2DVIRGIN": 1.0,
"FDTAU": 0.0,
"FDDOMINFO": 0.0,
"FDMETHINFO": 0.0,
"FDSCORE": 0.0,
"FDSCANS": 0.0,
"FDSRCNAME": "",
"FDUSERNAME": "",
"FDOPERNAME": "",
"FDTITLE": "",
"FDCOMMENT": "",
"FDF2LABEL": "X",
"FDF2APOD": 0.0,
"FDF2SW": 0.0,
"FDF2OBS": 1.0,
"FDF2OBSMID": 0.0,
"FDF2ORIG": 0.0,
"FDF2UNITS": 0.0,
"FDF2QUADFLAG": 1.0,
"FDF2FTFLAG": 0.0,
"FDF2AQSIGN": 0.0,
"FDF2CAR": 0.0,
"FDF2CENTER": 0.0,
"FDF2OFFPPM": 0.0,
"FDF2P0": 0.0,
"FDF2P1": 0.0,
"FDF2APODCODE": 0.0,
"FDF2APODQ1": 0.0,
"FDF2APODQ2": 0.0,
"FDF2APODQ3": 0.0,
"FDF2LB": 0.0,
"FDF2GB": 0.0,
"FDF2GOFF": 0.0,
"FDF2C1": 0.0,
"FDF2APODDF": 0.0,
"FDF2ZF": 0.0,
"FDF2X1": 0.0,
"FDF2XN": 0.0,
"FDF2FTSIZE": 0.0,
"FDF2TDSIZE": 0.0,
"FDDMXVAL": 0.0,
"FDDMXFLAG": 0.0,
"FDDELTATR": 0.0,
"FDF1LABEL": "Y",
"FDF1APOD": 0.0,
"FDF1SW": 0.0,
"FDF1OBS": 1.0,
"FDF1OBSMID": 0.0,
"FDF1ORIG": 0.0,
"FDF1UNITS": 0.0,
"FDF1FTFLAG": 0.0,
"FDF1AQSIGN": 0.0,
"FDF1QUADFLAG": 1.0,
"FDF1CAR": 0.0,
"FDF1CENTER": 1.0,
"FDF1OFFPPM": 0.0,
"FDF1P0": 0.0,
"FDF1P1": 0.0,
"FDF1APODCODE": 0.0,
"FDF1APODQ1": 0.0,
"FDF1APODQ2": 0.0,
"FDF1APODQ3": 0.0,
"FDF1LB": 0.0,
"FDF1GB": 0.0,
"FDF1GOFF": 0.0,
"FDF1C1": 0.0,
"FDF1ZF": 0.0,
"FDF1X1": 0.0,
"FDF1XN": 0.0,
"FDF1FTSIZE": 0.0,
"FDF1TDSIZE": 0.0,
"FDF3LABEL": "Z",
"FDF3APOD": 0.0,
"FDF3OBS": 1.0,
"FDF3OBSMID": 0.0,
"FDF3SW": 0.0,
"FDF3ORIG": 0.0,
"FDF3FTFLAG": 0.0,
"FDF3AQSIGN": 0.0,
"FDF3SIZE": 1.0,
"FDF3QUADFLAG": 1.0,
"FDF3UNITS": 0.0,
"FDF3P0": 0.0,
"FDF3P1": 0.0,
"FDF3CAR": 0.0,
"FDF3CENTER": 1.0,
"FDF3OFFPPM": 0.0,
"FDF3APODCODE": 0.0,
"FDF3APODQ1": 0.0,
"FDF3APODQ2": 0.0,
"FDF3APODQ3": 0.0,
"FDF3LB": 0.0,
"FDF3GB": 0.0,
"FDF3GOFF": 0.0,
"FDF3C1": 0.0,
"FDF3ZF": 0.0,
"FDF3X1": 0.0,
"FDF3XN": 0.0,
"FDF3FTSIZE": 0.0,
"FDF3TDSIZE": 0.0,
"FDF4LABEL": "A",
"FDF4APOD": 0.0,
"FDF4OBS": 1.0,
"FDF4OBSMID": 0.0,
"FDF4SW": 0.0,
"FDF4ORIG": 0.0,
"FDF4FTFLAG": 0.0,
"FDF4AQSIGN": 0.0,
"FDF4SIZE": 1.0,
"FDF4QUADFLAG": 1.0,
"FDF4UNITS": 0.0,
"FDF4P0": 0.0,
"FDF4P1": 0.0,
"FDF4CAR": 0.0,
"FDF4CENTER": 1.0,
"FDF4OFFPPM": 0.0,
"FDF4APODCODE": 0.0,
"FDF4APODQ1": 0.0,
"FDF4APODQ2": 0.0,
"FDF4APODQ3": 0.0,
"FDF4LB": 0.0,
"FDF4GB": 0.0,
"FDF4GOFF": 0.0,
"FDF4C1": 0.0,
"FDF4ZF": 0.0,
"FDF4X1": 0.0,
"FDF4XN": 0.0,
"FDF4FTSIZE": 0.0,
"FDF4TDSIZE": 0.0}