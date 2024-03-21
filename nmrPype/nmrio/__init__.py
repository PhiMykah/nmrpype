import numpy as np
from .read import *
from .write import *
from .fileiobase import *
from .ccp4.ccp4 import load_ccp4_map

"""
nmrio

Handles all of the input and output functions regarding
    the NMR file format
"""

r = [read, read_1D, read_2D, read_3D, read_4D, read_stream,
     read_lowmem, read_lowmem_2D,read_lowmem_3D, read_lowmem_4D,
     read_lowmem_stream, load_ccp4_map]
w = [write, write_single, write_3D, write_4D,
     write_lowmem, write_lowmem_2D, write_lowmem_3D, write_lowmem_4D,
     write_lowmem_3Ds, write_lowmem_4Ds]

all = []
all.extend(m.__name__ for m in r)
all.extend(m.__name__ for m in w)


__all__ = all

######################
# Reading Operations #
######################

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
        # Utilize modified nmrglue code to read 
        dic, data = read(file)
    except Exception as e:
        from ..utils import catchError, FileIOError
        e.args = (" ".join(str(arg) for arg in e.args),)
        catchError(e, new_e=FileIOError, msg="Unable to read File!", ePrint=False)
    return dic, data


def readFromBuffer(buffer) -> tuple[dict,np.ndarray]:
    """
    fn readFromBuffer

    set the header object and data array based on the input file

    Parameters
    ----------
    buffer : sys.stdin or sys.stin.buffer
        input buffer to read from, read from stdin if the
            designated stdin does not have buffer

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
        # Utilize modified nmrglue code to read 
        dic, data = read(buffer)
    except Exception as e:
        from ..utils import catchError, FileIOError
        e.args = (" ".join(str(arg) for arg in e.args),)
        catchError(e, new_e=FileNotFoundError, msg="Unable to read buffer!", ePrint=False)
    return dic, data


######################
# Writing Operations #
######################

def writeToFile(data, output : str, overwrite : bool) -> int:
    """
    fn writeToFile

    Utilizes modified nmrglue code to output the Dataframe to a file
        in a NMR data format.

    Parameters
    ----------
    data : DataFrame
        DataFrame object to write out
    output : str
        Output file path represented as string
    overwrite : bool
        Choose whether or not to overwrite existing files for file output

    Returns
    -------
    Integer exit code (e.g. 0 success 1 fail)
    """
    # Set pipe count to zero for writing out to file
    data.updatePipeCount(reset=True)

    # Write out if possible
    try:
        write(output, data.getHeader(), data.getArray(), overwrite)
    except Exception as e:
        from ..utils import catchError, FileIOError
        catchError(e, new_e=FileIOError, msg="Unable to write to file!")

    return 0


def writeToBuffer(data, output, overwrite : bool) -> int:
    """
    fn writeToBuffer

    Utilizes modified nmrglue code to output the Dataframe
        to standard output or standard output buffer
        in a NMR data format.

    Parameters
    ----------
    data : DataFrame
        DataFrame object to write out
    output : sys.stdin or sys.stdin.buffer
        Output stream
    overwrite : bool
        Choose whether or not to overwrite existing files for file output

    Returns
    -------
    Integer exit code (e.g. 0 success 1 fail)
    """
    # Increment pipe count when outputting to buffer
    data.updatePipeCount()

    # Write to buffer based on number of dimensions
    match data.getArray().ndim:
        case 1:
            writeHeaderToBuffer(output, data.getHeader())
            writeDataToBuffer(output, data.getArray())

        case 2:
            writeHeaderToBuffer(output, data.getHeader())
            writeDataToBuffer(output, data.getArray())

        case 3:
            # First write header to buffer
            writeHeaderToBuffer(output, data.getHeader())

            # Write each data plane to buffer
            lenZ, lenY, lenX = data.getArray().shape
            for zi in range(lenZ):
                plane = data.getArray()[zi]
                writeDataToBuffer(output, plane)

        case 4:
            ######################
            # Currently Untested #
            ######################
            lenA, lenZ, lenY, lenX = data.getArray().shape
            # Might need to make new header
            writeHeaderToBuffer(output, data.getHeader())

            for ai in range(lenA):
                for zi in range(lenZ):
                    plane = data.getArray()[ai, zi]

                    # Update dictionary if needed 
                    if data.getParam("FDSCAPEFLAG") == 1:
                        data.setParam("FDMAX", plane.max())
                        data.setParam("FDDISPMAX", data.getParam("FDMAX"))
                        data.setParam("FDMIN", plane.min())
                        data.setParam("FDDISPMIN", data.getParam("FDMIN"))
                    writeDataToBuffer(output, plane)

    return 0

def writeHeaderToBuffer(output, header : dict) -> int:
    from ..utils.fdata import dic2fdata
    """
    fn writeHeaderToBuffer

    Writes the header to the standard output as bytes

    Parameters
    ----------
    output : sys.stdout or sys.stdout.buffer
        stream to send the header to
    dic : Dict
        Header represented as dictionary
            to write to the buffer

    Returns
    ----------
    Returns input header to binary output stream
    """
    try:
        # create the fdata array
        fdata = dic2fdata(header)

        """
        Put fdata and to 2D NMRPipe.
        """
        # check for proper datatype
        if fdata.dtype != 'float32':
                raise TypeError('fdata.dtype is not float32')
        
        # Write fdata to buffer
        output.write(fdata.tobytes())
    except Exception as e:
        from ..utils import catchError, FileIOError
        catchError(e, new_e=FileIOError, msg="An exception occured when attempting to write header to buffer!")


def writeDataToBuffer(output, array : np.ndarray) -> int:
    from ..utils.fdata import append_data
    """
    fn writeToBuffer

    Writes the nmrData and its header to the standard output as bytes

    Parameters
    ----------
    outFileName : str
        Output file or stream to send the header and nmr data to
    data : ndarray
        Nd

    Returns
    ----------
    Returns input data to binary output stream
    """
    try:
        """
        Modification of nmrglue.pipe source code for write to accomodate buffer
        """

        # load all data if the data is not a numpy ndarray
        if not isinstance(array, np.ndarray):
            array = array[:]

        # append imaginary and flatten
        if array.dtype == "complex64":
            array = append_data(array)
        array = array.flatten()

        """
        Put data to 2D NMRPipe.
        """
        # check for proper datatypes
        if array.dtype != 'float32':
            raise TypeError('data.dtype is not float32')
        
        # Write data to buffer
        output.write(array.tobytes())
        
    except Exception as e:
        from ..utils import catchError, FileIOError
        catchError(e, new_e=FileIOError, msg="An exception occured when attempting to write data to buffer!")
