import numpy as np
from .header import UnknownHeaderParam, UnsupportedDimension, EmptyNMRData

from nmrglue import pipe
import sys

class NMRData:
    """
    class NMRData

    Object containing the information about the NMR data as well as the data itself,
    with methods for accessing and modifying the data based on the header included with the data.

    Parameters
    ----------
    file : str
        Input file or stream to obtain the header and nmr data from
        
    Values
    ------
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
        """
        fn getTDSize

        Obtain the current expected time domain size of the current

        Returns
        -------
        size : int
            Time-domain size
        """

        # Extract sizes from the np array axes
        match int(self.getParam('FDDIMCOUNT')):
            case 1:
                lenX = self.np_data.shape[0]
            case 2:
                lenY, lenX = self.np_data.shape
            case 3:
                lenZ, lenY, lenX = self.np_data.shape
            case 4:
                lenA, lenZ, lenY, lenX = self.np_data.shape

        # Return the correct size based on the dimension
        match self.header.currDim:
            case 1:
                size = lenX
            case 2:
                size = lenY
            case 3:
                size = lenZ
            case 4:
                size = lenA
            case _:
                size = lenX
    
        return size
    
    def readFile(self, file):
        from . import Header
        """
        fn readFile

        set the header object and data array based on the input file

        Parameters
        ----------
        file
            Input file or stream to obtain the header and nmr data from
        """
        try:
            # Attempt to read file using nmr glue
            dic,data = pipe.read(file)
        except Exception as e:
            print(f"{e}: Unable to read file!", file=sys.stderr)
            sys.exit(0)
        try:
            # Attempt to store file as bytes
            # Check if data stream is binary data
            if hasattr(file, "read"):
                hStream = file.read(512)
            else:
                with open(file, 'rb') as f:
                    hStream = f.read(512)
        except Exception as e:
            print(f"{e}: Unable to read header stream!", file=sys.stderr)
            sys.exit(0)
        
        # Add dictionary and bytes to header and array to data
        self.header = Header(dic, hStream)
        self.np_data = data


    def writeOut(self, output, overwrite: bool):
        from . import Header
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
            # Mimic nmrglue's write to standard output buffer if output to datastream
            match self.np_data.ndim:
                case 1:
                    self.writeToBuffer(output, self.header.getDict(), self.np_data)
                case 2:
                    self.writeToBuffer(output, self.header.getDict(), self.np_data)
                case 3:
                    # Write each plane to buffer
                    lenZ, lenY, lenX = self.np_data.shape
                    for zi in range(lenZ):
                        plane = self.np_data[zi]
                        self.writeToBuffer(output, self.header.getDict(), plane)
                case 4:
                    ######################
                    # Currently untested #
                    ######################
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
            print(f"{e}: Unable to write to file!", file=sys.stderr)


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
                raise TypeError('data.dtype is not float32')
            if fdata.dtype != 'float32':
                raise TypeError('fdata.dtype is not float32')
            
            bufferStream.write(fdata.tobytes())
            bufferStream.write(data.tobytes())
            
        except Exception as e:
            print(f"{e}: An exception occured when attempting to write data to buffer!", sys.stderr)
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

    def runFunction(self, fn : str, arguments: dict = {}):
        from fn import Function
        from fn import FT, ZF, PS
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
            case 'ZF':
                function = ZF(self, **arguments)
            case 'PS':
                function = PS(self, **arguments)
            case _:
                function = Function(self, arguments)
        function.run()