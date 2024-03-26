################
#This code is a modification of code soruced from 'nmrglue' by Johnathan J Halmus and other contributors.
#J.J. Helmus, C.P. Jaroniec, Nmrglue: An open source Python package for the analysis of multidimensional NMR data, 
#J. Biomol. NMR 2013, 55, 355-367, http://dx.doi.org/10.1007/s10858-013-9718-x.
################

import numpy as np

################
# file reading #
################


def read(filename):
    """
    Read a NMRPipe file.

    For standard multi-file 3D/4D NMRPipe data sets, filename should be a
    filemask (for example "/ft/test%03d.ft3") with a "%" formatter. If only
    one file of a 3D/4D data set is provided only that 2D slice of the data is
    read (for example "/ft/test001.ft3" results in a 2D data set being read).

    NMRPipe data streams stored as files (one file 3D/4D data sets made using
    xyz2pipe) can be read by providing the file name of the stream. The entire
    data set is read into memory.

    An in memory binary stream (io.BytesIO) or bytes buffer containing an NMRPipe
    dataset can also be read.

    Parameters
    ----------
    filename : str | pathlib.Path | bytes | io.BytesIO
        Filename or filemask of NMRPipe file(s) to read. Binary io.BytesIO stream
        (e.g. open(filename, "rb")) or bytes buffer can also be provided

    Returns
    --------
    dic : dict
        Dictionary of NMRPipe parameters.
    data : ndarray
        Array of NMR data.

    See Also
    --------
    read_lowmem : NMRPipe file reading with minimal memory usage.
    write : Write a NMRPipe data to file(s).

    """
    from ..utils.fdata import get_fdata, fdata2dic

    if (type(filename) is bytes):
        filemask = None
    elif hasattr(filename, "read"):
        filename = filename.read()
        filemask = None
    elif hasattr(filename, "read_bytes") and (filename.name.count("%") == 0):
        filemask = None
    else:
        filename = str(filename)
        if filename.count("%") == 1:
            filemask = filename
            filename = filename % 1
        elif filename.count("%") == 2:
            filemask = filename
            filename = filename % (1, 1)
        else:
            filemask = None

    fdata = get_fdata(filename)
    dic = fdata2dic(fdata)
    order = dic["FDDIMCOUNT"]

    if order == 1:
        return read_1D(filename)
    if order == 2:
        return read_2D(filename)
    if dic["FDPIPEFLAG"] != 0:  # open streams
        return read_stream(filename)
    if filemask is None:     # if no filemask open as 2D
        return read_2D(filename)
    if order == 3:
        return read_3D(filemask)
    if order == 4:
        return read_4D(filemask)
    raise ValueError('unknown dimensionality: %s' % order)


def read_lowmem(filename):
    """
    Read a NMRPipe file with minimal memory usage.

    See :py:func:`read` for Parameters and information.

    Returns
    -------
    dic : dict
        Dictionary of NMRPipe parameters.
    data : array_like
        Low memory object which can access NMR data on demand.

    See Also
    --------
    read : Read NMRPipe files.
    write_lowmem : Write NMRPipe files using minimal amounts of memory.

    """
    from ..utils.fdata import get_fdata, fdata2dic

    if filename.count("%") == 1:
        filemask = filename
        filename = filename % 1
    elif filename.count("%") == 2:
        filemask = filename
        filename = filename % (1, 1)
    else:
        filemask = None

    fdata = get_fdata(filename)
    dic = fdata2dic(fdata)
    order = dic["FDDIMCOUNT"]

    if order == 1:
        return read_1D(filename)    # there is no 1D low memory option
    if order == 2:
        return read_lowmem_2D(filename)
    if dic["FDPIPEFLAG"] != 0:  # open streams
        return read_lowmem_stream(filename)
    if filemask is None:    # if no filemask open as 2D
        return read_lowmem_2D(filename)
    if order == 3:
        return read_lowmem_3D(filemask)
    if order == 4:
        return read_lowmem_4D(filemask)

    raise ValueError('unknown dimensionality: %s' % order)


