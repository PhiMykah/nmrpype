import numpy as np 
from .errorHandler import *
import sys

class DataFrame:
    """
    class DataFrame

    Object containing the nmr data vectors as well as the header.
    Contains methods for accessing and modifying the data based
        on the header included with the data.

    Parameters
    ----------
    file : str
        Input file or stream for initializing frame
    header : dict
        Header to initialize, by default obtained from file or set
    array : ndarray or None
        Array to initialize, by default obtained from file or set
    """
    def __init__(self, file : str = "", header : dict = {}, array = None):
        if (file): # Read only if file is provided
            from nmrio import readFromFile

            # Initialize header and array based on file
            dic, data = readFromFile(file)

            self.header = dic
            self.array = data
        else:
            # Initialize header and array based on args
            self.header = header
            self.array = array


    def __repr__(self):
        return ""

    def getHeader(self) -> dict:
        """
        fn setArray

        array variable getter for object

        Returns
        -------
        self.header : dict
            Object's current header
        """
        return self.header


    def setHeader(self, dic : dict) -> int:
        try:
            self.header = dic
        except:
            return 1
        return 0 
    

    def getArray(self) -> np.ndarray:
        """
        fn setArray

        array variable getter for object

        Returns
        -------
        self.array : np.ndarray
            Object's current ndarray
        """
        return self.array
    

    def setArray(self, array : np.ndarray) -> int:
        """
        fn setArray

        array variable setter for object

        Parameters
        ----------
        array : np.ndarray
            New ndarray to set to object

        Returns
        -------
        Integer exit code (e.g. 0 success 1 fail)
        """
        try:
            self.array = array
        except:
            return 1
        return 0
    

    def getParam(self, param : str, dim : int = 0) -> float:
        """
        fn getParam

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
        fn setParam

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
        Integer exit code (e.g. 0 success 1 fail)
        """
        targetParam = self.updateParamSyntax(param, dim)
        try:
            self.header[targetParam] = value
        except:
            return 1
        return 0

 
    def runFunc(self):
        pass


    def updateParamSyntax(self, param, dim : int) -> str :
        """
        fn updateParamSyntax

        Converts header keywords from ND to proper parameter syntax if necessary

        Parameters
        ----------
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