################
#This code is a modification of code soruced from 'nmrglue' by Johnathan J Halmus and other contributors.
#J.J. Helmus, C.P. Jaroniec, Nmrglue: An open source Python package for the analysis of multidimensional NMR data, 
#J. Biomol. NMR 2013, 55, 355-367, http://dx.doi.org/10.1007/s10858-013-9718-x.
################

import numpy as np
from . import fileiobase

#####################
# writing functions #
#####################


def write(filename, dic, data, overwrite=False):
    """
    Write a NMRPipe file to disk.

    Parameters
    ----------
    filename : str
        Filename of NMRPipe to write to.  See Notes.
    dic : dict
        Dictionary of NMRPipe parameters.
    data : array_like
        Array of NMR data.
    overwrite : bool, optional.
        Set True to overwrite files, False will raise a Warning if file
        exists.

    Notes
    -----
    For 3D data if filename has no '%' formatter then the data is written as a
    3D NMRPipe data stream.  When the '%' formatter is provided the data is
    written out as a standard NMRPipe 3D multi-file 3D.

    For 4D data, filename can have one, two or no '%' formatters resulting in
    a single index file (test%03d.ft), two index file(test%02d%03d.ft), or
    one file data stream (test.ft4).

    dic["FDPIPEFLAG"] is not changed or checked when writing, please check
    that this value is 0.0 for standard non-data stream files, and 1.0 for data
    stream files or an file may be written with an incorrect header.

    Set overwrite to True to overwrite files that exist.

    See Also
    --------
    write_lowmem : Write NMRPipe files using minimal amounts of memory.
    read : Read NMRPipe files.

    """
    # load all data if the data is not a numpy ndarray
    if not isinstance(data, np.ndarray):
        data = data[:]

    if filename.count("%") == 0:
        return write_single(filename, dic, data, overwrite)
    elif data.ndim == 3:
        return write_3D(filename, dic, data, overwrite)
    elif data.ndim == 4:
        return write_4D(filename, dic, data, overwrite)

    raise ValueError('unknown filename/dimension')


def write_single(filename, dic, data, overwrite=False):
    from utils.fdata import append_data, unshape_data, dic2fdata, put_data
    """
    Write data to a single NMRPipe file from memory.

    Write 1D and 2D files completely as well as NMRPipe data streams.
    2D planes of 3D and 4D files should be written with this function.

    See :py:func:`write` for documentation.

    """
    # append imaginary and flatten
    if data.dtype == "complex64":
        data = append_data(data)
    data = unshape_data(data)

    # create the fdata array
    fdata = dic2fdata(dic)

    # write the file
    put_data(filename, fdata, data, overwrite)


def write_3D(filemask, dic, data, overwrite=False):
    """
    Write a standard multi-file 3D NMRPipe file

    See :py:func:`write` for documentation.

    """
    lenZ, lenY, lenX = data.shape
    for zi in range(lenZ):
        fn = filemask % (zi + 1)
        plane = data[zi]
        write_single(fn, dic, plane, overwrite)


def write_4D(filemask, dic, data, overwrite=False):
    """
    Write a one or two index 4D NMRPipe file.

    See :py:func:`write` for documentation.

    """
    lenA, lenZ, lenY, lenX = data.shape
    for ai in range(lenA):
        for zi in range(lenZ):
            if filemask.count("%") == 2:
                fn = filemask % (ai + 1, zi + 1)
            else:
                fn = filemask % (ai * lenZ + zi + 1)

            plane = data[ai, zi]

            # update dictionary if needed
            if dic["FDSCALEFLAG"] == 1:
                dic["FDMAX"] = plane.max()
                dic["FDDISPMAX"] = dic["FDMAX"]
                dic["FDMIN"] = plane.min()
                dic["FDDISPMIN"] = dic["FDMIN"]
            write_single(fn, dic, plane, overwrite)


