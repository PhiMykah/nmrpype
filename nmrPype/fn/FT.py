from .function import DataFunction as Function
import numpy as np
from scipy import fft

class FourierTransform(Function):
    def __init__(self, ft_inv: bool = False, ft_real: bool = False, ft_neg: bool = False, ft_alt: bool = False):
            """
            class FourierTransform

            Data Function object for performing a DFFT or IDFFT on the data.
            """
            self.ft_inv = ft_inv 
            self.ft_real = ft_real
            self.ft_neg = ft_neg
            self.ft_alt = ft_alt
            params = {'ft_inv':ft_inv, 'ft_real': ft_real, 'ft_neg': ft_neg, 'ft_alt': ft_alt}
            super().__init__(params) 
    
    ############
    # Function #
    ############
            
    def run(self, data) -> int:
        """
        fn run

        Main body of FFT code.
            - Initializes Header
            - Determine process to run using flags
            - Start Process (process data vector by vector in multiprocess)
            - Update Header
            - Return information if necessary

        Overload run for function specific operations

        Parameters
        ----------
        data : DataFrame
            Target data to to run function on

        Returns
        -------
        Integer exit code (e.g. 0 success 1 fail)
        """

        self.initialize()

        ndQuad = int(data.getParam('NDQUADFLAG'))
        #for loop iterating over processes
        #   p = mp.Process(self.process, (data, array, ndQuad))

        # Update header once processing is complete
        self.updateHeader()
        return 0

    def process(self, data, array : np.ndarray, ndQuad : int) -> np.ndarray:
        """
        fn process

        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed

        Parameters
        ----------
        array : np.ndarray (ndim = 1)
            1-D array processed

        Returns
        -------
        np.ndarray
            modified array post-process
        """
        # Change operation based on parameters
        if (self.ft_alt and not self.ft_inv):
            # Alternate real and imaginary prior to transform
            pass
        if (self.ft_neg and not self.ft_inv):
            # Negate all imaginary values prior to transform
            pass
        if (self.ft_real and ndQuad != 1):
            # Set all imaginary values to 0
            pass

        # Perform dfft or idfft depending on args
        operation = fft.fft if not self.ft_inv else fft.ifft

        # Flag operations following operation

        if (self.ft_real):
            pass
    
        if (self.ft_alt and self.ft_inv):
            # Alternate after ifft if necessary
            pass

        if (self.ft_neg and self.ft_inv):
            # Negate all imaginary values after ifft if necessary
            pass
        
        return array
    
    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser):
        """
        fn commands (Template)

        Adds function parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # FT subparser
        FT = subparser.add_parser('FT', help='Perform a Fourier transform (FT) on the data')
        FT.add_argument('-inverse', '-inv', action='store_true',
                        dest='ft_inv', help='Perform inverse FT')
        FT.add_argument('-real', action='store_true',
                        dest='ft_real', help='Perform a FT only on the real portion of the data')
        FT.add_argument('-neg', action='store_true',
                        dest='ft_neg', help='Negate imaginaries when performing FT')
        FT.add_argument('-alt', action='store_true',
                        dest='ft_alt', help='Use sign alternation when performing FT')
        
        # Include tail arguments proceeding function call
        Function.clArgsTail(FT)


    ####################
    # Proc Functions #
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
        currDim = data.getCurrDim()

        ftFlag = int(data.getParam('NDFTFLAG', currDim))

        # Flip value of ft flag
        ftFlag = 0 if ftFlag else 1

        # Set FT flag
        data.setParam('NDFTFLAG', float(ftFlag), currDim)

        size = data.array.shape[-1*currDim]

        # Update FT flag based parameters if necessary
        if ftFlag:
            data.setParam('NDAQSIGN', float(0), currDim)
            data.setParam('NDFTSIZE', float(size), currDim)

        # Set Quad flags
        data.setParam('FDQUADFLAG', float(0), currDim)
        data.setParam('NDQUADFLAG', float(0), currDim)
        
        #outQuadState = 2

        # If real update real parameters
        if self.ft_real:
            tdSize = data.getParam()
            outSize = size/2
            tdSize /= 2

            data.setParam('NDSIZE', float(outSize), currDim)
            data.setParam('NDTDSIZE', float(tdSize), currDim)


    def updateHeader(self):
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
