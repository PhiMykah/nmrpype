from .function import DataFunction as Function
import numpy as np

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class ZeroFill(Function):
    """
    class ZeroFill

    Data Function object for performing a zero-fill on the data
    """
    def __init__(self, zf_count : int = 0, zf_pad : int = 0, zf_size : int = 0,
                 zf_auto : bool = False, zf_inv : bool = False,
                 mp_enable = False, mp_proc = 0, mp_threads = 0):
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

        # Perform ZF without multiprocessing
        if not self.mp[0] or data.array.ndim == 1:
            data.array = self.process(data.array)
        else:
            data.array = self.parallelize(data.array)

        # Update header once processing is complete
        self.updateHeader()

        return 0

    ###################
    # Multiprocessing #
    ###################

    def parallelize(self, array : np.ndarray) -> np.ndarray:
        """
        fn parallelize

        Multiprocessing implementation for function to properly optimize for hardware

        Parameters:
        array : np.ndarray
            Target data array to process with function

        Returns:
        new_array : np.ndarray
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
            elif self.zf_count:
                # Double data zf_count times
                magnitude = 2**self.zf_count
                new_size = dataLength * magnitude
            elif self.zf_size:
                # Match user inputted size for new array
                new_size = self.zf_size 
            if self.zf_auto:
                # Reach next power of 2 with auto
                new_size = self.nextPowerOf2(dataLength)
        
        # Obtain new array shape and then create dummy array for data transfer
        new_shape = array.shape[:-1] + (new_size,)

        # Split array into manageable chunks
        chunk_size = int(array_shape[0] / self.mp[1])
        chunks = [array[i:i+chunk_size] for i in range(0, array_shape[0], chunk_size)]
        
        # Pad if size is larger and trim if size is shorter
        if new_size > dataLength:
            padding = new_size - dataLength
            operation = np.pad
            # Pass the chunk, the padding, and the padding function
            args = [(chunks[i], (0,padding), operation) for i in range(len(chunks))]
        else:
            operation = lambda a, size : a[:size]
            # Pass the chunk, the new array size, and the trimming function
            args = [(chunks[i], new_size, operation) for i in range(len(chunks))]
            
        # Process each chunk in processing pool
        with Pool(processes=self.mp[1]) as pool:
            output = pool.starmap(self.processMP, args, chunksize=chunk_size)

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(new_shape)
        return new_array
    

    def processMP(self, array : np.ndarray, arg, operation) -> np.ndarray:
        """
        fn processMP

        Process specifically for MP, changes how it performs operation

        Parameters
        ----------
        array : np.ndarray
            array to process

        args : tuple
            Arguments to implement for target operation

        operation : function
            function to call in each thread 

        Returns
        -------
        np.ndarray
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
            elif self.zf_count:
                # Double data zf_count times
                magnitude = 2**self.zf_count
                new_size = dataLength * magnitude
            elif self.zf_size:
                # Match user inputted size for new array
                new_size = self.zf_size 
            if self.zf_auto:
                # Reach next power of 2 with auto
                new_size = self.nextPowerOf2(dataLength)

        # Obtain new array shape and then create dummy array for data transfer
        new_shape = array.shape[:-1] + (new_size,)
        new_array = np.zeros(new_shape, dtype=array.dtype)

        # Ensure both arrays are matching for nditer operation based on size
        a = array if new_size > dataLength else array[...,:new_size]
        b = new_array[...,:dataLength] if new_size > dataLength else new_array

        # Iterate through each 1-D strip and copy over existing data
        it = np.nditer([a,b], flags=['external_loop', 'buffered'], 
                        op_flags=[['readonly'],['writeonly']],
                        buffersize=dataLength)
        with it:
            for x,y in it:
                y[...] = x

        # Flag operations following operation
        
        return new_array
    

    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser):
        """
        fn clArgs (ZF)

        Adds Zero Fill parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # ZF subparser
        ZF = subparser.add_parser('ZF', help='Perform a Zero Fill (ZF) Operation on the data')

        group = ZF.add_mutually_exclusive_group() 
        group.add_argument('-zf', type=int, metavar='count', default=0,
                        dest='zf_count', help='-Number of Times to Double the size')
        group.add_argument('-pad', type=int, metavar='padCount', default=0,
                        dest='zf_pad', help='Zeros to Add by Padding')
        group.add_argument('-size', type=int, metavar='xSize', default=0,
                        dest='zf_size', help='Desired Final size')
        group.add_argument('-auto', action='store_true',
                        dest='zf_auto', help='Round Final Size to Power of 2.')
        group.add_argument('-inv', action='store_true',
                        dest='zf_inv', help='Extract Original Time Domain.')
        
        # Include tail arguments proceeding function call
        Function.clArgsTail(ZF)


    ####################
    #  Proc Functions  #
    ####################
        
    def nextPowerOf2(x : int):
        return 1 if x == 0 else 2**(x-1).bit_length()
    

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
            else:
                zfCount = 0 if zfCount < 0 else zfCount
                for i in range (zfCount):
                    outSize *= 2
                zfSize = outSize
            if (self.zf_auto):
                zfSize = self.nextPowerOf2(int(zfSize))
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
    