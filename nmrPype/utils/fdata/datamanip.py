################
#This code is a modification of code soruced from 'nmrglue' by Johnathan J Halmus and other contributors.
#J.J. Helmus, C.P. Jaroniec, Nmrglue: An open source Python package for the analysis of multidimensional NMR data, 
#J. Biomol. NMR 2013, 55, 355-367, http://dx.doi.org/10.1007/s10858-013-9718-x.
################

import numpy as np
import struct
import os, io
from warnings import warn
from ...nmrio.fileiobase import *

# Type definitions
type InputFile = str | os.pathlib.Path | bytes | io.BytesIO

def fdata2dic(fdata : np.ndarray) -> dict:
    """
    Convert a fdata array to fdata dictionary.

    Converts the raw 512x4-byte NMRPipe header into a python dictionary
    with keys as given in fdatap.h
    
    See :py:func:`dic2fdata` for the inverse function.

    Parameters
    ----------
    fdata : ndarray
        512x4-byte array header

    Returns
    -------
    dic : dict
        python dictionary representation of NMRPipe header
    """
    dic = dict()

    # Populate the dictionary with FDATA which contains numbers
    for key in fdata_dic.keys():
        dic[key] = float(fdata[int(fdata_dic[key])])

    # make the FDDIMORDER
    dic["FDDIMORDER"] = [dic["FDDIMORDER1"], dic["FDDIMORDER2"],
                         dic["FDDIMORDER3"], dic["FDDIMORDER4"]]

    def _unpack_str(fmt, d):
        return struct.unpack(fmt, d)[0].decode().strip('\x00')

    # Populate the dictionary with FDATA which contains strings
    dic["FDF2LABEL"] = _unpack_str('8s', fdata[16:18])
    dic["FDF1LABEL"] = _unpack_str('8s', fdata[18:20])
    dic["FDF3LABEL"] = _unpack_str('8s', fdata[20:22])
    dic["FDF4LABEL"] = _unpack_str('8s', fdata[22:24])
    dic["FDSRCNAME"] = _unpack_str('16s', fdata[286:290])
    dic["FDUSERNAME"] = _unpack_str('16s', fdata[290:294])
    dic["FDTITLE"] = _unpack_str('60s', fdata[297:312])
    dic["FDCOMMENT"] = _unpack_str('160s', fdata[312:352])
    dic["FDOPERNAME"] = _unpack_str('32s', fdata[464:472])
    return dic


def dic2fdata(dic : dict) -> np.ndarray:
    """
    Converts a NMRPipe dictionary into an array.
    See :py:func:`fdata2dic` for the inverse function. 

    Parameters
    ----------
    dic : dict
        python dictionary representation of NMRPipe header

    Returns
    -------
    fdata : ndarray
        512x4-byte array header   
    """
    # A 512 4-byte array to hold the nmrPipe header data
    fdata = np.zeros(512, 'float32')

    # Populate the array with the simple numbers
    for key in fdata_nums.keys():
        fdata[int(fdata_dic[key])] = float(dic[key])

    # Check that FDDIMORDER didn't overwrite FDDIMORDER1
    fdata[int(fdata_dic["FDDIMORDER1"])] = dic["FDDIMORDER1"]

    # Pack the various strings into terminated strings of the correct length
    # then into floats in the fdata array
    fdata[16:18] = struct.unpack(
        '2f', struct.pack('8s', dic["FDF2LABEL"].encode()))
    fdata[18:20] = struct.unpack(
        '2f', struct.pack('8s', dic["FDF1LABEL"].encode()))
    fdata[20:22] = struct.unpack(
        '2f', struct.pack('8s', dic["FDF3LABEL"].encode()))
    fdata[22:24] = struct.unpack(
        '2f', struct.pack('8s', dic["FDF4LABEL"].encode()))

    # and the longer strings (typically blank)
    fdata[286:290] = struct.unpack(
        '4f', struct.pack('16s', dic["FDSRCNAME"].encode()))
    fdata[290:294] = struct.unpack(
        '4f', struct.pack('16s', dic["FDUSERNAME"].encode()))
    fdata[297:312] = struct.unpack(
        '15f', struct.pack('60s', dic["FDTITLE"].encode()))
    fdata[312:352] = struct.unpack(
        '40f', struct.pack('160s', dic["FDCOMMENT"].encode()))
    fdata[464:472] = struct.unpack(
        '8f', struct.pack('32s', dic["FDOPERNAME"].encode()))

    return fdata


#################################
# raw reading of data from file #
#################################


def get_fdata(filename : InputFile) -> np.ndarray:
    """
    Get an array of length 512-bytes holding NMRPipe header.

    Parameters
    ----------
    filename : InputFile [bytes/string/path-like]
        Input stream to read fdata from

    Returns
    -------
    fdata : ndarray
        512x4-byte numpy array for header
    """
    if type(filename) is bytes:
        fdata = np.frombuffer(filename, dtype=np.float32, count=512)
    else:
        fdata = np.fromfile(filename, 'float32', 512)

    if fdata[2] - 2.345 > 1e-6:    # fdata[2] should be 2.345
        fdata = fdata.byteswap()
    return fdata


