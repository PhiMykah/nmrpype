from .function import nmrFunction as Function

class FourierTransform(Function):
    def __init__(self, **params):
        self.ft_inv = params['ft_inv'] 
        self.ft_real = params['ft_real']
        self.ft_neg = params['ft_neg']
        self.ft_alt = params['ft_alt']
        super().__init__(self) 

    def updateFunctionHeader(self, nmrData, size):
        currDim = nmrData.header.getcurrDim()
        # Flip FT flag
        if (bool(nmrData.getParam('NDFTFLAG'))):
            nmrData.modifyParam('NDFTFLAG', float(0), currDim) 
        else:
            nmrData.modifyParam('NDFTFLAG', float(1), currDim) 

        # Set NDAQSIGN and NDFTSIZE
        if (bool(nmrData.getParam('NDFTFLAG'))):
            nmrData.modifyParam('NDAQSIGN', float(0), currDim)
            nmrData.modifyParam('NDFTSIZE', nmrData.getTDSize(), currDim)
        else:
            # Implement `dataInfo->outQuadState = 2`
            nmrData.modifyParam('NDFTSIZE', nmrData.getTDSize(), currDim) 

        # Add flag for complex
        nmrData.modifyParam('FDQUADFLAG', float(0))
        nmrData.modifyParam('NDQUADFLAG', float(0), currDim)  
        
        # Check for real flag, and update based on real (divide the size by 2)
        size = size/2 if self.ft_real else size
        nmrData.modifyParam('NDAPOD', float(size), currDim)  