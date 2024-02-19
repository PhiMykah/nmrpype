import gemmi
from utils import catchError
import numpy as np


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
    dic = {}

    return dic, map_array