def get_fdata_data(filename : InputFile) -> tuple[np.ndarray, np.ndarray]:
    """
    Get fdata and data array one after another 

    Parameters
    ----------
    filename : InputFile [bytes/string/path-like]
        Input stream to read fdata from

    Returns
    -------
    fdata : ndarray
        512x4-byte header array
    data : ndarray
        1D array representation of NMR data 
    """
    if type(filename) is bytes:
        data = np.frombuffer(filename, dtype=np.float32)
    else:
        data = np.fromfile(filename, 'float32')

    if data[2] - 2.345 > 1e-6:  # check for byteswap
        data = data.byteswap()
    return data[:512], data[512:]


def reshape_data(data : np.ndarray, shape : tuple) -> np.ndarray:
    """
    Reshape data or return 1D data after warning.

    Parameters
    ----------
    data : ndarray
        1D numpy array data

    shape : tuple
        Target reshape

    Returns
    -------
    ndarray
        Data shaped to match input shape
    """
    try:
        return data.reshape(shape)
    except ValueError:
        try: 
            # For 1-D case where imaginary data is zeros appended to the end of the list
            return data[:shape[0]].reshape(shape)
        except ValueError:
            warn(str(data.shape) + "cannot be shaped into" + str(shape))
            return data


def unshape_data(data : np.ndarray) -> np.ndarray:
    """
    Return 1D version of data.
    """
    return data.flatten()


def unappend_data(data : np.ndarray) -> np.ndarray:
    """
    Return complex data with last axis (-1) unappended.

    Data should have imaginary data vector appended to real data vector

    See :py:func:`append_data` for the inverse operation.

    Parameters
    ----------
    data : np.ndarray
        NMR data with complex direct dimension concatenating real and imaginary points
    
    Returns
    -------
    ndarray
        NMR data with direct dimension represented as complex numpy values
    """
    h = int(data.shape[-1] / 2)
    return np.array(data[..., :h] + data[..., h:] * 1.j, dtype="complex64")


def append_data(data : np.ndarray) -> np.ndarray:
    """
    Return data with last axis (-1) appended.

    Data should be complex
    
    See :py:func:`unappend_data` for the inverse operation.

    Parameters
    ----------
    data : np.ndarray
        NMR data with complex direct dimension represented as complex numpy values

    Returns
    -------
    ndarray
        NMR data with complex direct dimension concatenating real and imaginary points
    """
    return np.concatenate((data.real, data.imag), axis=-1)


def find_shape(dic : dict) -> tuple:
    """
    Find the shape (tuple) of data in a NMRPipe file from parameters.

    The last dimension of the tuple is length of the data in the file, the
    actual length of the data matrix may be half of this if the data is
    complex.

    Parameters
    ----------
    dic : dict
        NMR data header as python dictionary for obtaining correct shape
    Returns
    -------
    tuple
        1-tuple is returned for 1D data,
        2-tuple for 2D and non-stream 3D/4D data,
        3-tuple or 4-tuple for stream 3D/4D data.
    """
    if dic["FDDIMCOUNT"] == 1:  # 1D Data
        if dic["FDF2QUADFLAG"] == 1:
            multi = 1.0
        else:
            multi = 2.0

        dim1 = int(dic["FDSIZE"] * multi)
        return (dim1)
    else:  # 2D+ Data
        if dic["FDF1QUADFLAG"] == 1 and dic["FDTRANSPOSED"] == 1:
            multi = 1.0
        elif dic["FDF2QUADFLAG"] == 1 and dic["FDTRANSPOSED"] == 0:
            multi = 1.0
        else:
            multi = 2.0

        dim1 = int(dic["FDSIZE"] * multi)
        dim2 = int(dic["FDSPECNUM"])

        # when the direct dim is singular and the indirect
        # dim is complex FDSPECNUM is half of the correct value
        if dic["FDQUADFLAG"] == 0 and multi == 1.0:
            dim2 = dim2 * 2

        # check for 3D/4D data stream format files (made using xyz2pipe)
        if dic["FDDIMCOUNT"] == 3 and dic["FDPIPEFLAG"] != 0:
            dim3 = int(dic["FDF3SIZE"])
            return (dim3, dim2, dim1)
        if dic["FDDIMCOUNT"] == 4 and dic["FDPIPEFLAG"] != 0:
            dim3 = int(dic["FDF3SIZE"])
            dim4 = int(dic["FDF4SIZE"])
            return (dim4, dim3, dim2, dim1)

        return (dim2, dim1)
    

###############
# put to disk #
###############


def put_fdata(fh, fdata : np.ndarray):
    """
    Put NMR data, fdata, to a NMRPipe file described by file object fh.
    """
    if fdata.dtype != 'float32':
        raise TypeError('fdata.dtype is not float32')
    fh.write(fdata.tobytes())


def put_trace(fh, trace : np.ndarray):
    """
    Put a trace (real or complex) to NMRPipe file described by file object fh.
    """
    if trace.dtype == 'complex64':
        trace = append_data(trace)
    if trace.dtype != 'float32':
        raise TypeError('trace.dtype is not float32')
    fh.write(trace.tobytes())


def put_data(filename, fdata, data, overwrite=False):
    """
    Put fdata and data to 2D NMRPipe.
    """
    if data.dtype != 'float32':
        print(f"Data type: {data.dtype}", file=sys.stderr)
        raise TypeError('data.dtype is not float32')
    if fdata.dtype != 'float32':
        print(f"Data type: {fdata.dtype}", file=sys.stderr)
        raise TypeError('fdata.dtype is not float32')

    # write the file
    f = open_towrite(filename, overwrite=overwrite)
    f.write(fdata.tobytes())
    f.write(data.tobytes())
    f.close()

