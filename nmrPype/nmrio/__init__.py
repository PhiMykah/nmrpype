import numpy as np
from utils import catchError, FileIOError
from .read import *
from .write import *
from .fileiobase import *

"""
nmrio

Handles all of the input and output functions regarding
    the NMR file format
"""

r = [read, read_1D, read_2D, read_3D, read_4D, read_stream,
     read_lowmem, read_lowmem_2D,read_lowmem_3D, read_lowmem_4D,
     read_lowmem_stream]
w = [write, write_single, write_3D, write_4D,
     write_lowmem, write_lowmem_2D, write_lowmem_3D, write_lowmem_4D,
     write_lowmem_3Ds, write_lowmem_4Ds]

base = []

all = []
all.extend(m.__name__ for m in r)
all.extend(m.__name__ for m in w)
all.extend(m.__name__ for m in base)

__all__ = all

def readFromFile(file : str) -> tuple[dict,np.ndarray]:
    """
    fn readFromFile

    set the header object and data array based on the input file

    Parameters
    ----------
    file : str
        NMR data format file to read from

    Returns
    -------
    dic : dict
        Header Dictionary

    data : np.ndarray
        NMR data represented by an ndarray
    """
    dic = {}
    data = None
    try:
        # Utilize nmrglue to read 
        dic, data = read(file)
    except Exception as e:
        e.args = (" ".join(str(arg) for arg in e.args),)
        catchError(e, new_e=FileIOError, msg="Unable to read File!", ePrint=False)
    return dic, data


def readFromBuffer() -> bool:
    return True


def writeToFile() -> bool:
    return True


def writeToBuffer() -> bool:
    return True