from .function import DataFunction as Function
import numpy as np

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class DeleteImaginary(Function):
    """
    Data Function object for deleting imaginary values of NMR data.

    Parameters
    ----------
    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, mp_enable = False, mp_proc = 0, mp_threads = 0):
        self.mp = [mp_enable, mp_proc, mp_threads]
        params = {}
        super().__init__(params)

    ############
    # Function #
    ############
    
    def run(self, data : DataFrame) -> int:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.run` for documentation
        """
        # check if direct dimension is already real
        currDim = data.getCurrDim()
        quadFlag = data.getParam('NDQUADFLAG', currDim)
        if quadFlag:
            self.updateHeader(data)
            return 0
        # See function.py
        exitCode = super().run(data)
        if exitCode:
            return exitCode
        data.array = data.array.real

        """
        # depreciated code for halfing all the indirect dimensions

        # Nice code but not necessary
        # Exit normally if only one dimensional
        if data.array.ndim < 2:
            self.updateHeader(data)
            return 0
        
        # Collect indices to remove indirect imaginary in second dimension
        indices_list = [[0,size,1] for size in data.array.shape]

        # Delete from indirect dimensions only if not real
        for dim in range(2, data.array.ndim + 1):
            quadFlag = data.getParam('NDQUADFLAG', dim)
            if not quadFlag:
                indices_list[int(-1 * dim)][-1] = 2

        # generate slices
        slices = [slice(*indices) for indices in indices_list]

        data.array = data.array[tuple(slices)]
        """
        return 0
    
    ###################
    # Multiprocessing #
    ###################

    ######################
    # Default Processing #
    ######################
    
    def process(self, array: np.ndarray) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.process` for documentation
        """
        dataLength = array.shape[-1]

        # Operation strips imaginary component of array
        operation = lambda a : a.real

        # Check for parallelization
        if self.mp[0]:
            with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
                processed_chunk = list(executor.map(operation, array))
                array = np.array(processed_chunk)
        else:
            it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=dataLength)
            with it:
                for x in it:
                    x[...] = operation(x)

        return array
        
    ####################
    #  Proc Functions  #
    ####################
        
    def initialize(self, data : DataFrame):
        """
        Initialization follows the following steps:
            - Handle function specific arguments
            - Update any header values before any calculations occur
              that are independent of the data, such as flags and parameter storage

              
        Parameters
        ----------
        data : DataFrame
            Target data to manipulate 
        """
        currDim = data.getCurrDim()
        shape = data.array.shape 

        # Set curr dimension's quad flag to real
        data.setParam('NDQUADFLAG', float(1), currDim)

        qFlags = []
        # Get the flags for all dimensions
        for dim in range(len(shape)):
            qFlags.append(data.getParam('NDQUADFLAG', dim+1))
        
        # Check if all dimensions are real
        isReal = all(bool(flag) for flag in qFlags)

        data.setParam('FDQUADFLAG', float(1) if isReal else float(0))

        # Update Slicecount
        slices = np.prod(shape[:-1])

        data.setParam('FDSLICECOUNT', float(slices))


    def updateHeader(self, data : DataFrame):
        """
        Update the header following the main function's calculations.
        Typically this includes header fields that relate to data size.

        Parameters
        ----------
        data : DataFrame
            Target data frame containing header to update
        """
        shape = data.array.shape
        # Check if 1D or ND data
        if len(shape) == 1:
            # Update ndsize
            size = float(shape[-1])
            data.setParam('NDSIZE', size, data.getDimOrder(1))
            # Update slicecount
            data.setParam('FDSLICECOUNT', float(0))
            return
        
        for dim in range(len(shape)):
            size = float(shape[-1*(dim+1)])
            # when the direct dim is singular and the indirect
            # dim is complex FDSPECNUM is half of the correct value
            if dim == 1:
                # Check if first indirect (2) dimension is complex
                # Check if direct dimension (1) is real
                if data.getParam("NDQUADFLAG", 2) == 0 \
                and data.getParam("NDQUADFLAG", 1) == 1: 
                    size /= 2
            data.setParam('NDSIZE', size, data.getDimOrder(dim+1))
        
        slices = 1
        # Update slicecount
        for dim in range(1, len(shape)):
            slice = shape[-1*(dim+1)]
            if dim == 1:
                # Check if first indirect (2) dimension is complex
                # Check if direct dimension (1) is real
                if data.getParam("NDQUADFLAG", 2) == 0 \
                and data.getParam("NDQUADFLAG", 1) == 1:
                    slice /= 2
            slices *= slice

        data.setParam('FDSLICECOUNT', float(slices))