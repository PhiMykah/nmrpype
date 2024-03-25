NMR Input Utility
=======================
**Functions tasked with handling input properly**

*Adopted from nmrglue's source code for use in nmrPype*

Data Conversion
---------------

.. automodule:: nmrPype.utils.fdata
    :members: fdata2dic, dic2fdata, get_fdata, get_fdata_data

Data Handling
-------------

.. automodule:: nmrPype.utils.fdata
    :members: append_data, unappend_data, reshape_data, unshape_data, find_shape

Put To Disk
-----------
.. automodule:: nmrPype.utils.fdata
    :members: put_fdata, put_data, put_trace

Data Manipulation Classes
-------------------------
.. autoclass:: nmrPype.utils.fdata.pipe_2d
    :members:

.. autoclass:: nmrPype.utils.fdata.pipe_3d
    :members:

.. autoclass:: nmrPype.utils.fdata.pipe_4d
    :members:

.. autoclass:: nmrPype.utils.fdata.pipestream_3d
    :members:

.. autoclass:: nmrPype.utils.fdata.pipestream_4d
    :members: