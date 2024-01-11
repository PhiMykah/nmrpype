from . import UnknownHeaderParam

class Header:
    """
    class Header

    Stores header data from nmr format in an object for easier management

    Variables
    ----------
    hdict : dict
        Dictionary containing Header keys and values
    hStream: bytes
        Full header binary stream in python bytes format

    Methods
    ----------
    Python overloads
        __repr__()

    Getters and Setters
        setDict(dict), getDict()
        getCurrDim(), setCurrDim(dim)
        setParam(param, dim) getParam(param, dim)
    """
    def __init__(self, hDict: dict = None, hStream : bytes = None):
        self.hDict = hDict
        self.hStream = hStream
        if hDict:
            firstDim = int(hDict['FDDIMORDER1'])
            match firstDim:
                case 2:
                    self.setCurrDim(1)
                case 1:
                    self.setCurrDim(2)
                case _:
                    self.setCurrDim(firstDim)
        else:
            self.setCurrDim(1)

    def __repr__(self):
        # function __repr__ prints header in key value format
        output = ""
        for k,v in self.hDict.items():
                output += "({0} = {1})\n".format(k,v)
        return output
    
    #########################
    #  Getters and Setters  #
    #########################
    def setDict(self, dict):
        self.hDict = dict

    def getDict(self):
        return (self.hDict)
    
    def getcurrDim(self):
        return self.currDim

    def setCurrDim(self,dim):
        self.currDim = float(dim)
            
    def setParam(self, param: str, value, dim):
        param = self.checkParamSyntax(param,dim)
        if param in self.hDict.keys():
            self.hDict[param] = float(value)
            return True
        else:
            return False
    
    def getParam(self, param: str, dim : int = 0):
        dim = int(dim) # Make sure dimension is integer
        param = self.checkParamSyntax(param,dim)
        # Check if parameter exists and return
        if param in self.hDict.keys(): 
            return self.hDict[param]
        else:
            raise UnknownHeaderParam('Unknown Param \'{0}\''.format(param))

    def checkParamSyntax(self, param, dim : int):
        """
        fn checkParamSyntax

        Converts header keywords from ND to proper parameter syntax if necessary

        Parameters
        ----------
        dim : int
            Target dimension to convert syntax to
        """
        # Map the ND param to the fdfx param equivalent
        if dim:
            try: 
                dim = int(dim-1)
                if param.startswith('ND'):
                    dimCode =  int(self.hDict['FDDIMORDER'][dim])
                    param = 'FDF' + str(dimCode) + param[2:]
            except:
                raise UnknownHeaderParam('Unknown Param \'{0}\''.format(param))
        else:
            # If unspecified dimension for nd, then set dimension
            if param.startswith('ND'):
                dimCode =  int(self.hDict['FDDIMORDER'][0])
                param = 'FDF' + str(dimCode) + param[2:]

        # Check if the param ends with size and fix to match sizes
        if param.endswith('SIZE'):
            match param:
                case 'FDF2SIZE':
                    param = 'FDSIZE'
                case 'FDF1SIZE':
                    param = 'FDSPECNUM'
        return param
    
    """
    # unused #

    axisLetters = {
        0: ["x","X"], "x": 0, "X" : 0,
        1: ["y","Y"], "y" : 1, "Z" : 1,
        2: ["z","Z"], "z" : 2, "Z" : 2,
        3: ["a","A"], "a" : 3, "A" : 3,
    }

    def getAxisChar(self, code: int, isUpper: bool):
        return self.axisLetters[code][isUpper]

    """