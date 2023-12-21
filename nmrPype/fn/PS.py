from .function import nmrFunction as Function

class PhaseCorrection(Function):
    def __init__(self, data, ps_degP0: float = 0, ps_degP1: float = 0,
                 ps_inv: bool = False, ps_hdr = False, ps_noup = False, ps_df = False, 
                 ps_ht: bool = False, ps_zf=False):
        
        # Variable declarations
        self.ps_degP0 = ps_degP0
        self.ps_degP1 = ps_degP1
        self.ps_inv = ps_inv     
        self.ps_hdr = ps_hdr
        self.ps_noup = ps_noup   
        self.ps_df = ps_df
        self.ps_ht = ps_ht
        self.ps_zf = ps_zf

        # Initialize arrays for later
        self.arrReal = []
        self.arrImag = []

        # Parameter storing for development purposes
        params = { 'ps_degP0':ps_degP0, 'ps_degP1':ps_degP1,
                  'ps_inv':ps_inv, 'ps_hdr':ps_hdr, 'ps_noup':ps_noup, 'ps_df':ps_df,
                  'ps_ht':ps_ht, 'ps_zf':ps_zf}
        super().__init__(data, params)
        self.initialize()

    def initialize(self):
        from math import pi as PI
        from math import cos, sin
        """
        fn initialize
            
        Pre-allocate and initialize arrays for simpler computing
        """
        # Obtain size for phase correction from data
        size = self.data.getTDSize()

        # C code uses 3.14159265
        p0 = 2.0*PI*self.ps_degP0/360.0
        p1 = 2.0*PI*self.ps_degP1/360.0

        for x in range(size):
            realVal = cos(p0 + (p1*x)/size) # Ensure radians output is sufficient
            imagVal = sin(p0 + (p1*x)/size)
            self.arrReal.append(float(realVal))
            self.arrImag.append(float(imagVal))

    def run(self):
        from utils import UnsupportedDimension
        arr = self.data.np_data
        match int(self.data.getParam('FDDIMCOUNT')): 
            case 1:
                xSize = len(arr)
                self.phase1D(xSize)
            case 2:
                xSize = len(arr[0])
                ySize = len(arr)
                self.phase2D(xSize, ySize)
            case 3:
                xSize = len(arr[0][0])
                ySize = len(arr[0])
                zSize = len(arr)
                self.phase3D(xSize, ySize, zSize)
            case 4:
                xSize = len(arr[0][0][0])
                ySize = len(arr[0][0])
                zSize = len(arr[0])
                aSize = len(arr)
                self.phase4D(xSize, ySize, zSize, aSize)
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')
    
    def phase1D(self, size): 
        from numpy import zeros
        arr = self.data.np_data
        realVals = zeros(arr.shape)
        imagVals = zeros(arr.shape)
        for i in range(size):
            realVals[i] = arr.real[i] * self.arrReal[i] \
                        - arr.imag[i] * self.arrImag[i]
            
            imagVals[i] = arr.imag[i] * self.arrImag[i] \
                        + arr.imag[i] * self.arrReal[i]
        arr = realVals + 1j*imagVals
    
    def phase1D(self, xSize, ySize): 
        pass

    def phase3D(self, xSize, ySize, zSize): 
        pass

    def phase4D(self, xSize, ySize, zSize, aSize): 
        pass

    def updateFunctionHeader(self, size):
        pass
        
