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
    def __init__(self, file : str = ""):
        self.header = {}
        self.array = None
        if (file): # Read only if file is provided
            pass # readFile


    def __repr__(self):
        return ""


    def getParam(self, param : str, dim : int = 0):
        pass 


    def setParam(self, param : str, value : float, dim : int = 0):
        pass

 
    def runFunc(self):
        pass