def write_lowmem(filename, dic, data, overwrite=False):
    """
    Write a NMRPipe file to disk using minimal memory (trace by trace).

    Parameters
    ----------
    filename : str
        Filename of NMRPipe to write to.  See :py:func:`write` for details.
    dic : dict
        Dictionary of NMRPipe parameters.
    data : array_like
        Array of NMR data.
    overwrite : bool, optional.
        Set True to overwrite files, False will raise a Warning if file
        exists.

    See Also
    --------
    write : Write a NMRPipe file to disk.
    read_lowmem : Read a NMRPipe file using minimal memory.

    """
    if data.ndim == 1:
        return write_single(filename, dic, data, overwrite)
    if data.ndim == 2:
        return write_lowmem_2D(filename, dic, data, overwrite)
    if data.ndim == 3:
        if "%" in filename:
            return write_lowmem_3D(filename, dic, data, overwrite)
        else:
            return write_lowmem_3Ds(filename, dic, data, overwrite)
    if data.ndim == 4:
        if "%" in filename:
            return write_lowmem_4D(filename, dic, data, overwrite)
        else:
            return write_lowmem_4Ds(filename, dic, data, overwrite)

    raise ValueError('unknown dimensionality: %s' % data.ndim)


def write_lowmem_2D(filename, dic, data, overwrite=False):
    from utils.fdata import dic2fdata, put_fdata, put_trace
    """
    Write a 2D NMRPipe file using minimal memory (trace by trace)

    See :py:func:`write_lowmem` for documentation.

    """
    fh = fileiobase.open_towrite(filename, overwrite=overwrite)

    # create the fdata array and put to disk
    fdata = dic2fdata(dic)
    put_fdata(fh, fdata)

    # put data trace by trace
    lenY, lenX = data.shape
    for y in range(lenY):
        put_trace(fh, data[y])
    fh.close()


def write_lowmem_3D(filename, dic, data, overwrite=False):
    from utils.fdata import dic2fdata, put_fdata, put_trace
    """
    Write a standard multi-file 3D NMRPipe file using minimal memory.

    See :py:func:`write_lowmem` for documentation.

    Notes
    -----
    MIN/MAX parameters are not updated in the NMRPipe headers.

    """
    # create the fdata array
    fdata = dic2fdata(dic)

    # put data trace by trace
    lenZ, lenY, lenX = data.shape
    for z in range(lenZ):
        # open the file to store the 2D plane
        fh = fileiobase.open_towrite(filename % (z + 1), overwrite=overwrite)
        put_fdata(fh, fdata)
        for y in range(lenY):
            put_trace(fh, data[z, y])
        fh.close()


def write_lowmem_3Ds(filename, dic, data, overwrite=False):
    from utils.fdata import dic2fdata, put_fdata, put_trace
    """
    Write 3D NMRPipe data stream file using minimal memory (trace by trace)

    See :py:func:`write_lowmem` for documentation.

    """
    fh = fileiobase.open_towrite(filename, overwrite=overwrite)

    # create the fdata array and put to disk
    fdata = dic2fdata(dic)
    put_fdata(fh, fdata)

    # put data trace by trace
    lenZ, lenY, lenX = data.shape
    for z in range(lenZ):
        for y in range(lenY):
            put_trace(fh, data[z, y])
    fh.close()


def write_lowmem_4D(filename, dic, data, overwrite=False):
    from utils.fdata import dic2fdata, put_fdata, put_trace
    """
    Write a multi-file (single or double index) 4D NMRPipe file using
    minimal memory.

    See :py:func:`write_lowmem` for documentation.

    Notes
    -----
    MIN/MAX parameters are not updated in the NMRPipe headers.

    """
    # create the fdata array
    fdata = dic2fdata(dic)

    # put data trace by trace
    lenA, lenZ, lenY, lenX = data.shape
    for a in range(lenA):
        for z in range(lenZ):
            # open the file to store the 2D plane
            if filename.count("%") == 1:
                fname = filename % (a * lenZ + z + 1)
            else:
                fname = filename % (a + 1, z + 1)
            fh = fileiobase.open_towrite(fname, overwrite=overwrite)
            put_fdata(fh, fdata)
            for y in range(lenY):
                put_trace(fh, data[a, z, y])
            fh.close()


def write_lowmem_4Ds(filename, dic, data, overwrite=False):
    from utils.fdata import dic2fdata, put_fdata, put_trace
    """
    Write 4D NMRPipe data stream file using minimal memory (trace by trace)

    See :py:func:`write_lowmem` for documentation.

    """
    fh = fileiobase.open_towrite(filename, overwrite=overwrite)

    # create the fdata array and put to disk
    fdata = dic2fdata(dic)
    put_fdata(fh, fdata)

    # put data trace by trace
    lenA, lenZ, lenY, lenX = data.shape
    for a in range(lenA):
        for z in range(lenZ):
            for y in range(lenY):
                put_trace(fh, data[a, z, y])
    fh.close()


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