def get_trace(fhandle, ntrace, pts, bswap, cplex):
    """
    Get a single trace from a NMRPipe file

    Parameters
    ----------
    fhandle : file object
        File object of open NMRPipe file.
    ntrace : int
        Trace numbers (starting from 0).
    pts : int
        Number of points in trace, R|I.
    bswap : bool
        True to perform byteswap on trace.
    cplex : bool
        True to unappend imaginary data.

    """
    if cplex:
        tpts = pts * 2  # read twice as many points if data is complex
    else:
        tpts = pts

    fhandle.seek(4 * (512 + ntrace * tpts))  # seek to the start of the trace
    trace = np.fromfile(fhandle, 'float32', tpts)

    if bswap:
        trace = trace.byteswap()
    if cplex:
        return unappend_data(trace)
    else:
        return trace
    

###########
# Classes #
###########
    
class pipe_2d(data_nd):
    """
    Emulate a ndarray objects without loading data into memory for low memory
    reading of 2D NMRPipe files.

    * slicing operations return ndarray objects.
    * can iterate over with expected results.
    * transpose and swapaxes methods create a new objects with correct axes
      ordering.
    * has ndim, shape, and dtype attributes.

    Parameters
    ----------
    filename : str
        Filename of 2D NMRPipe file.
    order : tuple
        Ordering of axes against file.

    """

    def __init__(self, filename, order=(0, 1)):
        """
        Create and set up object
        """
        # read and parse the NMRPipe header
        fdata = get_fdata(filename)  # get the header data
        if fdata[2] - 2.345 > 1e-6:  # check if byteswapping will be necessary
            self.bswap = True
        else:
            self.bswap = False

        dic = fdata2dic(fdata)  # create the dictionary
        fshape = list(find_shape(dic))

        # set object attributes
        self.filename = filename
        self.order = order

        # check last axis quadrature
        fn = "FDF" + str(int(dic["FDDIMORDER1"]))
        if dic[fn + "QUADFLAG"] == 1.0:
            self.cplex = False
            self.dtype = np.dtype('float32')
        else:
            self.cplex = True
            self.dtype = np.dtype('complex64')
            fshape[1] = fshape[1] // 2

        # finalize
        self.fshape = tuple(fshape)
        self.__setdimandshape__()   # set ndim and shape attributes

    def __fcopy__(self, order):
        """
        Create a copy
        """
        n = pipe_2d(self.filename, order)
        return n

    def __fgetitem__(self, slices):
        """
        Return ndarray of selected values.

        (sY, sX) is a well formatted tuple of slices
        """
        sY, sX = slices
        f = open(self.filename, 'rb')  # open the file for reading

        # determine which objects should be selected
        lenY, lenX = self.fshape
        xch = range(lenX)[sX]
        ych = range(lenY)[sY]

        # create an empty array to store the selected slice
        out = np.empty((len(ych), len(xch)), dtype=self.dtype)

        # read in the data trace by trace
        for yi, y in enumerate(ych):
            ntrace = y
            trace = get_trace(f, ntrace, lenX, self.bswap, self.cplex)
            out[yi] = trace[sX]
        f.close()
        return out


# There are two types of NMRPipe 3D files:
# 1) streams which are single file data sets made with xyz2pipe.
# 2) multiple file data test, names test%03d.ft3, etc.
# Low memory objects exist for both, choose the correct one, or let read
# do it for you.


