from .function import DataFunction as Function
import numpy as np
from scipy import fft

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class FourierTransform(Function):
    """
    class FourierTransform

    Data Function object for performing a DFFT or IDFFT on the data.
    """
    def __init__(self, ft_inv: bool = False, ft_real: bool = False, ft_neg: bool = False, ft_alt: bool = False, 
                 mp_enable = False, mp_proc = 0, mp_threads = 0):
            self.ft_inv = ft_inv 
            self.ft_real = ft_real
            self.ft_neg = ft_neg
            self.ft_alt = ft_alt
            self.mp = [mp_enable, mp_proc, mp_threads]
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

        self.initialize(data)
        
        ndQuad = int(data.getParam('NDQUADFLAG'))

        # Perform fft without multiprocessing
        if not self.mp[0] or data.array.ndim == 1:
            data.array = self.process(data.array, ndQuad)
        else:
            data.array = self.parallelize(data.array, ndQuad)

        # Update header once processing is complete
        self.updateHeader()

        return 0


    ###################
    # Multiprocessing #
    ###################

    def parallelize(self, array : np.ndarray, ndQuad : int) -> np.ndarray:
        """
        fn parallelize

        Multiprocessing implementation for function to properly optimize for hardware

        Parameters:
        array : np.ndarray
            Target data array to process with function

        ndQuad : int
            NDQUADFLAG header value

        Returns:
        new_array : np.ndarray
            Updated array after function operation
        """
        # Save array shape for reshaping later
        array_shape = array.shape

        # Split array into manageable chunks
        chunk_size = int(array_shape[0] / self.mp[1])
        chunks = [array[i:i+chunk_size] for i in range(0, array_shape[0], chunk_size)]
        
        # Process each chunk in processing pool
        args = [(chunks[i], ndQuad) for i in range(len(chunks))]
        with Pool(processes=self.mp[1]) as pool:
            output = pool.starmap(self.process, args, chunksize=chunk_size)

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(array_shape)
        return new_array

    def VectorFFT(self, array : np.ndarray) -> np.ndarray:
        array = fft.fft(array)
        array = fft.fftshift(array)
        array = np.flip(array)
        array = np.roll(array, 1)
        return(array)
        
    def VectorIFFT(self, array : np.ndarray) -> np.ndarray:
        array = fft.ifft(array)
        array = fft.ifftshift(array)
        array = np.flip(array)
        array = np.roll(array, 1)
        return(array)


    ######################
    # Default Processing #
    ######################

    def process(self, array : np.ndarray, ndQuad : int) -> np.ndarray:
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
        operation = self.VectorFFT if not self.ft_inv else self.VectorIFFT

        # Check for parallelization
        if self.mp[0] and not array.ndim == 1:
            with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
                processed_chunk = list(executor.map(operation, array))
                array = np.array(processed_chunk)
        else:
            it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=array.shape[-1])
            with it:
                for x in it:
                    x[...] = operation(x)

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
        # FT subparser
        FT = subparser.add_parser('FT', help='Perform a Fourier transform (FT) on the data')
        FT.add_argument('-inv', '--inverse', action='store_true',
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
