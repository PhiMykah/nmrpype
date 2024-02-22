from numpy import ndarray
from .function import DataFunction as Function
import numpy as np
from enum import Enum

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class PHASE(Enum):
    FD_MAGNITUDE = 0
    FD_TIPPI = 1
    FD_STATES = 2
    FD_IMAGE = 3
    FD_ARRAY = 4

class Transpose(Function):
    """
    class Transpose

    Template Data Function object for transposition operations
    """
    def __init__(self,
                tp_noord: bool = False, tp_exch : bool = False,
                tp_minMax: bool = True, tp_axis : int = 0, params : dict = {}):
        
        self.tp_noord = tp_noord
        self.tp_exch = tp_exch
        self.tp_minMax = tp_minMax
        self.tp_axis = tp_axis
        self.xDim = 1
        self.yDim = 2
        self.zDim = 3
        self.aDim = 4

        params.update({'tp_noord':tp_noord,
                  'tp_exch':tp_exch,'tp_minMax':tp_minMax,})
        super().__init__(params)


    ############
    # Function #
    ############
    
    ###################
    # Multiprocessing #
    ###################
        
    def parallelize(self, array) -> np.ndarray:
        """
        fn parallelize

        General Multiprocessing implementation for function, utilizing cores and threads
        
        Should be overloaded if array_shape changes in processing or process requires more args

        Parameters:
        array : np.ndarray
            Target data array to process with function

        Returns:
        new_array : np.ndarray
            Updated array after function operation
        """
        # Multiprocessing and mulithreading transpose is likely slower due to stitching
        return(self.process(array))
    

    ######################
    # Default Processing #
    ######################
        
    def process(self, array : np.ndarray) -> np.ndarray:
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
        
        # Expanding out the imaginary to to another set of data 
        # when performing the TP implementations is necessary,
        # this code is placeholder
        return array.swapaxes(-1,self.tp_axis-1)
    
    def matrixTP(self, array, dim1, dim2):
        transpose = np.swapaxes(array, -1*dim1,-1*dim2)
        return transpose
    
    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser):    
        """
        fn clArgs (FT command-line arguments)

        Adds Fourier Transform parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """

        # 2D Transpose subparser
        YTP = subparser.add_parser('YTP', aliases=['TP', 'XY2YX'], help='2D Plane Transpose.')
        group = YTP.add_mutually_exclusive_group()
        group.add_argument('-hyper', action='store_true',
                        dest='tp_hyper', help='Hypercomplex Transpose Mode.')
        group.add_argument('-noauto', action='store_true',
                dest='tp_noauto', help='Choose Mode via Command Line.')
        group.add_argument('-nohyper', action='store_true',
                        dest='tp_nohyper', help='Suppress Hypercomplex Mode.')
        group.add_argument('-auto', action='store_true',
                        dest='tp_auto', help='Chose Mode Automaticaly (Default).')
        YTP.add_argument('-nohdr', action='store_true',
                        dest='tp_nohdr', help='No Change to Header TRANSPOSE state.')
        YTP.add_argument('-exch', action='store_true',
                dest='tp_exch', help='Exchange Header Parameters for the Two Dimensions.')
        
        # Include tail arguments proceeding function call
        Transpose.headerArgsTP(YTP)
        Function.clArgsTail(YTP)

        # 3D Transpose subparser
        ZTP = subparser.add_parser('ZTP', aliases=['XYZ2ZYX'], help='3D Matrix Transpose.')
        ZTP.add_argument('-exch', action='store_true',
                dest='tp_exch', help='Exchange Header Parameters for the Two Dimensions.')
        
        # Include tail arguments proceeding function call
        Transpose.headerArgsTP(ZTP)
        Function.clArgsTail(ZTP)

        # 4D Transpose subparser
        ATP = subparser.add_parser('ATP', aliases=['XYZA2AYZX'], help='4D Matrix Transpose.')

        # Include tail arguments proceeding function call
        Transpose.headerArgsTP(ATP)
        Function.clArgsTail(ATP)


    @staticmethod
    def headerArgsTP(parser):
        """
        fn headerArgsTP 

        Parse commands related to header adjustment
        """
        parser.add_argument('-noord', action='store_true',
                        dest='tp_noord', help='No Change to Header Orders')
        parser.add_argument('-minMax', action='store_true',
                        dest='tp_minMax', help='Update FDMIN and FDMAX')
    

    ####################
    #  Proc Functions  #
    ####################

    def initialize(self, data):
        """
        fn initialize

        Initialization follows the following steps:
            -Handle function specific arguments
            -Update any header values before any calculations occur
                that are independent of the data, such as flags and parameter storage

        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        None
        """

        # Check if allowed to switch dimension orders
        if (self.tp_noord == False):
            # Swap dimension orders
            dimOrder1 = data.getParam('FDDIMORDER1')
            dimOrder2 = data.getParam(f'FDDIMORDER{str(self.tp_axis)}')

            data.setParam('FDDIMORDER1', dimOrder2)
            data.setParam(f'FDDIMORDER{str(self.tp_axis)}', dimOrder1)

            # Swap in dim order
            data.header['FDDIMORDER'][0] = dimOrder2
            data.header['FDDIMORDER'][self.tp_axis-1] = dimOrder1

        # Toggle Transpose flag
        isTransposed = data.getParam('FDTRANSPOSED')
        isTransposed = 0 if isTransposed else 1
        data.setParam('FDTRANSPOSED', isTransposed)


    def updateHeader(self, data):
        """
        fn updateHeader

        Update the header following the main function's calculations.
            Typically this includes header fields that relate to data size.

        Parameters
        ----------
        None
        """
        # Update ndsize here  
        shape = data.array.shape

        for dim in range(len(shape)):
            data.setParam('NDSIZE', float(shape[-1*(dim+1)]), data.getDimOrder(dim+1))
            
        # Update Slicecount
        slices = np.prod(shape[:-1])

        data.setParam('FDSLICECOUNT', float(slices))
        pass


