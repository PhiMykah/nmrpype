from .function import DataFunction as Function
import numpy as np
from scipy import fft
from sys import stderr
# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class FourierTransform(Function):
    """
    Data Function object for performing a DFFT or IDFFT on the data.

    Parameters
    ----------
    ft_inv : bool
        Use inverse fourier transform instead of fourier transform

    ft_real : bool
        Perform fourier transform on the real data only

    ft_neg : bool
        Negate imaginary values when performing fourier transform

    ft_alt : bool
        Alternate the signs of even and odd data points
    
    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, ft_inv: bool = False, ft_real: bool = False, ft_neg: bool = False, ft_alt: bool = False, 
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
            self.ft_inv = ft_inv 
            self.ft_real = ft_real
            self.ft_neg = ft_neg
            self.ft_alt = ft_alt
           
            self.mp = [mp_enable, mp_proc, mp_threads]
            self.name = "FT"
            
            params = {'ft_inv':ft_inv, 'ft_real': ft_real, 'ft_neg': ft_neg, 'ft_alt': ft_alt}
            super().__init__(params) 
    
    ############
    # Function #
    ############
            
    def run(self, data : DataFrame) -> int:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.run` for documentation
        """

        self.initialize(data)
        
        ndQuad = 1 if not np.all(data.array.imag) else 2

        # Perform fft without multiprocessing
        if not self.mp[0] or data.array.ndim == 1:
            data.array = self.process(data.array, ndQuad, (data.verb, data.inc, data.getParam('NDLABEL')))
        else:
            data.array = self.parallelize(data.array, ndQuad, (data.verb, data.inc, data.getParam('NDLABEL')))

        # Update header once processing is complete
        self.updateHeader(data)

        return 0


    ###################
    # Multiprocessing #
    ###################

    def parallelize(self, array : np.ndarray, ndQuad : int, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
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
        
        chunk_num = len(chunks)
        # Process each chunk in processing pool
        args = []
        for i in range(chunk_num):
            if i == 0:
                args.append((chunks[i], ndQuad, verb))
            else:
                args.append((chunks[i], ndQuad))

        if verb[0]:
            Function.mpPrint("FT", chunk_num, (len(chunks[0]), len(chunks[-1])), 'start')

        with Pool(processes=self.mp[1]) as pool:
            output = pool.starmap(self.process, args, chunksize=chunk_size)

        if verb[0]:
            Function.mpPrint("FT", chunk_num, (len(chunks[0]), len(chunks[-1])), 'end')

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(array_shape, order='C')
        return new_array

    def vectorFFT(self, array : np.ndarray) -> np.ndarray:
        """
        Perform fourier transform on 1D array, transform result to match nmrPipe

        Parameters
        ----------
        array : ndarray
            Target vector 

        Returns
        -------
        ndarray
            Processed vector
        """
        array = fft.fft(array)
        array = fft.fftshift(array)
        array = np.flip(array)
        array = np.roll(array, 1)
        return(array)
        
    def vectorIFFT(self, array : np.ndarray) -> np.ndarray:
        """
        Perform inverse fourier transform on 1D array, transform result to match nmrPipe

        Parameters
        ----------
        array : ndarray
            Target vector 
            
        Returns
        -------
        ndarray
            Processed vector
        """
        array = fft.ifft(array)
        array = fft.ifftshift(array)
        array = np.flip(array)
        array = np.roll(array, 1)
        return(array)


    ######################
    # Default Processing #
    ######################

    def process(self, array : np.ndarray, ndQuad : int, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.process` for documentation
        """
        # Change operation based on parameters
        if (self.ft_alt and not self.ft_inv):
            # Alternate real and imaginary prior to transform
            array.real = FourierTransform.alternate(array.real)
            array.imag = FourierTransform.alternate(array.imag)
            
        if (self.ft_neg and not self.ft_inv):
            # Negate all imaginary values prior to transform
            array.imag = FourierTransform.negate(array.imag)

        if (self.ft_real and ndQuad != 1):
            # Set all imaginary values to 0
            array.imag = np.zeros_like(array.imag)

        # Perform dfft or idfft depending on args
        operation = self.vectorFFT if not self.ft_inv else self.vectorIFFT

        # -------------------------------------------------
        # USAGE OF THREADS IS BUGGED WITH FT, OBSOLETE CODE
        # -------------------------------------------------
        # Check for parallelization
        # if self.mp[0] and (1 < array.ndim < 4):
        #     with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
        #         processed_chunk = list(executor.map(operation, array))
        #         array = np.array(processed_chunk, order='C')
        # else:
        it = np.nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=array.shape[-1], order='C')
        with it:
            for x in it:
                if verb[0]:
                    Function.verbPrint('FT', it.iterindex, it.itersize, array.shape[-1], verb[1:])
                x[...] = operation(x)
            if verb[0]:
                print("", file=stderr)

        # Flag operations following operation

        if (self.ft_real):
            # Python implementation of vvCopy64 in vutil.h/vutil.c of nmrpipe
            outSize = len(array)
            size = outSize/2
            array.real[...,:outSize] = array.real[...,size/2:outSize]
            array.real[...,:outSize] = array.real[...,size/2:outSize]
    
        if (self.ft_alt and self.ft_inv):
            # Alternate after ifft if necessary
            array.real = FourierTransform.alternate(array.real)
            array.imag = FourierTransform.alternate(array.imag)

        if (self.ft_neg and self.ft_inv):
            # Negate all imaginary values after ifft if necessary
            array.imag = FourierTransform.negate(array.imag)
        
        return array
    

    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Fourier Transform command-line arguments

        Adds Fourier Transform parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # FT subparser
        FT = subparser.add_parser('FT', parents=[parent_parser], help='Perform a Fourier transform (FT) on the data')
        FT.add_argument('-inv', '--inverse', action='store_true',
                        dest='ft_inv', help='Perform inverse FT')
        FT.add_argument('-real', action='store_true',
                        dest='ft_real', help='Perform a FT only on the real portion of the data')
        FT.add_argument('-neg', action='store_true',
                        dest='ft_neg', help='Negate imaginaries when performing FT')
        FT.add_argument('-alt', action='store_true',
                        dest='ft_alt', help='Use sign alternation when performing FT')
        
        # Include tail arguments proceeding function call
        # Function.clArgsTail(FT)

    @staticmethod
    def negate(array : np.ndarray) -> np.ndarray:
        """
        Negate values of inputted array
        """
        return -1 * array

    @staticmethod
    def alternate(array : np.ndarray, positiveStart : bool = True):
        """
        Return inputted array with alternating signs from postitive to negative

        Parameters
        ----------
        array : ndarray
            Target array to sign alternate, assumed to be non-complex

        positiveStart : bool
            Set whether the values start as negative or positive

        Returns
        -------
        ndarray
            Sign alternating array
        """
        # Make an array of ones similar to the array
        signs = np.ones_like(array)

        # Half of the ones are set to negative, the other half positive 
        negative = -1*signs[...,1::2]
        positive = np.absolute(signs[...,::2])
        signs[...,1::2] = negative if positiveStart else positive
        signs[...,::2] = positive if positiveStart else negative
        return np.absolute(array) * signs


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

        # Automatically set real flag if data is real (possibly)
    

        ftFlag = int(data.getParam('NDFTFLAG', currDim))

        # Flip value of ft flag
        ftFlag = 0 if ftFlag else 1

        # Set FT flag
        data.setParam('NDFTFLAG', float(ftFlag), currDim)

        if data.getDimOrder(1) == 1:
            size = data.getParam('NDSIZE', currDim)
        else:
            size = data.getParam('NDTDSIZE', currDim)

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
