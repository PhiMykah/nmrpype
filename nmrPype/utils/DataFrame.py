import numpy as np 
from .errorHandler import *
import sys
from typing import TypeAlias

# Type declarations
Array : TypeAlias = np.ndarray | None

class DataFrame:
    """
    Object containing the nmr data vectors as well as the header.
    Contains methods for accessing and modifying the data based
    on the header included with the data.

    Parameters
    ----------
    file : str
        Input file or stream for initializing frame
    header : dict
        Header to initialize, by default obtained from file or set
    array : Array [numpy.ndarray or None]
        Array to initialize, by default obtained from file or set
    """
    def __init__(self, file : str = "", header : dict = {}, array : Array = None, verb : int = 0, inc : int = 16):
        if (file): # Read only if file is provided
            from ..nmrio import readFromFile

            # Initialize header and array based on file
            dic, data = readFromFile(file)

            self.header = dic
            self.array = data
            self.file = file
            self.verb = verb
            self.inc = inc
        else:
            # Initialize header and array based on args
            self.header = header
            self.array = array
            self.file = file
            self.verb = verb
            self.inc = inc


    def __repr__(self):
        """
        Printable string describe the DataFrame
        """
        if type(self.array) == None or not self.header or not self.file:
            return "Empty NMR DataFrame"
        
        file = self.file
        dim = self.array.ndim
        size = self.array.size
        order = " ".join([str(int(s)) for s in self.header['FDDIMORDER']])
        shape = " ".join([str(s) for s in reversed(self.array.shape)])
        quad = "Complex" if np.any(np.iscomplex(self.array)) else "Real"
        t = "True" if self.header['FDTRANSPOSED'] else 'False'
        hdr = "\n".join(["{}: {}".format(k,v) for k, v in self.header.items()])
        data = str(self.array)
        return \
        f"NMR DataFrame @ {file}\
        \nDIM: {dim}\tSIZE: {size}\tORDER: {order}\tSHAPE: {shape}\
        \nQUAD: {quad} TRANSPOSED: {t}\n"
            

    def __str__(self) -> str:
        """
        String describing the DataFrame, with file and shape

        Returns
        -------
        str
            Returns string description
        """
        return f"NMR DataFrame @ {self.file} ({" ".join([str(s) for s in reversed(self.array.shape)])})"
    
    def runFunc(self, targetFunction : str, arguments : dict = {}) -> int:
        """
        runFunc completes the following:

        1. Checks for valid function call
        2. Passes function arguments to function call
        3. Uses function call to process array based on function implementation
        4. Update the data's header accordingly

        Can be called outside of command-line mode if arguments are passed with proper keys

        Parameters
        ----------
        targetFunction : str
            Function Code (e.g. FT, SP, ZF)
        arguments: dict
            Dictionary of arguments to pass to function initialization
            (May become a kwargs in the future for user simplicity)

        Returns
        -------
        int
            Integer exit code obtained by the function itself (e.g. 0 success 1 fail)
        """
        from ..fn import fn_list
        if targetFunction == 'NULL':
            return 0
        
        try:
            function = fn_list[targetFunction](**arguments)
        except Exception as e:
            catchError(e, FunctionError, msg='Unknown or Unimplemented function called!', ePrint=False)

        return(function.run(self))


    def updateParamSyntax(self, param : str, dim : int) -> str :
        """
        Converts header keywords from ND to proper parameter syntax if necessary

        Parameters
        ----------
        param : str
            Starter parameter string before modification

        dim : int
            Target parameter dimension

        Returns
        -------
        param : str
            Parameter string with updated syntax
        """
        # Map the ND param to the fdfx param equivalent
        if dim:
            try: 
                dim = int(dim-1)
                if param.startswith('ND'):
                    dimCode =  int(self.header['FDDIMORDER'][dim])
                    param = 'FDF' + str(dimCode) + param[2:]
            except:
                raise UnknownHeaderParam('Unknown Param \'{0}\''.format(param))
        else:
            # If unspecified dimension for nd, then set dimension
            if param.startswith('ND'):
                dimCode =  int(self.header['FDDIMORDER'][0])
                param = 'FDF' + str(dimCode) + param[2:]

        # Check if the param ends with size and fix to match sizes
        if param.endswith('SIZE'):
            match param:
                case 'FDF2SIZE':
                    param = 'FDSIZE'
                case 'FDF1SIZE':
                    param = 'FDSPECNUM'
        return param
    

    def updatePipeCount(self, reset : bool = False) -> int:
        """
        Increment the FDPIPECOUNT parameter or reset to zero

        Parameters
        ----------
        reset : bool
            Whether or not to reset pipe count or increment pipe count

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        try:
            if reset:
                self.setParam('FDPIPECOUNT', 0.0)
            else:
                pCount = self.getParam('FDPIPECOUNT')
                self.setParam('FDPIPECOUNT', float(pCount + 1))
        except:
            return 1
        return 0


    #######################
    # Getters and Setters #
    #######################
    
    def getHeader(self) -> dict:
        """
        Dataframe header variable getter

        Returns
        -------
        self.header : dict
            Object's current header
        """
        return self.header

    def setHeader(self, dic : dict) -> int:
        """
        Dataframe header variable setter

        Parameters
        ----------
        dic : dict
            New header to assign to data frame

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """

        try:
            self.header = dic
        except:
            return 1
        return 0 
    

    def getArray(self) -> Array:
        """
        Dataframe array variable getter

        Returns
        -------
        self.array : Array
            Object's current ndarray
        """
        return self.array
    

    def setArray(self, array : Array) -> int:
        """
        Dataframe array variable setter

        Parameters
        ----------
        array : Array
            New array to assign to data frame

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        try:
            self.array = array
        except:
            return 1
        return 0
    

    def getParam(self, param : str, dim : int = 0) -> float:
        """
        Obtain header parameter from dictionary given key and dimension

        Parameters
        ----------
        param : str
            Header parameter to obtain value from
        dim : int
            Dimension of parameter

        Returns
        -------
        float
            Float value of header parameter
        """
        targetParam = self.updateParamSyntax(param, dim)
        try:
            return(self.header[targetParam])
        except:
            raise UnknownHeaderParam('Unknown Param \'{0}\''.format(targetParam))


    def setParam(self, param : str, value : float, dim : int = 0) -> int:
        """
        Set given header parameter's value to inputted value

        Parameters
        ----------
        param : str
            Header parameter to set value to
        value : float
            Value to replace header value with
        dim : int
            Dimension of parameter

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        targetParam = self.updateParamSyntax(param, dim)
        try:
            self.header[targetParam] = value
        except:
            return 1
        return 0
    
    def getCurrDim(self) -> int:
        """
        Obtain current dim for Dataframe based on dim order

        Returns
        -------
        int
            Current direct dimension
        """
        return 0 # Bandaid fix self.getDimOrder(1)
        
    def getDimOrder(self, dim : int) -> int:
        """
        Convert order number into correct dimension index
        


        Parameters
        ----------
        dim : int
            Dimension Index

            * 1 = Direct
            * 2 = First Indirect
            * 3 = Second Indirect
            * 4 = Third Indirect
            * and so on..

        Returns
        -------
        int
            Integer corresponding to the inputted dimension
            specifically for this dataset
        """
        if int(self.header['FDDIMORDER'][dim-1]) == 2:
            return 1
        elif int(self.header['FDDIMORDER'][dim-1]) == 1:
            return 2
        else:
            return int(self.header['FDDIMORDER'][dim-1])

    def getVerb(self) -> int:
        """
        Obtain verbosity value

        Returns
        -------
        int
            Integer corresponding to verbosity value
        """ 
        return self.verb
    
    def setVerb(self, level : int):
        """
        Set verbosity value

        Parameters
        ----------
        level : int
            Integer for new verbosity value
        """
        self.verb = level

    def getInc(self) -> int:
        """
        Obtain verbose increment vlue

        Returns
        -------
        int
            Integer corresponding to verbose output loop increment
        """
        return self.inc

    def setInc(self, level : int):
        """
        Set verbosity increment

        Parameters
        ----------
        level : int
            Integer for verbose output loop increment
        """
        self.inc = level