class Transpose2D(Transpose):
    """
    class Transpose2D

    Data Function object for 2D transposition operations
    """
    def __init__(self,
                 tp_hyper : bool = True, tp_nohyper : bool = False, 
                 tp_auto: bool = True, tp_noauto : bool = False,
                 tp_nohdr : bool = False, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        self.tp_hyper = tp_hyper or (not tp_nohyper)
        self.tp_auto = tp_auto or (not tp_noauto)
        self.tp_nohdr = tp_nohdr
        self.mp = [mp_enable, mp_proc, mp_threads]
        tp_axis = 2 
        params = {'tp_hyper':tp_hyper,'tp_auto':tp_auto,
                  'tp_nohdr':tp_nohdr}
        super().__init__(tp_noord, tp_exch, tp_minMax, tp_axis, params)


    ############
    # Function #
    ############

    ###################
    # Multiprocessing #
    ###################
        
    ######################
    # Default Processing #
    ######################
    
    def process(self, array):
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

        # Ensure that the dimensions are at least 2
        if array.ndim < 2:
            raise Exception('Unable to resolve desired axis!')
        #if array.ndim < 2: Only necessary for 3D TP
        #    raise IndexError('Attempting to swap out of dimension bounds!')

        if self.tp_hyper:
            return self.hyperTP(array)
        else:
            return self.matrixTP(array, self.xDim, self.yDim)
    

    def hyperTP(self, array):
        """
        fn hyperTP

        Performs a hypercomplex transposition

        Parameters
        ----------
        array : ndarray
            N-dimensional array to swap first two dimensions
        Returns
        -------
        new_array : ndarray
            Transposed array
        """
        # Check if directly detected dimension is real
        if array.dtype == 'float32':
            realY = array[...,::2,:]
            imagY = array[...,1::2,:]
            return self.matrixTP(realY, self.xDim, self.yDim) \
                 + 1j * self.matrixTP(imagY, self.xDim, self.yDim)

        # Extrapolate real and imaginary parts of the last dimension
        realX = array.real
        imagX = array.imag

        # Interweave Y values prior to transpose
        a = realX[...,::2,:] + 1j*realX[...,1::2,:]
        b = imagX[...,::2,:] + 1j*imagX[...,1::2,:]

        transposeShape = a.shape[:-2] + (2*a.shape[-1], a.shape[-2])
        
        # Prepare new array to interweave real and imaginary indirect dimensions
        new_array = np.zeros(transposeShape, dtype=a.dtype)

        # Interweave real and imaginary values of former X dimension
        new_array[...,::2,:] = self.matrixTP(a, self.xDim, self.yDim)
        new_array[...,1::2,:] = self.matrixTP(b, self.xDim, self.yDim)

        return new_array


    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser): 
        pass 


    ####################
    #  Proc Functions  #
    ####################

    def initialize(self, data):
        """
        fn initialize

        Initialization follows the following steps:
            -Handle function specific arguments
            -Update any header values before any calculations occur
                that are independent of the data, such as flags and parameter storage

        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        """
        xDim = 1
        yDim = 2

        # If both dimensions are real, ensure nohyper flag, If either dimension is complex do hyper 
        if not data.getParam('NDQUADFLAG', xDim) or not data.getParam('NDQUADFLAG', yDim):
            self.tp_hyper = True
        else:
            self.tp_hyper = False
        
        # If the 2Dphase parameter matches magnitude, switch the dimension complexity
        if data.getParam('FD2DPHASE') == PHASE.FD_MAGNITUDE.value:
        
            xID = data.getParam('NDQUADFLAG', xDim)
            yID = data.getParam('NDQUADFLAG', yDim)

            # Swap the number type of x and y dims
            data.setParam('NDQUADFLAG', float(yID), xDim)
            data.setParam('NDQUADFLAG', float(xID), yDim)

        super().initialize(data)
        

    def updateHeader(self, data):
        """
        fn updateHeader

        Update the header following the main function's calculations.
            Typically this includes header fields that relate to data size.

        Parameters
        ----------
        None
        """
        super().updateHeader(data)


