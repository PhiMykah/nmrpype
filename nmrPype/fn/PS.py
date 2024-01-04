from .function import nmrFunction as Function

class PhaseCorrection(Function):
    def __init__(self, data, ps_p0: float = 0, ps_p1: float = 0,
                 ps_inv: bool = False, ps_hdr = False, ps_noup = False, ps_df = False, 
                 ps_ht: bool = False, ps_zf=False):
        
        # Variable declarations
        self.ps_p0 = ps_p0
        self.ps_p1 = ps_p1
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
        params = { 'ps_p0':ps_p0, 'ps_p1':ps_p1,
                  'ps_inv':ps_inv, 'ps_hdr':ps_hdr, 'ps_noup':ps_noup, 'ps_df':ps_df,
                  'ps_ht':ps_ht, 'ps_zf':ps_zf}
        super().__init__(data, params)
        self.initialize()

    @staticmethod
    def commands(subparser):    
        """
        fn commands

        Adds Fourier Transform parser to the subparser, with its corresponds
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument},
            e.g. the ps_p0 destination stores the p0 value for the ps function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        PS = subparser.add_parser('PS', help='Perform a Phase Correction (PS) on the data')
        PS.add_argument('-p0', type=float, metavar='p0Deg', default=0.0,
                        dest='ps_p0', help='Zero Order Phase, Degrees')
        PS.add_argument('-p1', type=float, metavar='p1Deg', default=0.0,
                        dest='ps_p1', help='First Order Phase, Degrees')
        PS.add_argument('-inv', action='store_true',
                        dest='ps_inv', help='Inverse Phase Correction')
        PS.add_argument('-hdr', action='store_true',
                        dest='ps_hdr', help='Use Phase Values in Header')
        PS.add_argument('-noup', action='store_true',
                        dest='ps_noup', help='Don\'t Update Values Header')
        PS.add_argument('-df', action='store_true',
                        dest='ps_df', help='Adjust P1 for Digital Oversampling')
        
        # Include universal commands proceeding function call
        Function.universalCommands(PS)

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
        p0 = 2.0*PI*self.ps_p0/360.0
        p1 = 2.0*PI*self.ps_p1/360.0

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
                lenX = arr.shape[0]
                set('FDSIZE', float(lenX))
            case 2:
                lenY, lenX = arr.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
            case 3:
                lenZ, lenY, lenX = arr.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
                set('FDF3SIZE', float(lenZ))
            case 4:
                lenA, lenZ, lenY, lenX = arr.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
                set('FDF3SIZE', float(lenZ))
                set('FDF4SIZE', float(lenA))
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')
        # Add values to header if noup is off
        if (not self.ps_noup):
            currDim = self.data.header.getcurrDim()
            setParam = self.data.modifyParam
            setParam('NDP0', float(self.ps_p0), currDim)
            setParam('NDP1', float(self.ps_p1), currDim)
    
    def phase1D(self, size): 
        from numpy import zeros
        from numpy import float32
        arr = self.data.np_data
        realVals = zeros(arr.shape, dtype=float32)
        imagVals = zeros(arr.shape, dtype=float32)
        for i in range(size):
            realVals[i] = arr.real[i] * self.arrReal[i] \
                        - arr.imag[i] * self.arrImag[i]
            
            imagVals[i] = arr.imag[i] * self.arrImag[i] \
                        + arr.imag[i] * self.arrReal[i]
        newArr = realVals + 1j*imagVals
        # Return array to nmr dataset, ensuring float32 datatype
        self.data.np_data = newArr
        
    
    def phase2D(self, xSize, ySize): 
        pass

    def phase3D(self, xSize, ySize, zSize): 
        pass

    def phase4D(self, xSize, ySize, zSize, aSize): 
        pass

    def updateFunctionHeader(self, size):
        pass
        
