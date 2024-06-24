from .function import DataFunction as Function
import numpy as np
from sys import stderr

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class SineBell(Function):
    """
    Data Function object for performing a Sinusoidal Filter on the data.

    Parameters
    ----------
    sp_off : float
        PI value starting offset

    sp_end : float
        PI value ending offset

    sp_pow : float
        Sine function exponent

    sp_size : int
        Span of data to apply sinusoidal filter to
        
    sp_start : int
        Starting point of sinusoidal filter window

    sp_c : float
        Scaling value for the first point of the sinusoidal filter window
        (e.g. scale first point by 0.5 or 2.0)

    sp_one : bool
        Set all points outside of sinusoidal filter window to 1 instead of 0

    sp_hdr : bool
        Use constant values from the header

    sp_inv : bool
        Invert the sinusoidal filter window

    sp_df : bool
        Adjust PI value starting offset and gaussian offset for Digital Oversampling.

    sp_elb : float
        Add an exponential filter by value in Hz

    sp_glb : float 
        Add a gaussian filter by value in Hz

    sp_goff : float
        Set gausian offset, within 0 to 1.

    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, sp_off : float = 0.0, sp_end : float = 1.0,
                 sp_pow : float = 1.0, sp_size : int = 0, sp_start : int = 1,
                 sp_c : float = 1, sp_one : bool = False, sp_hdr : bool = False,
                 sp_inv : bool = False, sp_df : bool = False, sp_elb : float = 0.0,
                 sp_glb : float = 0.0, sp_goff : float = 0.0,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        
        self.sp_off = sp_off
        self.sp_end = sp_end
        self.sp_pow = sp_pow
        self.sp_size = sp_size
        self.sp_start = sp_start
        self.sp_c = sp_c
        self.sp_one = sp_one
        self.sp_hdr = sp_hdr
        self.sp_inv = sp_inv
        self.sp_df = sp_df
        self.sp_elb = sp_elb
        self.sp_glb = sp_glb
        self.sp_goff = sp_goff
        self.mp = [mp_enable, mp_proc, mp_threads]
        self.headerParams = {}
        self.name = "SP"

        params = {
        'sp_off': sp_off, 'sp_end': sp_end, 'sp_pow': sp_pow,
        'sp_size': sp_size, 'sp_start': sp_start, 'sp_c': sp_c,
        'sp_one': sp_one, 'sp_hdr': sp_hdr, 'sp_inv': sp_inv,
        'sp_df': sp_df, 'sp_elb': sp_elb, 'sp_glb': sp_glb,
        'sp_goff': sp_goff,}
        super().__init__(params)


    ############
    # Function #
    ############
        
    def run(self, data : DataFrame) -> int:
        """
        Sine Bell's run utilizes the generic function run but saves computation time by
        skipping the running step for trivial constants.

        For example, a power of 0 for the sinusoidal filter will return the data unchanged.

        See Also
        --------
        nmrPype.fn.function.DataFunction.run : Default run function
        """
        # Return unmodified array to save time if computation would return self
        if (self.sp_pow == 0.0):
            return 0
        if ((self.sp_off == 0.5) and (self.sp_end == 0.5)):
            return 0
        # See function.py
        return super().run(data)
        
    ###################
    # Multiprocessing #
    ###################

    def parallelize(self, array : np.ndarray, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.parallelize` for documentation.
        """
        # Set length of each vector
        dataLength = array.shape[-1]

        # Allocate variables from parameters for code simplification
        if self.sp_hdr and self.headerParams:
            a1 = self.headerParams['Q1']
            a2 = self.headerParams['Q2']
            a3 = self.headerParams['Q3']
            firstPointScale = 1.0 + self.headerParams['C1']
        else:
            a1 = self.sp_off
            a2 = self.sp_end
            a3 = self.sp_pow
            firstPointScale = self.sp_c

        df = self.headerParams['DFVAL'] if self.sp_df else 0.0

        # Set arguments for function
        args = []
        for i in range(len(array)):
            if i == 0:
                args.append((array[i], a1, a2, a3, firstPointScale, df, verb))
            else:
                args.append((array[i], a1, a2, a3, firstPointScale, df))
        
        with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
            processed_chunk = list(executor.map(lambda p: self.applyFunc(*p), args))
            array = np.array(processed_chunk)

        return array
    
    ######################
    # Default Processing #
    ######################
        
    def process(self, array: np.ndarray, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.process` for documentation
        """
        dataLength = array.shape[-1]
        
        # Allocate variables from parameters for code simplification
        if self.sp_hdr and self.headerParams:
            a1 = self.headerParams['Q1']
            a2 = self.headerParams['Q2']
            a3 = self.headerParams['Q3']
            firstPointScale = 1.0 + self.headerParams['C1']
        else:
            a1 = self.sp_off
            a2 = self.sp_end
            a3 = self.sp_pow
            firstPointScale = self.sp_c

        df = self.headerParams['DFVAL'] if self.sp_df else 0.0

        it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=dataLength, order='C')
        with it:
            for x in it:
                if verb[0]:
                    Function.verbPrint('SP', it.iterindex, it.itersize, array.shape[-1], verb[1:])
                x[...] = self.applyFunc(x, a1, a2, a3, firstPointScale, df)
            if verb[0]:
                print("", file=stderr)

        return array


    def applyFunc(self, array : np.ndarray, a1 : float, a2 : float,
                  a3 : float, fps : int, df : float, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        Apply sine bell to array

        Parameters
        ----------
        array : np.ndarray
            Target array to apply function to

        a1 : float
            offset value
        a2 : float 
            end value
        a3 : float
            exponential power value
        fps : int
            first point scale to apply
        df : float
            digital filter value
        verb : tuple[int,int,str], optional
        Tuple containing elements for verbose print, by default (0, 16,'H')
            - Verbosity level
            - Verbosity Increment
            - Direct Dimension Label
            
        Returns
        -------
        new_array : np.ndarray
            Array with sinusoidal filter
        """
        if array.ndim == 1:
            tSize = len(array)
        else:
            tSize = array.shape[-1]

        # Set size to the size of array if one is not provided
        aSize = self.sp_size if self.sp_size else tSize

         #mSize = aStart + aSize - 1 > tSize ? tSize - aStart + 1 : aSize;
        mSize = tSize - self.sp_start + 1 if self.sp_start + aSize - 1 > tSize else aSize


        # Modify offset based on digital filter
        if (df > 0 and mSize > df):
            a1 -= (a2 - a1)/(mSize - df) 
        
        q = aSize - 1
        
        q = 1 if q <= 0.0 else q

        new_shape = array.shape[:-1] + (tSize,)
        new_array = np.ones(new_shape, dtype=array.dtype) if self.sp_one else np.zeros(new_shape, dtype=array.dtype)
        
        startIndex = self.sp_start - 1

        t = (np.arange(mSize) - df)/q

        f_t = np.sin(np.pi*a1 + np.pi*(a2 -a1)*np.absolute(t))
        a = np.power(f_t, a3)
        in_closed_unit_interval = (0.0 <= a1 <= 1.0) and (0.0 <= a2 <= 1.0)
        a = np.absolute(a) if (in_closed_unit_interval) else a

        # Place window function region into dummy array
        new_array[...,startIndex:startIndex + mSize] = array[startIndex:startIndex + mSize] * a
        
        if self.sp_inv: 
            new_array[0] /= fps
        else:
            new_array[0] *= fps

        return(new_array)



    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Adds Sine Bell parser to the subparser, with its corresponding args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        SP = subparser.add_parser('SP', parents=[parent_parser], aliases=['SINE'], help='Adjustable Sine Bell')
        SP.add_argument('-off', type=float, metavar='offset [0.0]', default=0.0,
                        dest='sp_off', help='Sine Start*PI.    (Q1)')
        SP.add_argument('-end', type=float, metavar='end [1.0]', default=1.0,
                        dest='sp_end', help='Sine End*PI.    (Q2)')
        SP.add_argument('-pow', type=float, metavar='exp [1.0]', default=1.0,
                        dest='sp_pow', help='Sine Exponent.  (Q3)')
        SP.add_argument('-size', type=float, metavar='aSize [APOD]', default=0.0,
                        dest='sp_size', help='Apodize Length')
        SP.add_argument('-start', type=int, metavar='aStart [1]', default=1,
                        dest='sp_start', help='Apodize Start')
        SP.add_argument('-c', type=float, metavar='fScale [1]', default=1,
                        dest='sp_c', help='Scaling Value for the First Point')
        SP.add_argument('-one', action='store_true',
                        dest='sp_one', help='Outside = 1')
        SP.add_argument('-hdr', action='store_true',
                        dest='sp_hdr', help='Use Q/LB/GB/GOFF from Header')
        SP.add_argument('-inv', action='store_true',
                        dest='sp_inv', help='Invert Window')
        SP.add_argument('-df', action='store_true',
                        dest='sp_df', help='Adjust -off and -goff for Digital Oversampling')
        group = SP.add_argument_group('Composite Window Options')
        group.add_argument('-elb', type=float, metavar='elbHz [0.0]', default=0.0,
                        dest='sp_elb', help='Addition Exponential, Hz. (LB)')
        group.add_argument('-glb', type=float, metavar='glbHz [0.0]', default=0.0,
                        dest='sp_glb', help='Addition Gaussian, Hz.    (GB)')
        group.add_argument('-goff', type=float, metavar='gOff [0.0]', default=0.0,
                        dest='sp_goff', help='Gauss Offset, 0 to 1.   (GOFF)')
        
        # Include tail arguments proceeding function call
        # Function.clArgsTail(SP)


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
            target data to manipulate 
        """
        # Initialize Header Params
        currDim = data.getCurrDim()
        self.headerParams = {
            'Q1':data.getParam('NDAPODQ1', currDim), 
            'Q2':data.getParam('NDAPODQ2', currDim), 
            'Q3':data.getParam('NDAPODQ3', currDim),
            'DF':data.getParam('FDDMXVAL', currDim),
            'C1':data.getParam('NDC1', currDim)
        }

        # Variable initialization for clarity
        q1 = self.sp_off
        q2 = self.sp_end
        q3 = self.sp_pow

        lb = self.sp_elb
        gb = self.sp_glb
        goff = self.sp_goff

        data.setParam('NDAPODQ1', float(q1), currDim)
        data.setParam('NDAPODQ2', float(q2), currDim)
        data.setParam('NDAPODQ3', float(q3), currDim)

        data.setParam('NDLB', float(lb), currDim)
        data.setParam('NDGB', float(gb), currDim)
        data.setParam('NDGOFF', float(goff), currDim)
        data.setParam('NDC1', float(self.headerParams['C1']), currDim)
        # Signal that window function occured
        data.setParam('NDAPODCODE', float(1), currDim)


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