# dimension specific reading
def read_1D(filename):
    """
    Read a 1D NMRPipe file.

    See :py:func:`read` for documentation.

    """
    from ..utils.fdata import get_fdata_data, fdata2dic, reshape_data, find_shape, unappend_data
    fdata, data = get_fdata_data(filename)   # get the fdata and data arrays
    dic = fdata2dic(fdata)  # convert the fdata block to a python dictionary
    data = reshape_data(data, find_shape(dic))    # reshape data

    # unappend imaginary data if needed
    if dic["FDF2QUADFLAG"] != 1:
        data = unappend_data(data)

    return (dic, data)


def read_2D(filename):
    """
    Read a 2D NMRPipe file or NMRPipe data stream.

    See :py:func:`read` for documentation.

    """
    from ..utils.fdata import get_fdata_data,fdata2dic,reshape_data,find_shape,unappend_data
    fdata, data = get_fdata_data(filename)   # get the fdata and data arrays
    dic = fdata2dic(fdata)  # convert the fdata block to a python dictionary
    data = reshape_data(data, find_shape(dic))    # reshape data

    # unappend imaginary data if needed
    if dic["FDTRANSPOSED"] == 1 and dic["FDF1QUADFLAG"] != 1:
        data = unappend_data(data)
    elif dic["FDTRANSPOSED"] == 0 and dic["FDF2QUADFLAG"] != 1:
        data = unappend_data(data)

    return (dic, data)


def read_lowmem_2D(filename):
    """
    Read a 2D NMRPipe file or NMRPipe data stream using minimal memory.

    See :py:func:`read_lowmem` for documentation

    """
    from ..utils.fdata import fdata2dic,get_fdata,pipe_2d,pipestream_3d,pipestream_4d
    dic = fdata2dic(get_fdata(filename))
    order = dic["FDDIMCOUNT"]
    if order == 2:
        data = pipe_2d(filename)
    if order == 3:
        data = pipestream_3d(filename)
    if order == 4:
        data = pipestream_4d(filename)
    return dic, data


def read_stream(filename):
    """
    Read a NMRPipe data stream (one file 3D or 4D files).

    See :py:func:`read` for documentation.

    """
    return read_2D(filename)


def read_lowmem_stream(filename):
    """
    Read a NMRPipe data stream using minimal memory.

    See :py:func:`read_lowmem` for documentation.
    """
    return read_lowmem_2D(filename)


def read_3D(filemask):
    """
    Read a 3D NMRPipe file.

    See :py:func:`read` for documentation.

    """
    dic, data = read_lowmem_3D(filemask)
    data = data[:, :, :]  # read all the data
    return dic, data


def read_lowmem_3D(filemask):
    """
    Read a 3D NMRPipe file using minimal memory.

    See :py:func:`read_lowmem` for documentation

    """
    from ..utils.fdata import pipe_3d,fdata2dic,get_fdata
    if '%' not in filemask:  # data streams should be read with read_stream
        return read_lowmem_stream(filemask)
    data = pipe_3d(filemask)    # create a new pipe_3d object
    dic = fdata2dic(get_fdata(filemask % (1)))
    return dic, data


def read_4D(filemask):
    """
    Read a 3D NMRPipe file.

    See :py:func:`read` for documentation.

    Notes
    -----
    This function should not be used to read NMRPipe data streams stored in a
    single file (one file 3D/4D data sets made using xyz2pipe),
    :py:func:`read_2D` should be used.

    """
    dic, data = read_lowmem_4D(filemask)
    data = data[:, :, :, :]  # read all the data
    return dic, data


def read_lowmem_4D(filemask):
    """
    Read a NMRPipe file using minimal memory.

    See :py:func:`read_lowmem` for documentation

    Notes
    -----
    This function should not be used to read NMRPipe data streams stored in a
    single file (one file 3D/4D data sets made using xyz2pipe),
    :py:func:`read_lowmem_2D` should be used.

    """
    from ..utils.fdata import pipe_4d,fdata2dic, get_fdata
    if '%' not in filemask:  # data streams should be read with read_stream
        return read_lowmem_stream(filemask)

    data = pipe_4d(filemask)    # create a new pipe_3d object
    if data.singleindex:
        dic = fdata2dic(get_fdata(filemask % (1)))
    else:
        dic = fdata2dic(get_fdata(filemask % (1, 1)))
    return (dic, data)

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