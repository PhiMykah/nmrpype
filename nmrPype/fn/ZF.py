from .function import nmrFunction as Function

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
        from utils import UnsupportedDimension
        from numpy import zeros
        from numpy import append
        """
        fn fnZeroFill

        Performs a zero fill operation on the data
            Afterwards, update the header accordingly

        Parameters
        ----------
        params : dict
            Dictionary of all options for the Fourier Transform
        """
        try:
            data = self.data
            arr = data.np_data
            dimCount = int(data.getParam('FDDIMCOUNT'))
            
            currDim = int(data.header.currDim)

            # Make sure that multidimensional data appends to the correct axis
            target_axis = dimCount - currDim
            
            size = data.getTDSize()
            shape = arr.shape

            # Add Zeroes to designated data location
            if (self.zf_pad):
                if (len(shape) >= data.header.currDim):
                    # Convert shape to list to change shape dimensions
                    shape = list(shape)
                    # Change the target dimension to zeroes amount
                    shape[currDim-1] = self.zf_pad
                    shape = tuple(shape)
                else:
                    raise UnsupportedDimension

            # Create zeros nparray
            zf = zeros(shape, dtype='float32')
                    
            
            # Add zeroes to the data array
            data.np_data = append(arr, zf, target_axis)
            
            # Update header parameters
            self.updateHeader()
            self.updateFunctionHeader(size)

        except Exception as e:
            if hasattr(e, 'message'):
                raise type(e)(e.message + ' Unable to perform zero fill operation.')
            else:
                raise type(e)(' Unable to perform zero fill operation.')
            
    def updateFunctionHeader(self, size):
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
            outSize = size # Data output size
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
                    zfSize = size - self.zf_pad
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
            zfSize = size * 2
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
            mid += (outSize - size)
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