class Transpose3D(Transpose):
    """
    class Transpose3D

    Data Function object for 3D transposition operations
    """
    def __init__(self, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        self.mp = [mp_enable, mp_proc, mp_threads]
        tp_axis = 3
        super().__init__(tp_noord, tp_exch, tp_minMax, tp_axis)

    ############
    # Function #
    ############

    ###################
    # Multiprocessing #
    ###################
        
    ######################
    # Default Processing #
    ######################

    def process(self, array):
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

        # Ensure that there are at least 3 dimensions
        if array.ndim < 2:
            raise IndexError('Attempting to swap out of dimension bounds!')

        return self.TP3D(array)
        
        
    def TP3D(self, array : np.ndarray) -> np.ndarray:
        """
        fn TP3D

        Performs a hypercomplex transposition on 3D Data

        Parameters
        ----------
        array : ndarray
            N-dimensional array to swap first and third dimensions
        Returns
        -------
        new_array : ndarray
            Transposed array
        """

        # Extrapolate X real and X imag
        realX = array.real
        imagX = array.imag

        isComplex = np.all(imagX)


        # Prepare to interweave z axis
        a = realX[...,::2,:,:] + 1j*realX[...,1::2,:,:]
        if isComplex:
            b = imagX[...,::2,:,:] + 1j*imagX[...,1::2,:,:]

        transposeShape = a.shape[:-3] + (2*a.shape[-1], a.shape[-2],a.shape[-3]) if isComplex else \
                         a.shape[:-3] + (a.shape[-1], a.shape[-2],a.shape[-3])

        # Prepare new array to interweave real and imaginary indirect dimensions
        new_array = np.zeros(transposeShape, dtype=a.dtype)

        if isComplex:
            # Interweave real and imaginary values of former X dimension
            new_array[...,::2,:,:] = self.matrixTP(a,self.xDim, self.zDim)
            new_array[...,1::2,:,:] = self.matrixTP(b,self.xDim, self.zDim)
        else:
            new_array = self.matrixTP(a,self.xDim,self.zDim)

        return new_array
    

    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser): 
        pass

    ####################
    #  Proc Functions  #
    ####################

    def initialize(self, data):
        """
        fn initialize

        Initialization follows the following steps:
            -Handle function specific arguments
            -Update any header values before any calculations occur
                that are independent of the data, such as flags and parameter storage

        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        """
        # Designate proper dimensions based on dim order
        xDim = 1
        yDim = 2
        zDim = 3

        xQuadState = data.getParam('NDQUADFLAG', xDim)
        yQuadState = data.getParam('NDQUADFLAG', yDim)
        zQaudState = data.getParam('NDQUADFLAG', zDim)

        # If the 2Dphase parameter matches magnitude, switch the dimension complexity
        if data.getParam('FD2DPHASE') == PHASE.FD_MAGNITUDE.value:
        
            xID = data.getParam('NDQUADFLAG', xDim)
            zID = data.getParam('NDQUADFLAG', zDim)

            # Swap the number type of x and y dims
            data.setParam('NDQUADFLAG', float(zID), xDim)
            data.setParam('NDQUADFLAG', float(xID), zDim)

        super().initialize(data)


    def updateHeader(self, data):
        """
        fn updateHeader

        Update the header following the main function's calculations.
            Typically this includes header fields that relate to data size.

        Parameters
        ----------
        None
        """
        # Update ndsize here  
        pass


class Transpose4D(Transpose):
    """
    class Transpose4D

    Data Function object for 4D transposition operations
    """
    def __init__(self, data, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        self.mp = [mp_enable, mp_proc, mp_threads]
        tp_axis = 4
        super().__init__(data, tp_noord, tp_exch, tp_minMax, tp_axis)


    ############
    # Function #
    ############

    ###################
    # Multiprocessing #
    ###################
        
    ######################
    # Default Processing #
    ######################

    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser): 
        pass


    ####################
    #  Proc Functions  #
    ####################

    def initialize(self, data):
        """
        fn initialize

        Initialization follows the following steps:
            -Handle function specific arguments
            -Update any header values before any calculations occur
                that are independent of the data, such as flags and parameter storage

        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        """
        super().initialize(data)


    def updateHeader(self, data):
        """
        fn updateHeader

        Update the header following the main function's calculations.
            Typically this includes header fields that relate to data size.

        Parameters
        ----------
        None
        """
        # Update ndsize here  
        pass