class pipe_3d(data_nd):
    """
    Emulate a ndarray objects without loading data into memory for low memory
    reading of 3D NMRPipe files (multiple file data sets).

    * slicing operations return ndarray objects.
    * can iterate over with expected results.
    * transpose and swapaxes methods create a new objects with correct axes
      ordering.
    * has ndim, shape, and dtype attributes.

    Parameters
    ----------
    filemask : str
        Filename of 3D NMRPipe file. Should contain one formatter '%'
        operator.
    order : tuple
        Ordering of axes against file.
    fcheck : bool, optional.
        True to perform a basic check to see if all files expected for the data
        set exist.  Raises a IOError if files are missing. Default is False.

    """

    def __init__(self, filemask, order=(0, 1, 2), fcheck=False):
        """
        Create and set up object, check that files exist if fcheck is True
        """
        filename = filemask % 1

        # read and parse the NMRPipe header in the first file of the 3D
        fdata = get_fdata(filename)  # get the header data
        if fdata[2] - 2.345 > 1e-6:  # check if byteswapping will be necessary
            self.bswap = True
        else:
            self.bswap = False

        # find the shape of the first two dimensions
        dic = fdata2dic(fdata)  # create the dictionary
        fshape = list(find_shape(dic))[-2:]

        # find the length of the third dimension
        f3 = "FDF" + str(int(dic["FDDIMORDER3"]))
        quadrature_factor = [2, 1][int(dic[f3 + 'QUADFLAG'])]

        #Checking whether "nmrPipe -fn EXT ..." has been applied to z-dim or not.
        #If EXT has been applied, FDF*XN is not zero.
        #If z-dim is in time-domain, data-size given by FDF*X1 and FDF*XN has to be doubled.
        if dic[f3 + 'FTFLAG']:

            if int(dic[f3 + 'XN']) == 0:
                lenZ = int(dic[f3 + 'FTSIZE'] * quadrature_factor)
            else:
                lenZ = int(dic[f3 + 'XN']) - int(dic[f3 + 'X1']) + 1

        else:
            if int(dic[f3 + 'XN']) == 0:
                lenZ = int(dic[f3 + 'TDSIZE'] * quadrature_factor)
            else:
                lenZ = 2*(int(dic[f3 + 'XN']) - int(dic[f3 + 'X1']) + 1)

        fshape.insert(0, lenZ)   # insert as leading size of fshape

        # check that all files exist if fcheck is set
        if fcheck:
            for i in range(1, lenZ + 1):
                if os.path.exists(filemask % i) is False:
                    raise OSError("File not found: " + str(filemask % i))

        # check last axis quadrature
        fn = "FDF" + str(int(dic["FDDIMORDER1"]))
        if dic[fn + "FTFLAG"] == 1.0:
            self.cplex = False
            self.dtype = np.dtype('float32')
        else:
            self.cplex = True
            self.dtype = np.dtype('complex64')
            fshape[2] = fshape[2] // 2

        # finalize
        self.filemask = filemask
        self.order = order
        self.fshape = fshape
        self.__setdimandshape__()  # set ndim and shape attributes

    def __fcopy__(self, order):
        """
        Create a copy
        """
        n = pipe_3d(self.filemask, order)
        return n

    def __fgetitem__(self, slices):
        """
        Return ndarray of selected values

        (sZ, sY, sX) is a well formatted tuple of slices
        """
        sZ, sY, sX = slices
        # determine which objects should be selected
        lenZ, lenY, lenX = self.fshape
        xch = range(lenX)[sX]
        ych = range(lenY)[sY]
        zch = range(lenZ)[sZ]

        # create an empty array to store the selected slice
        out = np.empty((len(zch), len(ych), len(xch)), dtype=self.dtype)

        # read in the data file by file and trace by trace
        for zi, z in enumerate(zch):
            # open the Z axis file
            f = open(self.filemask % (z + 1), 'rb')
            for yi, y in enumerate(ych):
                ntrace = y
                trace = get_trace(f, ntrace, lenX, self.bswap, self.cplex)
                out[zi, yi] = trace[sX]
            f.close()
        return out


class pipestream_3d(data_nd):
    """
    Emulate a ndarray objects without loading data into memory for low memory
    reading of 3D NMRPipe data stream files (one file data sets).

    * slicing operations return ndarray objects.
    * can iterate over with expected results.
    * transpose and swapaxes methods create a new objects with correct axes
      ordering.
    * has ndim, shape, and dtype attributes.

    Parameters
    ----------
    filename : str
        Filename of 3D NMRPipe stream file.
    order : tuple
        Ordering of axes against file.

    """
    def __init__(self, filename, order=(0, 1, 2)):
        """
        Create and set up object
        """
        # read and parse the NMRPipe header
        fdata = get_fdata(filename)  # get the header data
        if fdata[2] - 2.345 > 1e-6:  # check if byteswapping will be necessary
            self.bswap = True
        else:
            self.bswap = False

        dic = fdata2dic(fdata)  # create the dictionary
        fshape = list(find_shape(dic))

        # check last axis quadrature
        fn = "FDF" + str(int(dic["FDDIMORDER1"]))
        if dic[fn + "QUADFLAG"] == 1.0:
            self.cplex = False
            self.dtype = np.dtype('float32')
        else:
            self.cplex = True
            self.dtype = np.dtype('complex64')
            fshape[2] = fshape[2] // 2

        # finalize
        self.filename = filename
        self.order = order
        self.fshape = tuple(fshape)
        self.__setdimandshape__()   # set ndim and shape attributes

    def __fcopy__(self, order):
        """
        Create a copy
        """
        n = pipestream_3d(self.filename, order)
        return n

    def __fgetitem__(self, slices):
        """
        Return ndarray of selected values

        (sZ, sY, sX) is a well formatted tuple of slices
        """
        sZ, sY, sX = slices
        f = open(self.filename, 'rb')  # open the file for reading

        # determine which objects should be selected
        lenZ, lenY, lenX = self.fshape
        xch = range(lenX)[sX]
        ych = range(lenY)[sY]
        zch = range(lenZ)[sZ]

        # create an empty array to store the selected slice
        out = np.empty((len(zch), len(ych), len(xch)), dtype=self.dtype)

        # read in the data trace by trace
        for zi, z in enumerate(zch):
            for yi, y in enumerate(ych):
                ntrace = y + z * lenY
                trace = get_trace(f, ntrace, lenX, self.bswap, self.cplex)
                out[zi, yi] = trace[sX]
        f.close()
        return out

# There are three types of NMRPipe 4D files:
# 1) streams which are single file data sets made with xyz2pipe.
# 2) single index multiple file data sets, named test%03d.ft4, etc.
# 3) two index muttuple file data sets, named test%02d%03d.ft2, made with
# pipe2xyz and conversion binary.
# Low memory objects exist for all three, choose the correct one, or let read
# do it for you.


