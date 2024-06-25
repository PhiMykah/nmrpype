from nmrPype.utils import DataFrame
from .function import DataFunction as Function
import numpy as np
from scipy.signal import hilbert
from sys import stderr
# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class HilbertTransform(Function):
    """
    Data Function object for performing a Hilber Transform on the data.

    Parameters
    ----------
    ht_ps90_180 : bool, optional
        Enable mirror image Hilbert transform, by default False
    ht_td : bool, optional
        Set time domain size to SIZE/2, by default False
    mp_enable : bool, optional
        Enable multiprocessing, by default False
    mp_proc : int, optional
        Number of processors to utilize for multiprocessing, by default 0
    mp_threads : int, optional
        Number of threads to utilize per process, by default 0
    """
    def __init__(self, ht_ps90_180 : bool = False, ht_td : bool = False, 
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        
        self.ht_ps90_180 = ht_ps90_180
        # self.ht_zf = ht_zf
        self.ht_td = ht_td
        # self.ht_auto = ht_auto
        # self.ht_ps0_0 = ht_ps0_0
        # self.ht_nozf = ht_nozf

        self.mp = [mp_enable, mp_proc, mp_threads]
        self.name = "HT"
        
        params = {'ht_ps90_180':ht_ps90_180, 'ht_td':ht_td}
        super().__init__(params)

    ############
    # Function #
    ############

    def run(self, data : DataFrame) -> int:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.run` for documentation
        """

        self.initialize(data)

        if not self.mp[0] or data.array.ndim == 1:
            data.array = self.process(data.array, (data.verb, data.inc, data.getParam('NDLABEL')))
        else:
            data.array = self.parallelize(data.array, (data.verb, data.inc, data.getParam('NDLABEL')))

        # Update header once processing is complete
        self.updateHeader(data)

        return 0
    
    ###################
    # Multiprocessing #
    ###################

    ######################
    # Default Processing #
    ######################

    def process(self, array : np.ndarray, verb : tuple[int,int, str] = (0,16,'H')) -> np.ndarray:
        """
        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        verb : tuple[int,int,str], optional
        Tuple containing elements for verbose print, by default (0, 16,'H')
            - Verbosity level
            - Verbosity Increment
            - Direct Dimension Label

        Returns
        -------
        ndarray
            Updated array after function operation
        """
        # Ensure support for an odd number of points

        it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=array.shape[-1], order='C')
        with it:
            for x in it:
                if verb[0]:
                    Function.verbPrint('HT', it.iterindex, it.itersize, array.shape[-1], verb[1:])
                    x[...] = self.hilb(x)
            if verb[0]:
                print("", file=stderr)

        return array
    
    def hilb(self, array : np.ndarray) -> np.ndarray:
        x = array.real
        htSize = len(x)

        if (self.ht_ps90_180):
            htSize = 2*htSize
        
        return hilbert(x, htSize)


    ##################
    # Static Methods #
    ##################

    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Hilbert Transform command-line arguments

        Adds Hilbert Transform parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # HT subparser
        HT = subparser.add_parser('HT', parents=[parent_parser], help='Perform a Hilbert Transform (HT) on the data')
        HT.add_argument('-ps90-180', action='store_true', 
                        dest='ht_ps90_180', help='Mirror Image Hilbert Transform.')
        # HT.add_argument('-zf', action='store_true', 
        #                 dest='ht_zf', help='Temporary Zero Fill for Speed')
        HT.add_argument('-td', action='store_true', 
                        dest='ht_td', help='Set Time-Domain Size to SIZE/2')
        # HT.add_argument('-auto', action='store_true', 
        #                 dest='ht_auto', help='Auto Mode; Select HT and ZF mode.')
        # HT.add_argument('-ps0-0', action='store_true',
        #                 dest='ht_ps0_0', help='Force Ordinary Hilbert Transform')
        # HT.add_argument('-nozf', action='store_true',
        #                 dest='ht_nozf', help='No Temporary Zero Fill')
        

    ####################
    #  Proc Functions  #
    ####################

    def initialize(self, data: DataFrame):
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
        return super().initialize(data)
    
    def updateHeader(self, data : DataFrame):
        """
        Update the header following the main function's calculations.
        Typically this includes header fields that relate to data size.

        Parameters
        ----------
        data : DataFrame
            Target data frame containing header to update
        """
        # Set data to complex if needed
        currDim = data.getCurrDim()
        if data.getParam("NDQUADFLAG", currDim) == 1:
            data.setParam("NDQUADFLAG", currDim, 0.0)

        shape = data.array.shape
        qFlags = []
        # Get the flags for all dimensions
        for dim in range(len(shape)):
            qFlags.append(data.getParam('NDQUADFLAG', dim+1))
        
        # Check if all dimensions are real
        isReal = all(bool(flag) for flag in qFlags)

        data.setParam('FDQUADFLAG', float(1) if isReal else float(0))

        if self.ht_td:
            size = data.getParam('NDAPOD', currDim)
            data.setParam('NDAPOD', size/2, currDim)


        