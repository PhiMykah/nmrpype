from .function import DataFunction as Function
import numpy as np
from sys import stderr

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

# type Imports/Definitions
from ..utils import DataFrame

class ZeroFill(Function):
    """
    Data Function object for performing a zero-fill on the data

    Parameters
    ----------
    zf_count : int
        Number of times to double the data

    zf_pad : int
        Number of zeros to pad the data by

    zf_size : int
        Set data to new size while filling empty data with zeros

    zf_auto : bool
        Automatically add zeros to pad data to the next power of two

    zf_inv : bool
        Reverse a zero-fill operation based on header params

    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, zf_count : int = -1, zf_pad : int = 0, zf_size : int = 0,
                 zf_auto : bool = False, zf_inv : bool = False,
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        self.zf_count = zf_count
        self.zf_pad = zf_pad
        self.zf_size = zf_size
        self.zf_auto = zf_auto
        self.zf_inv = zf_inv
        self.mp = [mp_enable, mp_proc, mp_threads]
        params = {'zf_count':zf_count, 'zf_pad':zf_pad, 'zf_size':zf_size,
                  'zf_auto':zf_auto, 'zf_inv':zf_inv}
        super().__init__(params)

    ############
    # Function #
    ############
            
    def run(self, data : DataFrame) -> int:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.run` for documentation
        """

        self.initialize(data)

        # Perform ZF without multiprocessing
        if not self.mp[0] or data.array.ndim == 1:
            data.array = self.process(data.array, (data.verb, data.inc, data.getParam('NDLABEL')))
        else:
            data.array = self.parallelize(data.array)

        # Update header once processing is complete
        self.updateHeader(data)

        return 0

    ###################
    # Multiprocessing #
    ###################

    def parallelize(self, array : np.ndarray) -> np.ndarray:
        """
        Multiprocessing implementation for function to properly optimize for hardware

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        Returns
        -------
        new_array : ndarray
            Updated array after function operation
        """
        # Save array shape for reshaping later
        array_shape = array.shape
        dataLength = array_shape[-1]

        # By default multiply size by 2
        new_size = dataLength * 2

        # check if undoing zero-fill operation
        if self.zf_inv:
            if self.zf_count:
                # Reduce size by 2 zf_count times, ensure size is nonzero positive
                new_size = int(dataLength / (2**self.zf_count))
                new_size = new_size if new_size > 0 else 1
            elif self.zf_pad:
                # Subtract padding, ensure size is nonzero positive
                new_size = dataLength - self.zf_pad
                new_size = new_size if new_size >= 1 else 1
            else: 
                # Divide size by 2 by default
                new_size = dataLength / 2
        else:
            if self.zf_pad:
                # Add amount of zeros corresponding to pad amount
                new_size += self.zf_pad
            elif self.zf_count >= 0:
                # Double data zf_count times
                magnitude = 2**self.zf_count
                new_size = dataLength * magnitude
            elif self.zf_size:
                # Match user inputted size for new array
                new_size = self.zf_size 
            if self.zf_auto:
                # Reach next power of 2 with auto
                new_size = ZeroFill.nextPowerOf2(dataLength)
        
        # Obtain new array shape and then create dummy array for data transfer
        new_shape = array.shape[:-1] + (new_size,)

        # Split array into manageable chunks
        chunk_size = int(array_shape[0] / self.mp[1])

        # Assure chunk_size is nonzero
        chunk_size = array_shape[0] if chunk_size == 0 else chunk_size
        
        chunks = [array[i:i+chunk_size] for i in range(0, array_shape[0], chunk_size)]

        # Pad if size is larger and trim if size is shorter
        if new_size > dataLength:
            padding = new_size - dataLength
            operation = np.pad

            # Only pad the last dimension by unchanging other dimension
            pad_width = [[0,0] for i in range(chunks[0].ndim-1)]
            pad_width[-1][-1] = padding

            # Pass the chunk, the pad width, and the padding function
            args = [(chunks[i], pad_width, operation) for i in range(len(chunks))]
        else:
            operation = ZeroFill.truncate
            # Pass the chunk, the new array size, and the trimming function
            args = [(chunks[i], new_size, operation) for i in range(len(chunks))]
            
        # Process each chunk in processing pool
        with Pool(processes=self.mp[1]) as pool:
            output = pool.starmap(self.processMP, args, chunksize=chunk_size)

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(new_shape)
        return new_array
    

    def processMP(self, array : np.ndarray, arg : tuple, operation) -> np.ndarray:
        """
        Process specifically for MP, changes how it performs operation

        Parameters
        ----------
        array : ndarray
            array to process

        args : tuple
            Arguments to implement for target operation

        operation : function
            function to call in each thread 

        Returns
        -------
        ndarray
            modified array post-process
        """
        args = ((array[i], arg) for i in range(len(array))) 

        with ThreadPoolExecutor(max_workers=self.mp[2]) as executor:
            processed_chunk = list(executor.map(lambda p: operation(*p), args))
            array = np.array(processed_chunk)
        return array
    

    ######################
    # Default Processing #
    ######################

    def process(self, array : np.ndarray, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.process` for documentation
        """
        # Collect last axis shape to fill array size
        dataLength = array.shape[-1]

        # By default multiply size by 2 
        new_size = dataLength * 2

        # check if undoing zero-fill operation
        if self.zf_inv:
            if self.zf_count:
                # Reduce size by 2 zf_count times, ensure size is nonzero positive
                new_size = int(dataLength / (2**self.zf_count))
                new_size = new_size if new_size > 0 else 1
            elif self.zf_pad:
                # Subtract padding, ensure size is nonzero positive
                new_size = dataLength - self.zf_pad
                new_size = new_size if new_size >= 1 else 1
            else: 
                # Divide size by 2 by default
                new_size = dataLength / 2
        else:
            if self.zf_pad:
                # Add amount of zeros corresponding to pad amount
                new_size = dataLength
                new_size += self.zf_pad
            elif self.zf_count >= 0:
                # Double data zf_count times
                magnitude = 2**self.zf_count
                new_size = dataLength * magnitude
            elif self.zf_size:
                # Match user inputted size for new array
                new_size = self.zf_size 
            if self.zf_auto:
                # Reach next power of 2 with auto
                new_size = ZeroFill.nextPowerOf2(dataLength)

        # Obtain new array shape and then create dummy array for data transfer
        new_shape = array.shape[:-1] + (new_size,)
        new_array = np.zeros(new_shape, dtype=array.dtype)

        # Ensure both arrays are matching for nditer operation based on size
        a = array if new_size > dataLength else array[...,:new_size]
        b = new_array[...,:dataLength] if new_size > dataLength else new_array

        # Iterate through each 1-D strip and copy over existing data
        it = np.nditer([a,b], flags=['external_loop', 'buffered'], 
                        op_flags=[['readonly'],['writeonly']],
                        buffersize=dataLength, order='C')
        with it:
            for x,y in it:
                if verb[0]:
                    Function.verbPrint('ZF', it.iterindex, it.itersize, array.shape[-1], verb[1:])
                y[...] = x
            if verb[0]:
                print("", file=stderr)

        # Flag operations following operation
        
        return new_array
    

    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Zero Fill command-line arguments

        Adds Zero Fill parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # ZF subparser
        ZF = subparser.add_parser('ZF', parents=[parent_parser], help='Perform a Zero Fill (ZF) Operation on the data')
        
        ZF.add_argument('-auto', action='store_true',
                        dest='zf_auto', help='Round Final Size to Power of 2')
        
        group = ZF.add_mutually_exclusive_group() 
        group.add_argument('-zf', type=int, metavar='count', default=-1,
                        dest='zf_count', help='-Number of Times to Double the size')
        group.add_argument('-pad', type=int, metavar='padCount', default=0,
                        dest='zf_pad', help='Zeros to Add by Padding')
        group.add_argument('-size', type=int, metavar='xSize', default=0,
                        dest='zf_size', help='Desired Final size')
        group.add_argument('-inv', action='store_true',
                        dest='zf_inv', help='Extract Original Time Domain')
        
        # Include tail arguments proceeding function call
        # Function.clArgsTail(ZF)


    ####################
    #  Proc Functions  #
    ####################
        
    @staticmethod
    def nextPowerOf2(x : int):
        """
        Helper function to set input integer to the nearest power of two
        greater than input integer.
        """
        return 1 if x == 0 else 2**(x-1).bit_length()
    
    @staticmethod
    def truncate(array : np.array, size : int):
        return array[...,:size]

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
        currDim = data.getCurrDim()
        outSize = data.getParam('NDAPOD', currDim)
        currDimSize = outSize
        zfSize = self.zf_size
        zfCount = 1

        # See userproc.c ln453-468 for more information
        if (self.zf_inv):
            if (self.zf_count > 0):
                for i in range(self.zf_count):
                    outSize /= 2
                zfSize = outSize if (outSize > 0) else 1
                outSize = zfSize
            elif(self.zf_pad > 0):
                zfSize = outSize - self.zf_pad
                zfSize = 1 if (zfSize < 1) else zfSize
                outSize = zfSize
            else:
                zfSize = data.getParam('NDAPOD',currDim)
                outSize = zfSize
        else:
            if (self.zf_size):
                outSize = zfSize
            elif (self.zf_pad):
                zfSize = outSize + self.zf_pad
                outSize = zfSize
            elif self.zf_count >= 0:
                magnitude = 2**self.zf_count
                zfSize = outSize * magnitude
            if (self.zf_auto):
                zfSize = ZeroFill.nextPowerOf2(int(zfSize))
                outSize = zfSize

        #zfSize = outSize * 2
        #outSize = zfSize

        # Parameters to update based on zerofill
        mid   = data.getParam('NDCENTER', currDim)
        orig  = data.getParam('NDORIG',   currDim)
        car   = data.getParam('NDCAR',    currDim)
        obs   = data.getParam('NDOBS',    currDim)
        sw    = data.getParam('NDSW',     currDim)
        ix1   = data.getParam('NDX1',     currDim)
        ixn   = data.getParam('NDXN',     currDim)
        izf   = data.getParam('NDZF',     currDim) # Currently unused
        fSize = outSize

        # Check if FT has been performed on data, unlikely but plausible
        if (bool(data.getParam('NDFTFLAG'))):
            mid += (outSize - currDimSize)
            data.setParam('NDCENTER', mid, currDim)
        else:
            if (data.getParam('NDQUADFLAG', currDim) == 1):
                fSize = outSize/2
            else:
                fSize = outSize
            if (ix1 or ixn):
                # Currently unimplemented in the c code
                pass
            else:
                mid = fSize/2 + 1
                orig = obs*car - sw*(fSize - mid)/fSize
            
            data.setParam('NDZF',     float(-1*outSize), currDim)
            data.setParam('NDCENTER', float(mid),      currDim)
            data.setParam('NDX1',     float(ix1),      currDim)
            data.setParam('NDXN',     float(ixn),      currDim)
            data.setParam('NDORIG',    orig,           currDim)
    
        if (currDim == 3 or currDim == 4):
            data.setParam('NDSIZE', float(outSize), currDim)
        else:
            data.setParam('FDSIZE', float(outSize), currDim)

        # Update maximum size if size exceeds maximum size (NYI)
        """
        if (outSize > maxSize)
           {
            dataInfo->maxSize = dataInfo->outSize;
           }
        """


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
    