class pipe_4d(data_nd):
    """
    Emulate a ndarray objects without loading data into memory for low memory
    reading of single/two index 4D NMRPipe data files.

    * slicing operations return ndarray objects.
    * can iterate over with expected results.
    * transpose and swapaxes methods create a new objects with correct axes
      ordering.
    * has ndim, shape, and dtype attributes.

    Parameters
    ----------
    filemask : str
        Filename of 4D NMRPipe file with one or two formatter (%) operators.
    order : tuple
        Ordering of axes against file.
    fcheck : bool, optional.
        True to perform a basic check to see if all files expected for the data
        set exist.  Raises a IOError if files are missing. Default is False.

    """
    def __init__(self, filemask, order=(0, 1, 2, 3), fcheck=False):
        """
        Create and set up object, check that files exist if fcheck is True
        """
        if filemask.count("%") == 1:
            self.singleindex = True
            filename = filemask % (1)
        elif filemask.count("%") == 2:
            self.singleindex = False
            filename = filemask % (1, 1)
        else:
            raise ValueError("bad filemask")

        # read and parse the NMRPipe header in the first file of the 3D
        fdata = get_fdata(filename)  # get the header data
        if fdata[2] - 2.345 > 1e-6:  # check if byteswapping will be necessary
            self.bswap = True
        else:
            self.bswap = False

        # find the shape of the first two dimensions
        dic = fdata2dic(fdata)  # create the dictionary
        fshape = list(find_shape(dic))[-2:]

        # find the length of the third dimension
        f3 = "FDF" + str(int(dic["FDDIMORDER3"]))
        quadrature_factor = [2, 1][int(dic[f3 + 'QUADFLAG'])]
        if dic[f3 + 'QUADFLAG']:
            lenZ = int(dic[f3 + 'FTSIZE'] * quadrature_factor)
        else:
            lenZ = int(dic[f3 + 'TDSIZE'] * quadrature_factor)
        fshape.insert(0, lenZ)   # insert as leading size of fshape

        # find the length of the fourth dimension
        f4 = "FDF" + str(int(dic["FDDIMORDER4"]))
        quadrature_factor = [2, 1][int(dic[f4 + 'QUADFLAG'])]
        if dic[f4 + 'QUADFLAG']:
            lenA = int(dic[f4 + 'FTSIZE'] * quadrature_factor)
        else:
            lenA = int(dic[f4 + 'TDSIZE'] * quadrature_factor)
        fshape.insert(0, lenA)   # insert as leading size of fshape

        # check that all files exist if fcheck is set
        if fcheck:
            for ai in range(1, lenA + 1):
                for zi in range(1, lenZ + 1):
                    if self.singleindex:
                        fname = filemask % (ai * lenZ + zi + 1)
                    else:
                        fname = filemask % (ai + 1, zi + 1)
                    if os.path.exists(fname) is False:
                        raise OSError("File not found: " + str(fname))

        # check last axis quadrature
        fn = "FDF" + str(int(dic["FDDIMORDER1"]))
        if dic[fn + "QUADFLAG"] == 1.0:
            self.cplex = False
            self.dtype = np.dtype('float32')
        else:
            self.cplex = True
            self.dtype = np.dtype('complex64')
            fshape[3] = fshape[3] // 2

        # finalize
        self.filemask = filemask
        self.order = order
        self.fshape = fshape
        self.__setdimandshape__()   # set ndim and shape attributes

    def __fcopy__(self, order):
        """
        Create a copy
        """
        n = pipe_4d(self.filemask, order)
        return n

    def __fgetitem__(self, slices):
        """
        Return ndarray of selected values

        (sZ, sY, sX) is a well formatted tuple of slices

        """
        sA, sZ, sY, sX = slices
        # determine which objects should be selected
        lenA, lenZ, lenY, lenX = self.fshape
        xch = range(lenX)[sX]
        ych = range(lenY)[sY]
        zch = range(lenZ)[sZ]
        ach = range(lenA)[sA]

        # create an empty array to store the selected slice
        out = np.empty((len(ach), len(zch), len(ych), len(xch)),
                       dtype=self.dtype)

        # read in the data file by file, trace by trace
        for ai, a in enumerate(ach):
            for zi, z in enumerate(zch):
                if self.singleindex:   # single index
                    f = open(self.filemask % (a * lenZ + z + 1), 'rb')
                else:   # two index
                    f = open(self.filemask % (a + 1, z + 1), 'rb')
                for yi, y in enumerate(ych):
                    ntrace = y
                    trace = get_trace(f, ntrace, lenX, self.bswap, self.cplex)
                    out[ai, zi, yi] = trace[sX]
                f.close()
        return out


