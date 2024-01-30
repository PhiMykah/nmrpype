import numpy as np 
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
        return self.header


    def setHeader(self, dic : dict) -> int:
        try:
            self.header = dic
        except:
            return 1
        return 0 
    

    def getArray(self) -> np.ndarray:
        return self.array
    

    def setArray(self, array : np.ndarray) -> int:
        try:
            self.array = array
        except:
            return 1
        return 0
    

    def getParam(self, param : str, dim : int = 0):
        pass 


    def setParam(self, param : str, value : float, dim : int = 0):
        pass

 
    def runFunc(self):
        pass


