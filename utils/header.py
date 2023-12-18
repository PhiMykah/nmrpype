class EmptyNMRData(Exception):
    # Exception called when trying to access or modify data 
    #   before a designated input stream existws
    pass

class UnsupportedDimension(Exception):
    # Exception called when trying to output data for an unsupported 
    #    array dimension
    pass

class UnknownHeaderParam(Exception):
    # Exception called when trying to access an unknown header parameter
    pass

class Header:
    axisLetters = {
        0: ["x","X"], "x": 0, "X" : 0,
        1: ["y","Y"], "y" : 1, "Z" : 1,
        2: ["z","Z"], "z" : 2, "Z" : 2,
        3: ["a","A"], "a" : 3, "A" : 3,
    }

    def __init__(self, hDict: dict = None, hStream : bytes = None):
        self.hDict = hDict
        self.hStream = hStream
        self.setCurrDim(1)

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
    
    def getAxisChar(self, code: int, isUpper: bool):
        return self.axisLetters[code][isUpper]
    
    def __repr__(self):
        output = ""
        for k,v in self.hDict.items():
                output += "({0} = {1})\n".format(k,v)
        return output

    def checkParamSyntax(self, param, dim : int):
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
        return param