class pipestream_4d(data_nd):
    """
    Emulate a ndarray objects without loading data into memory for low memory
    reading of 4D NMRPipe data streams (one file 4D data sets).

    * slicing operations return ndarray objects.
    * can iterate over with expected results.
    * transpose and swapaxes methods create a new objects with correct axes
      ordering.
    * has ndim, shape, and dtype attributes.

    Parameters
    ----------
    filename : str
        Filename of 4D NMRPipe stream file.
    order : tuple
        Ordering of axes against file.

    """

    def __init__(self, filename, order=(0, 1, 2, 3)):
        """
        Create and set up object
        """
        # read and parse the NMRPipe header
        fdata = get_fdata(filename)  # get the header data
        if fdata[2] - 2.345 > 1e-6:  # check if byteswapping will be necessary
            self.bswap = True
        else:
            self.bswap = False

        dic = fdata2dic(fdata)  # create the dictionary
        fshape = list(find_shape(dic))

        # set object attributes
        self.filename = filename
        self.order = order

        # check last axis quadrature
        fn = "FDF" + str(int(dic["FDDIMORDER1"]))
        if dic[fn + "QUADFLAG"] == 1.0:
            self.cplex = False
            self.dtype = np.dtype('float32')
        else:
            self.cplex = True
            self.dtype = np.dtype('complex64')
            fshape[3] = fshape[3] // 2

        # finalize
        self.fshape = tuple(fshape)
        self.__setdimandshape__()   # set ndim and shape attributes

    def __fcopy__(self, order):
        """
        Create a copy
        """
        n = pipestream_4d(self.filename, order)
        return n

    def __fgetitem__(self, slices):
        """
        Return ndarray of selected values

        (sA, sZ, sY, sX) is a well formatted tuple of slices

        """
        sA, sZ, sY, sX = slices
        f = open(self.filename, 'rb')  # open the file for reading

        # determine which objects should be selected
        lenA, lenZ, lenY, lenX = self.fshape
        xch = range(lenX)[sX]
        ych = range(lenY)[sY]
        zch = range(lenZ)[sZ]
        ach = range(lenA)[sA]

        # create an empty array to store the selected slice
        out = np.empty((len(ach), len(zch), len(ych), len(xch)),
                       dtype=self.dtype)

        # read in the data trace by trace
        for ai, a in enumerate(ach):
            for zi, z in enumerate(zch):
                for yi, y in enumerate(ych):
                    ntrace = y + z * lenY + a * lenY * lenZ
                    trace = get_trace(f, ntrace, lenX, self.bswap, self.cplex)
                    out[ai, zi, yi] = trace[sX]
        f.close()
        return out


# data, see fdata.h
fdata_nums = {
    'FDMAGIC': '0',
    'FDFLTFORMAT': '1',
    'FDFLTORDER': '2',

    'FDSIZE': '99',
    'FDREALSIZE': '97',
    'FDSPECNUM': '219',
    'FDQUADFLAG': '106',
    'FD2DPHASE': '256',

    'FDTRANSPOSED': '221',
    'FDDIMCOUNT': '9',

    'FDDIMORDER1': '24',
    'FDDIMORDER2': '25',
    'FDDIMORDER3': '26',
    'FDDIMORDER4': '27',

    'FDNUSDIM': '45',

    'FDPIPEFLAG': '57',
    'FDCUBEFLAG': '447',
    'FDPIPECOUNT': '75',
    'FDSLICECOUNT': '443',  # Also FDSLICECOUNT0
    'FDSLICECOUNT1': '446',
    'FDFILECOUNT': '442',

    'FDTHREADCOUNT': '444',
    'FDTHREADID': '445',

    'FDFIRSTPLANE': '77',
    'FDLASTPLANE': '78',
    'FDPARTITION': '65',

    'FDPLANELOC': '14',

    'FDMAX': '247',
    'FDMIN': '248',
    'FDSCALEFLAG': '250',
    'FDDISPMAX': '251',
    'FDDISPMIN': '252',
    'FDPTHRESH': '253',
    'FDNTHRESH': '254',

    'FDUSER1': '70',
    'FDUSER2': '71',
    'FDUSER3': '72',
    'FDUSER4': '73',
    'FDUSER5': '74',
    'FDUSER6': '76',

    'FDLASTBLOCK': '359',
    'FDCONTBLOCK': '360',
    'FDBASEBLOCK': '361',
    'FDPEAKBLOCK': '362',
    'FDBMAPBLOCK': '363',
    'FDHISTBLOCK': '364',
    'FD1DBLOCK': '365',

    'FDMONTH': '294',
    'FDDAY': '295',
    'FDYEAR': '296',
    'FDHOURS': '283',
    'FDMINS': '284',
    'FDSECS': '285',

    'FDMCFLAG': '135',
    'FDNOISE': '153',
    'FDRANK': '180',
    'FDTEMPERATURE': '157',
    'FDPRESSURE': '158',
    'FD2DVIRGIN': '399',
    'FDTAU': '199',
    'FDDOMINFO': '266',
    'FDMETHINFO': '267',

    'FDSCORE': '370',
    'FDSCANS': '371',

    'FDF2APOD': '95',
    'FDF2SW': '100',
    'FDF2OBS': '119',
    'FDF2OBSMID': '378',
    'FDF2ORIG': '101',
    'FDF2UNITS': '152',
    'FDF2QUADFLAG': '56',
    'FDF2FTFLAG': '220',
    'FDF2AQSIGN': '64',
    'FDF2CAR': '66',
    'FDF2CENTER': '79',
    'FDF2OFFPPM': '480',
    'FDF2P0': '109',
    'FDF2P1': '110',
    'FDF2APODCODE': '413',
    'FDF2APODQ1': '415',
    'FDF2APODQ2': '416',
    'FDF2APODQ3': '417',
    'FDF2LB': '111',
    'FDF2GB': '374',
    'FDF2GOFF': '382',
    'FDF2C1': '418',
    'FDF2APODDF': '419',
    'FDF2ZF': '108',
    'FDF2X1': '257',
    'FDF2XN': '258',
    'FDF2FTSIZE': '96',
    'FDF2TDSIZE': '386',

    'FDDMXVAL': '40',
    'FDDMXFLAG': '41',
    'FDDELTATR': '42',

    'FDF1APOD': '428',
    'FDF1SW': '229',
    'FDF1OBS': '218',
    'FDF1OBSMID': '379',
    'FDF1ORIG': '249',
    'FDF1UNITS': '234',
    'FDF1FTFLAG': '222',
    'FDF1AQSIGN': '475',
    'FDF1QUADFLAG': '55',
    'FDF1CAR': '67',
    'FDF1CENTER': '80',
    'FDF1OFFPPM': '481',
    'FDF1P0': '245',
    'FDF1P1': '246',
    'FDF1APODCODE': '414',
    'FDF1APODQ1': '420',
    'FDF1APODQ2': '421',
    'FDF1APODQ3': '422',
    'FDF1LB': '243',
    'FDF1GB': '375',
    'FDF1GOFF': '383',
    'FDF1C1': '423',
    'FDF1ZF': '437',
    'FDF1X1': '259',
    'FDF1XN': '260',
    'FDF1FTSIZE': '98',
    'FDF1TDSIZE': '387',

    'FDF3APOD': '50',
    'FDF3OBS': '10',
    'FDF3OBSMID': '380',
    'FDF3SW': '11',
    'FDF3ORIG': '12',
    'FDF3FTFLAG': '13',
    'FDF3AQSIGN': '476',
    'FDF3SIZE': '15',
    'FDF3QUADFLAG': '51',
    'FDF3UNITS': '58',
    'FDF3P0': '60',
    'FDF3P1': '61',
    'FDF3CAR': '68',
    'FDF3CENTER': '81',
    'FDF3OFFPPM': '482',
    'FDF3APODCODE': '400',
    'FDF3APODQ1': '401',
    'FDF3APODQ2': '402',
    'FDF3APODQ3': '403',
    'FDF3LB': '372',
    'FDF3GB': '376',
    'FDF3GOFF': '384',
    'FDF3C1': '404',
    'FDF3ZF': '438',
    'FDF3X1': '261',
    'FDF3XN': '262',
    'FDF3FTSIZE': '200',
    'FDF3TDSIZE': '388',

    'FDF4APOD': '53',
    'FDF4OBS': '28',
    'FDF4OBSMID': '381',
    'FDF4SW': '29',
    'FDF4ORIG': '30',
    'FDF4FTFLAG': '31',
    'FDF4AQSIGN': '477',
    'FDF4SIZE': '32',
    'FDF4QUADFLAG': '54',
    'FDF4UNITS': '59',
    'FDF4P0': '62',
    'FDF4P1': '63',
    'FDF4CAR': '69',
    'FDF4CENTER': '82',
    'FDF4OFFPPM': '483',
    'FDF4APODCODE': '405',
    'FDF4APODQ1': '406',
    'FDF4APODQ2': '407',
    'FDF4APODQ3': '408',
    'FDF4LB': '373',
    'FDF4GB': '377',
    'FDF4GOFF': '385',
    'FDF4C1': '409',
    'FDF4ZF': '439',
    'FDF4X1': '263',
    'FDF4XN': '264',
    'FDF4FTSIZE': '201',
    'FDF4TDSIZE': '389',
}


