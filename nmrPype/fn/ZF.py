from .function import nmrFunction as Function
from . import catchError, FunctionError

class ZeroFill(Function):
    def __init__(self, data, zf_count : int = 0, zf_pad : int = 0, zf_size : int = 0,
                            zf_auto : bool = False, zf_inv: bool = False):
        self.zf_count = zf_count
        self.zf_pad = zf_pad
        self.zf_size = zf_size
        self.zf_auto = zf_auto
        self.zf_inv = zf_inv
        params = {'zf_count':zf_count, 'zf_pad':zf_pad, 'zf_size':zf_size, 'zf_auto':zf_auto, 'zf_inv':zf_inv}
        super().__init__(data,params)

    @staticmethod
    def commands(subparser):
        """
        fn commands

        Adds Zero Fill parser to the subparser, with its corresponds
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument},
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
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

        # Include universal commands proceeding function call
        Function.universalCommands(ZF)

    def nextPowerOf2(x : int):
        return 1 if x == 0 else 2**(x-1).bit_length()

    def run(self):
        """
        fn run

        Zerofill has a unique run operation due to allocating new data

        Parameters
        ----------
        array : ndarray (1-D)
            Array to perform operation on, passed from run
        """
        from utils import EmptyNMRData
        import sys

        try:
            # Ensure data is available to modify
            array = self.data.np_data
            if type(array) is None:
                raise EmptyNMRData("No data to modify!")
            
            # Update header before processing data
            self.updateHeader()

            # Take parameters from dictionary and allocate to designated header locations
            sizes = self.obtainSizes()

            # Update np_data array to new modified array
            self.data.np_data = self.func(array)

            # Process data 
            self.updateHeader()
            self.updateFunctionHeader(sizes)

        # Exceptions
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)


    def func(self, array):
        """
        fn func 
        Expands the array shape then copys data over through 1-D strips

        Header updating operations are performed outside scope

        This implementation is unique because the loop is contained here rather
            than in run()

        Parameters
        ----------
        array : ndarray
            N-dimensional array to perform operation on, passed from run
        Returns
        -------
        new_array : ndarray
            Modified array of N dimensions after operation
        """
        from numpy import zeros
        from numpy import nditer
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
        new_array = zeros(new_shape, dtype=array.dtype)

        # Ensure both arrays are matching for nditer operation based on size
        a = array if new_size > dataLength else array[...,:new_size]
        b = new_array[...,:dataLength] if new_size > dataLength else new_array

        # Iterate through each 1-D strip and copy over existing data
        it = nditer([a,b], flags=['external_loop','buffered'],
            op_flags=[['readonly'],['writeonly']],
            buffersize=dataLength)
        with it:
            for x, y in it:
                y[...] = x

        return new_array
    
    def updateFunctionHeader(self, sizes):
        """
        fn updateFunctionHeader

        Implementation of parameter updating seen in nmrPipe source code
            See 'userproc.c'

        Parameters
        ----------
        size : int
            Current size of time domain
        """ 
        get = self.data.getParam
        mod = self.data.modifyParam
        currDim = int(self.data.header.currDim)
        try: 
            apod = self.data.header.checkParamSyntax('NDAPOD', currDim)
            currDimSize = sizes[apod]
            outSize = currDimSize # Data output size
            zfSize = self.zf_size # Size of data based on zerofill
            zfCount = 1
            # See userproc.c line 453-468 for more information
            if (self.zf_inv):
                if (self.zf_count > 0):
                    for i in range(self.zf_count):
                        outSize /= 2
                    zfSize = outSize if (outSize > 0) else 1
                    outSize = zfSize
                elif(self.zf_pad > 0):
                    zfSize = currDimSize - self.zf_pad
                    zfSize = 1 if (zfSize < 1) else zfSize
                    outSize = zfSize
                else:
                    zfSize = get('NDAPOD',currDim)
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
        except KeyError: # Use default values if params is empty or inaccessible 
            zfSize = currDimSize * 2
            outSize = zfSize

        # Parameters to update based on zerofill
        mid   = get('NDCENTER', currDim)
        orig  = get('NDORIG',   currDim)
        car   = get('NDCAR',    currDim)
        obs   = get('NDOBS',    currDim)
        sw    = get('NDSW',     currDim)
        ix1   = get('NDX1',     currDim)
        ixn   = get('NDXN',     currDim)
        izf   = get('NDZF',     currDim) # Currently unused
        fSize = outSize

        # Check if FT has been performed on data, unlikely but plausible
        if (bool(get('NDFTFLAG'))):
            mid += (outSize - currDimSize)
            mod('NDCENTER', mid, currDim)
        else:
            if (get('NDQUADFLAG', currDim) == 1):
                fSize = outSize/2
            else:
                fSize = outSize
            if (ix1 or ixn):
                # Currently unimplemented in the c code
                pass
            else:
                mid = fSize/2 + 1
                orig = obs*car - sw*(fSize - mid)/fSize
            
            mod('NDZF',     float(-1*outSize), currDim)
            mod('NDCENTER', float(mid),      currDim)
            mod('NDX1',     float(ix1),      currDim)
            mod('NDXN',     float(ixn),      currDim)
            mod('NDORIG',    orig,           currDim)
    
        if (currDim == 3 or currDim == 4):
            mod('NDSIZE', float(outSize), currDim)
        else:
            mod('FDSIZE', float(outSize), currDim)

        # Update maximum size if size exceeds maximum size (NYI)
        """
        if (outSize > maxSize)
           {
            dataInfo->maxSize = dataInfo->outSize;
           }
        """