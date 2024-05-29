from .function import DataFunction as Function
import numpy as np
import operator

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class PhaseCorrection(Function):
    """
    Data Function object for performing a Phase Correction on the data.

    Parameters
    ----------
    ps_p0 : float
        Zero-order phase value in degrees

    ps_p1 : float
        First-order phase value in degrees

    ps_inv : bool
        Perform an inverse phase correction on the data

    ps_hdr : bool
        Use constant values from the header

    ps_noup : bool
        Don't update the header with the used constants

    ps_df : bool
        Adjust the p1 value for digital oversampling

    ps_ht : bool
        Reconstruct Imaginaries via Hilbert Transform

    ps_zf : bool
        Use Temporary Zero Fill for the Hilbert Transform.

    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, ps_p0 : float = 0, ps_p1 : float = 0,
                 ps_inv : bool = False, ps_hdr : bool = False, 
                 ps_noup : bool = False, ps_df : bool = False,
                 ps_ht : bool = False, ps_zf : bool = False,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        self.ps_p0 = ps_p0
        self.ps_p1 = ps_p1
        self.ps_inv = ps_inv
        self.ps_hdr = ps_hdr
        self.ps_noup = ps_noup
        self.ps_df = ps_df
        self.ps_ht = ps_ht
        self.ps_zf = ps_zf
        self.mp = [mp_enable, mp_proc, mp_threads]

        # initialize array for later
        self.phase = None
        
        params = {'ps_p0': ps_p0, 'ps_p1': ps_p1, 'ps_inv': ps_inv,
                  'ps_hdr': ps_hdr, 'ps_noup': ps_noup, 'ps_df': ps_df,
                  'ps_ht': ps_ht, 'ps_zf': ps_zf}
        super().__init__(params)

    ############
    # Function #
    ############

    ###################
    # Multiprocessing #
    ###################
    
    def parallelize(self, array: np.ndarray) -> np.ndarray:
        """
        Multiprocessing implementation for function to properly optimize for hardware

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        ndQuad : int
            NDQUADFLAG header value

        Returns
        -------
        new_array : ndarray
            Updated array after function operation
        """
        # Save array shape for reshaping later
        array_shape = array.shape

        # Split array into manageable chunks
        chunk_size = int(array_shape[0] / self.mp[1])
        
        # Assure chunk_size is nonzero
        chunk_size = array_shape[0] if chunk_size == 0 else chunk_size
        
        chunks = [array[i:i+chunk_size] for i in range(0, array_shape[0], chunk_size)]
        
        # Process each chunk in processing pool
        with Pool(processes=self.mp[1]) as pool:
            output = pool.map(self.phaseCorrect, chunks, chunksize=chunk_size)

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(array_shape)
        return new_array

    def phaseCorrect(self, array: np.ndarray) -> np.ndarray:
        """
        Phase correction helper function for multiprocessing

        Parameters
        ----------
        array : ndarray
            Target data array to phase correct

        Returns
        -------
        new_array : ndarray
            Updated array after function operation
        """
        # Set arguments for function
        args = [(a, self.phase) for a in array]
        with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
            processed_chunk = list(executor.map(lambda p: operator.mul(*p), args))
        array = np.array(processed_chunk)
        return array
    

    ######################
    # Default Processing #
    ######################

    def process(self, array : np.ndarray) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.process` for documentation
        """
        # Check for parallelization

        dataLength = array.shape[-1]
        it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=dataLength, order='C')
        with it:
            for x in it:
                x[...] = self.phase * x

        return array
    
    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Adds Phase Correction parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        PS = subparser.add_parser('PS', parents=[parent_parser], help='Perform a Phase Correction (PS) on the data')
        PS.add_argument('-p0', type=float, metavar='p0Deg', default=0.0,
                        dest='ps_p0', help='Zero Order Phase, Degrees')
        PS.add_argument('-p1', type=float, metavar='p1Deg', default=0.0,
                        dest='ps_p1', help='First Order Phase, Degrees')
        PS.add_argument('-inv', action='store_true',
                        dest='ps_inv', help='Inverse Phase Correction')
        PS.add_argument('-hdr', action='store_true',
                        dest='ps_hdr', help='Use Phase Values in Header')
        PS.add_argument('-noup', action='store_true',
                        dest='ps_noup', help='Don\'t Update Values Header')
        PS.add_argument('-df', action='store_true',
                        dest='ps_df', help='Adjust P1 for Digital Oversampling')
        
        # Include universal commands proceeding function call
        # Function.clArgsTail(PS)

    ####################
    #  Proc Functions  #
    ####################
        
    def initialize(self, data : DataFrame):
        """
        fn initialize

        Initialization follows the following steps:
            - Handle function specific arguments
            - Update any header values before any calculations occur
              that are independent of the data, such as flags and parameter storage

              
        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        """
        # Obtain size for phase correction from data
        size = data.array.shape[-1*data.getDimOrder(1)]

        # Convert from degrees to radians
        # C code uses 3.14159265
        p0 = np.radians(self.ps_p0)
        p1 = np.radians(self.ps_p1)

        realList = []
        imagList = []
        for x in range(size):
            realVal = np.cos(p0 + (p1*x)/size) # Ensure radians output is sufficient
            imagVal = np.sin(p0 + (p1*x)/size)
            realList.append(float(realVal))
            imagList.append(float(imagVal))

        imag = np.array(imagList)
        self.phase = np.array(realVal + 1j * imag, dtype='complex64')
        import sys
        # Add values to header if noup is off
        if (not self.ps_noup):
            currDim = data.getCurrDim()
            data.setParam('NDP0', float(self.ps_p0), currDim)
            data.setParam('NDP1', float(self.ps_p1), currDim)
        

    def updateHeader(self, data : DataFrame):
        """
        Update the header following the main function's calculations.
        Typically this includes header fields that relate to data size.

        Parameters
        ----------
        data : DataFrame
            Target data frame containing header to update
        """
        # Update ndsize here  
        pass
