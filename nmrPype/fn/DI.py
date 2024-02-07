from .function import DataFunction as Function
import numpy as np

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class DeleteImaginary(Function):
    """
        class ZeroFill

        Data Function object for performing a zero-fill on the data
    """
    def __init__(self, mp_enable = False, mp_proc = 0, mp_threads = 0):
        self.mp = [mp_enable, mp_proc, mp_threads]
        params = {}
        super().__init__(params)

    ############
    # Function #
    ############
    
    def run(self, data) -> int:
        # See function.py
        exitCode = super().run(data)
        if exitCode:
            return 1
        
        # Collect indices to remove indirect imaginary
        indices_list = [[0,size,2] for size in data.array.shape]

        # Keep all of the direct dimension
        indices_list[int(-1 * data.getCurrDim())][-1] = 1
        
        # generate slices
        slices = [slice(*indices) for indices in indices_list]

        data.array = data.array[*slices]
        
        self.updateHeader(data)

        return 0
    
    ###################
    # Multiprocessing #
    ###################

    ######################
    # Default Processing #
    ######################
    
    def process(self, array: np.ndarray) -> np.ndarray:
        """
        fn process

        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed

        Parameters
        ----------
        array : np.ndarray
            array to process

        Returns
        -------
        np.ndarray
            modified array post-process
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
        
    def initialize(self, data):
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

    def updateHeader(self, data):
        """
        fn updateHeader

        Update the header following the main function's calculations.
            Typically this includes header fields that relate to data size.

        Parameters
        ----------
        None
        """
        shape = data.array.shape

        # Update ndsizes
        for dim in range(data.array.ndim):
            index = dim + 1
            data.setParam('NDSIZE', float(shape[-1*(index)]),index)

        # Update slicecount
        slices = np.prod(shape[:-1])

        data.setParam('FDSLICECOUNT', float(slices))