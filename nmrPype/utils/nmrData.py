import numpy as np
from .header import UnknownHeaderParam, UnsupportedDimension, EmptyNMRData

from nmrglue import pipe
import sys

def nextPowerOf2(x : int):
    return 1 if x == 0 else 2**(x-1).bit_length()

class NMRData:
    """
    NMRData class

    Object containing the information about the NMR data as well as the data itself,
    with methods for accessing and modifying the data based on the header included with the data.

    Parameters
    ----------
    file : str
        Input file or stream to obtain the header and nmr data from
    Values
    ----------
    header : Header
        Header class object containing the header as a dictionary,
          as binary data, and methods for manipulating the parameters
    np_data : ndarray
        Numpy array with float32 data
    """
    def __init__(self, file : str = None):
        self.header = None
        self.np_data = None
        if (file): # Read only if file is provided
            self.readFile(file)


    def getTDSize(self): 
        dimCount = self.getParam('FDDIMCOUNT')
        if self.header.currDim == 1:
            size = len(self.np_data[0]) if dimCount > 1 else len(self.np_data)
        elif self.header.currDim == 2:
            size = len(self.np_data)
        else:
            size = len(self.np_data)
        return size
    
    def readFile(self, file):
        from utils import Header
        """
        fn readFile

        set the header object and data array based on the input file

        Parameters
        ----------
        file
            Input file or stream to obtain the header and nmr data from
        """
        try: # Attempt to read file using nmr glue
            dic,data = pipe.read(file)
            try:
                if hasattr(file, "read"):
                    hStream = file.read(512)
                else:
                    with open(file, 'rb') as f:
                        hStream = f.read(512)
            except Exception as e:
                print(f"{e}: Unable to read header stream!")
                sys.exit(0)
                return
        except Exception as e:
            print(f"{e}: Unable to read file!")
            sys.exit(0)
        else:
            self.header = Header(dic, hStream)
            self.np_data = data


    def writeOut(self, output, overwrite: bool):
        from utils import Header
        """
        fn writeOut

        Attempts to output the user's nmrData depending on the type of output
        This code is an adoption of the nmrglue.pipe.write 
        method to accomodate for output stream

        Parameters
        ----------
        output 
            Either the output file path or the standard ouput buffer
        overwrite : bool
            Choose whether or not to overwrite existing files for file output
        """
        # Determine if output is to file or output stream
        if not hasattr(output, 'write'):
            self.writeToFile(output, overwrite)
        else:
            match self.np_data.ndim:
                case 1:
                    self.writeToBuffer(output, self.header.getDict(), self.np_data)
                case 2:
                    self.writeToBuffer(output, self.header.getDict(), self.np_data)
                case 3:
                    lenZ, lenY, lenX = self.np_data.shape
                    for zi in range(lenZ):
                        plane = self.np_data[zi]
                        self.writeToBuffer(output, self.header.getDict(), plane)
                case 4:
                    lenA, lenZ, lenY, lenX = self.np_data.shape
                    new_header = Header(self.header.hDict, self.header.hStream)
                    for ai in range(lenA):
                        for zi in range(lenZ):
                            plane = np.data[ai, zi]

                            # update dictionary if needed
                            if new_header.getParam("FDSCALEFLAG") == 1:
                                new_header.setParam("FDMAX", plane.max())
                                new_header.setParam("FDDISPMAX", new_header.getParam("FDMAX"))
                                new_header.setParam("FDMIN", plane.min())
                                new_header.setParam("FDDISPMIN", new_header.getParam("FDMIN"))
                            self.writeToBuffer(output, self.header.getDict(), plane)
                case _:
                    raise UnsupportedDimension('Dimension provided in header \
                                                           is currently unsupported!')
              
        
    def writeToFile(self, outFileName : str, overwrite : bool = False): 
        """
        fn writeToFile

        Writes the nmrData and its header to a file of the user's choice

        Parameters
        ----------
        outFileName : str
            Output file or stream to send the header and nmr data to
        overwrite : bool
            Bool represents whether or not to overwrite file if the file exists
        current warning: 
        """
        try:
            pipe.write(outFileName, self.header.getDict(), self.np_data, overwrite)
        except Exception as e:
            print(e)


    def writeToBuffer(self, bufferStream, dic, data): 
        """
        fn writeToBuffer

        Writes the nmrData and its header to the standard output as bytes

        Parameters
        ----------
        outFileName : str
            Output file or stream to send the header and nmr data to
        overwrite : bool
            Bool represents whether or not to overwrite file if the file exists
        current warning: 

        Returns
        ----------
        Returns in binary output stream the header as well as data
        """
        try:
            """
            Modification of nmrglue.pipe source code for write to accomodate buffer
            """

            # load all data if the data is not a numpy ndarray
            if not isinstance(data, np.ndarray):
                data = data[:]

            # append imaginary and flatten
            if data.dtype == "complex64":
                data = pipe.append_data(data)
            data = data.flatten()

            # create the fdata array
            fdata = pipe.dic2fdata(dic)

            """
            Put fdata and data to 2D NMRPipe.
            """
            # check for proper datatypes
            if data.dtype != 'float32':
                # print(data.dtype)
                raise TypeError('data.dtype is not float32')
            if fdata.dtype != 'float32':
                raise TypeError('fdata.dtype is not float32')
            
            bufferStream.write(fdata.tobytes())
            bufferStream.write(data.tobytes())
            
        except Exception as e:
            print(e)
            print("An exception occured when attempting to write data to buffer!")
            pass


    def modifyParam(self, param , value, dim = 0):
        """
        fn modify
        ***** Primarily used Internally for Header Modification *******

        Modifies the indicated parameter from the header file

        param: str
            Header parameter to modify, must be a valid parameter

        value: str
            String representing the new numerical value associated with the given parameter

        dim: int
            Designated dimension to look at if using ND syntax
        """
        try:
            if (self.header == None):
                raise EmptyNMRData("No data to modify!")
            isParamSet = self.header.setParam(param, value, dim) # Checks for valid param and sets if possible
            if isParamSet:
                return True
            else:
                raise UnknownHeaderParam("Parameter unable to be set!")
        except Exception as e:
            if hasattr(e,'message'):
                raise type(e)(e.message + ' Unable to modify parameter.')
            else:
                raise type(e)(' Unable to modify parameter.')


    def getParam(self, param, dim: int = 0):
        """
        fn getParam

        Obtains the indicated parameter from the header file

        Parameters
        ----------
        param: str
            Header parameter to modify, must be a valid parameter

        dim: int
            Designated dimension to look at if using ND syntax

        Returns
        ----------
        Returns value from designated param
            otherwise raises UnknownHeaderParam error
        """
        return(self.header.getParam(param, dim))

    def runFunction(self, fn : str, arguments: dict):
        from fn import Function
        from fn import FT
        """
        fn runFunction

        Function that runs the function passed as a string keyword
        using the Function class and its children.

        Parameters
        ----------
        fn : str
            Function code for the designated function to run
        arguments : dict
            Dictionary of arguments for the designated function
        """
        match fn:
            case 'FT':
                function = FT(self, **arguments)
            case _:
                function = Function(self, arguments)
        function.run()
    
    ###############
    #  Functions  #
    ###############
            
    def updateFT(self, size, params):
        currDim = self.header.getcurrDim()
        # Flip FT flag
        if (bool(self.getParam('NDFTFLAG'))):
            self.modifyParam('NDFTFLAG', float(0), currDim) 
        else:
            self.modifyParam('NDFTFLAG', float(1), currDim) 

        # Set NDAQSIGN and NDFTSIZE
        if (bool(self.getParam('NDFTFLAG'))):
            self.modifyParam('NDAQSIGN', float(0), currDim)
            self.modifyParam('NDFTSIZE', self.getTDSize(), currDim)
        else:
            # Implement `dataInfo->outQuadState = 2`
            self.modifyParam('NDFTSIZE', self.getTDSize(), currDim) 

        # Add flag for complex
        self.modifyParam('FDQUADFLAG', float(0))
        self.modifyParam('NDQUADFLAG', float(0), currDim)  
        
        # Check for real flag, and update based on real (divide the size by 2)
        if 'ft_real' in params:
            size = size/2 if params['ft_real'] else size
            self.modifyParam('NDAPOD', float(size), currDim)  


    """ 
    Zero Fill (ZF)
    """
    def fnZeroFill(self, params: dict = {}):
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
            arr = self.np_data
            dimCount = int(self.getParam('FDDIMCOUNT'))
            # Make sure that multidimensional data appends to the correct axis
            target_axis = 0 if \
                (dimCount == 1) \
                else 1
            
            currDim = int(self.header.currDim)
            size = self.getTDSize()
            shape = arr.shape

            # Add Zeroes to designated data location
            if (params):
                if (params['zf_pad']):
                    if (len(shape) >= self.header.currDim):
                        # Convert shape to list to change shape dimensions
                        shape = list(shape)
                        # Change the target dimension to zeroes amount
                        shape[currDim-1] = params['zf_pad']
                        shape = tuple(shape)
                    else:
                        raise UnsupportedDimension

            # Create zeros nparray
            zf = np.zeros(shape, dtype='float32')
                    
            
            # Add zeroes to the data array
            self.np_data = np.append(arr, zf, target_axis)
            
            # Update header parameters
            self.updateHeader(size, 'ZF', params)
        except Exception as e:
            if hasattr(e, 'message'):
                raise type(e)(e.message + ' Unable to perform zero fill operation.')
            else:
                raise type(e)(' Unable to perform zero fill operation.')

    def updateZF(self, size, params):
        """
        fn updateZF

        Implementation of parameter updating seen in nmrPipe source code
            See 'userproc.c'

        Parameters
        ----------
        size : int
            Current size of time domain
        params : dict
            Dictionary of all options for Zero Fill
        """ 
        try: 
            outSize = size # Data output size
            zfSize = params['zf_size'] # Size of data based on zerofill
            zfCount = 1
            # See userproc.c line 453-468 for more information
            if (params['zf_inv']):
                if (params['zf_count'] > 0):
                    for i in range(params['zf_count']):
                        outSize /= 2
                    zfSize = outSize if (outSize > 0) else 1
                    outSize = zfSize
                elif(params['zf_pad'] > 0):
                    zfSize = size - params['zf_pad']
                    zfSize = 1 if (zfSize < 1) else zfSize
                    outSize = zfSize
                else:
                    zfSize = self.getParam('NDAPOD',self.header.currDim)
                    outSize = zfSize
            else:
                if (params['zf_size']):
                    outSize = zfSize
                elif (params['zf_pad']):
                    zfSize = outSize + params['zf_pad']
                    outSize = zfSize
                else:
                    zfCount = 0 if zfCount < 0 else zfCount
                    for i in range (zfCount):
                        outSize *= 2
                    zfSize = outSize
                if (params['zf_auto']):
                    zfSize = nextPowerOf2(int(zfSize))
                    outSize = zfSize
        except KeyError: # Use default values if params is empty or inaccessible 
            zfSize = size * 2
            outSize = zfSize

        currDim = int(self.header.currDim)

        # Parameters to update based on zerofill
        mid   = self.getParam('NDCENTER', currDim)
        orig  = self.getParam('NDORIG',   currDim)
        car   = self.getParam('NDCAR',    currDim)
        obs   = self.getParam('NDOBS',    currDim)
        sw    = self.getParam('NDSW',     currDim)
        ix1   = self.getParam('NDX1',     currDim)
        ixn   = self.getParam('NDXN',     currDim)
        izf   = self.getParam('NDZF',     currDim) # Currently unused
        fSize = outSize

        # Check if FT has been performed on data, unlikely but plausible
        if (bool(self.getParam('NDFTFLAG'))):
            mid += (outSize - size)
            self.modifyParam('NDCENTER', mid, currDim)
        else:
            if (self.getParam('NDQUADFLAG', currDim) == 1):
                fSize = outSize/2
            else:
                fSize = outSize
            if (ix1 or ixn):
                # Currently unimplemented in the c code
                pass
            else:
                mid = fSize/2 + 1
                orig = obs*car - sw*(fSize - mid)/fSize
            
            self.modifyParam('NDZF',     float(-1*outSize), currDim)
            self.modifyParam('NDCENTER', float(mid),      currDim)
            self.modifyParam('NDX1',     float(ix1),      currDim)
            self.modifyParam('NDXN',     float(ixn),      currDim)
            self.modifyParam('NDORIG',    orig,           currDim)
    
        if (currDim == 3 or currDim == 4):
            self.modifyParam('NDSIZE', float(outSize), currDim)
        else:
            self.modifyParam('FDSIZE', float(outSize), currDim)

        # Update maximum size if size exceeds maximum size (NYI)
        """
        if (outSize > maxSize)
           {
            dataInfo->maxSize = dataInfo->outSize;
           }
        """


    """
    Delete Imaginary (DI)
    """
    def deleteImaginary(self):
        """
        fn deleteImaginary

        Remove imaginary element from data
            Then update the header to indicate performa
        """
        try:
            # Delete imaginary elements
            self.np_data = np.real(self.np_data)
            dimCount = int(self.getParam('FDDIMCOUNT'))
            # Remove imaginary elements in direct dimensions
            
            if (dimCount > 1):
                currDim = int(self.header.currDim)
                # Check if direct dimension and real or complex
                isReal = True # NYI
                if (isReal):
                    # Obtain direct dimensions and slice based on size
                    match dimCount:
                        case 2:
                            realIndex = int(len(self.np_data)/2)
                            self.np_data = self.np_data[:realIndex]

            # Update header properly based on deleting Imaginary values
            self.updateHeader(self.getTDSize, 'DI')
        except:
            pass

    def updateDI(self):
        pass