fdata_dic = {
    'FDMAGIC': '0',
    'FDFLTFORMAT': '1',
    'FDFLTORDER': '2',

    'FDSIZE': '99',
    'FDREALSIZE': '97',
    'FDSPECNUM': '219',
    'FDQUADFLAG': '106',
    'FD2DPHASE': '256',

    'FDTRANSPOSED': '221',
    'FDDIMCOUNT': '9',
    'FDDIMORDER': '24',

    'FDDIMORDER1': '24',
    'FDDIMORDER2': '25',
    'FDDIMORDER3': '26',
    'FDDIMORDER4': '27',

    'FDNUSDIM': '45',

    'FDPIPEFLAG': '57',
    'FDCUBEFLAG': '447',
    'FDPIPECOUNT': '75',
    'FDSLICECOUNT': '443',  # Also FDSLICECOUNT0
    'FDSLICECOUNT1': '446',
    'FDFILECOUNT': '442',

    'FDTHREADCOUNT': '444',
    'FDTHREADID': '445',

    'FDFIRSTPLANE': '77',
    'FDLASTPLANE': '78',
    'FDPARTITION': '65',

    'FDPLANELOC': '14',

    'FDMAX': '247',
    'FDMIN': '248',
    'FDSCALEFLAG': '250',
    'FDDISPMAX': '251',
    'FDDISPMIN': '252',
    'FDPTHRESH': '253',
    'FDNTHRESH': '254',

    'FDUSER1': '70',
    'FDUSER2': '71',
    'FDUSER3': '72',
    'FDUSER4': '73',
    'FDUSER5': '74',
    'FDUSER6': '76',

    'FDLASTBLOCK': '359',
    'FDCONTBLOCK': '360',
    'FDBASEBLOCK': '361',
    'FDPEAKBLOCK': '362',
    'FDBMAPBLOCK': '363',
    'FDHISTBLOCK': '364',
    'FD1DBLOCK': '365',

    'FDMONTH': '294',
    'FDDAY': '295',
    'FDYEAR': '296',
    'FDHOURS': '283',
    'FDMINS': '284',
    'FDSECS': '285',

    'FDMCFLAG': '135',
    'FDNOISE': '153',
    'FDRANK': '180',
    'FDTEMPERATURE': '157',
    'FDPRESSURE': '158',
    'FD2DVIRGIN': '399',
    'FDTAU': '199',
    'FDDOMINFO': '266',
    'FDMETHINFO': '267',

    'FDSCORE': '370',
    'FDSCANS': '371',

    'FDSRCNAME': '286',
    'FDUSERNAME': '290',
    'FDOPERNAME': '464',
    'FDTITLE': '297',
    'FDCOMMENT': '312',

    'FDF2LABEL': '16',
    'FDF2APOD': '95',
    'FDF2SW': '100',
    'FDF2OBS': '119',
    'FDF2OBSMID': '378',
    'FDF2ORIG': '101',
    'FDF2UNITS': '152',
    'FDF2QUADFLAG': '56',
    'FDF2FTFLAG': '220',
    'FDF2AQSIGN': '64',
    'FDF2CAR': '66',
    'FDF2CENTER': '79',
    'FDF2OFFPPM': '480',
    'FDF2P0': '109',
    'FDF2P1': '110',
    'FDF2APODCODE': '413',
    'FDF2APODQ1': '415',
    'FDF2APODQ2': '416',
    'FDF2APODQ3': '417',
    'FDF2LB': '111',
    'FDF2GB': '374',
    'FDF2GOFF': '382',
    'FDF2C1': '418',
    'FDF2APODDF': '419',
    'FDF2ZF': '108',
    'FDF2X1': '257',
    'FDF2XN': '258',
    'FDF2FTSIZE': '96',
    'FDF2TDSIZE': '386',

    'FDDMXVAL': '40',
    'FDDMXFLAG': '41',
    'FDDELTATR': '42',

    'FDF1LABEL': '18',
    'FDF1APOD': '428',
    'FDF1SW': '229',
    'FDF1OBS': '218',
    'FDF1OBSMID': '379',
    'FDF1ORIG': '249',
    'FDF1UNITS': '234',
    'FDF1FTFLAG': '222',
    'FDF1AQSIGN': '475',
    'FDF1QUADFLAG': '55',
    'FDF1CAR': '67',
    'FDF1CENTER': '80',
    'FDF1OFFPPM': '481',
    'FDF1P0': '245',
    'FDF1P1': '246',
    'FDF1APODCODE': '414',
    'FDF1APODQ1': '420',
    'FDF1APODQ2': '421',
    'FDF1APODQ3': '422',
    'FDF1LB': '243',
    'FDF1GB': '375',
    'FDF1GOFF': '383',
    'FDF1C1': '423',
    'FDF1ZF': '437',
    'FDF1X1': '259',
    'FDF1XN': '260',
    'FDF1FTSIZE': '98',
    'FDF1TDSIZE': '387',

    'FDF3LABEL': '20',
    'FDF3APOD': '50',
    'FDF3OBS': '10',
    'FDF3OBSMID': '380',
    'FDF3SW': '11',
    'FDF3ORIG': '12',
    'FDF3FTFLAG': '13',
    'FDF3AQSIGN': '476',
    'FDF3SIZE': '15',
    'FDF3QUADFLAG': '51',
    'FDF3UNITS': '58',
    'FDF3P0': '60',
    'FDF3P1': '61',
    'FDF3CAR': '68',
    'FDF3CENTER': '81',
    'FDF3OFFPPM': '482',
    'FDF3APODCODE': '400',
    'FDF3APODQ1': '401',
    'FDF3APODQ2': '402',
    'FDF3APODQ3': '403',
    'FDF3LB': '372',
    'FDF3GB': '376',
    'FDF3GOFF': '384',
    'FDF3C1': '404',
    'FDF3ZF': '438',
    'FDF3X1': '261',
    'FDF3XN': '262',
    'FDF3FTSIZE': '200',
    'FDF3TDSIZE': '388',

    'FDF4LABEL': '22',
    'FDF4APOD': '53',
    'FDF4OBS': '28',
    'FDF4OBSMID': '381',
    'FDF4SW': '29',
    'FDF4ORIG': '30',
    'FDF4FTFLAG': '31',
    'FDF4AQSIGN': '477',
    'FDF4SIZE': '32',
    'FDF4QUADFLAG': '54',
    'FDF4UNITS': '59',
    'FDF4P0': '62',
    'FDF4P1': '63',
    'FDF4CAR': '69',
    'FDF4CENTER': '82',
    'FDF4OFFPPM': '483',
    'FDF4APODCODE': '405',
    'FDF4APODQ1': '406',
    'FDF4APODQ2': '407',
    'FDF4APODQ3': '408',
    'FDF4LB': '373',
    'FDF4GB': '377',
    'FDF4GOFF': '385',
    'FDF4C1': '409',
    'FDF4ZF': '439',
    'FDF4X1': '263',
    'FDF4XN': '264',
    'FDF4FTSIZE': '201',
    'FDF4TDSIZE': '389',
}


"""
Copyright Notice and Statement for the nmrglue Project


Copyright (c) 2010-2015 Jonathan J. Helmus
All rights reserved.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:


a. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.


b. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.


c. Neither the name of the author nor the names of contributors may
   be used to endorse or promote products derived from this software
   without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""