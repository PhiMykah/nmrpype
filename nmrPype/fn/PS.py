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

        # Initialize array for later
        self.phase = None

        # Parameter storing for development purposes
        params = { 'ps_p0':ps_p0, 'ps_p1':ps_p1,
                  'ps_inv':ps_inv, 'ps_hdr':ps_hdr, 'ps_noup':ps_noup, 'ps_df':ps_df,
                  'ps_ht':ps_ht, 'ps_zf':ps_zf}
        super().__init__(params)
        self.initialize(data)

    @staticmethod
    def commands(subparser):    
        """
        fn commands

        Adds Phase Correction parser to the subparser, with its corresponding args
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

    def initialize(self, data):
        from numpy import pi as PI
        from numpy import cos, sin, radians, array
        """
        fn initialize
            
        Pre-allocate and initialize arrays for simpler computing
        """
        # Obtain size for phase correction from data
        size = data.getTDSize()

        # Convert from 
        # C code uses 3.14159265
        p0 = radians(self.ps_p0)
        p1 = radians(self.ps_p1)

        realList = []
        imagList = []
        for x in range(size):
            realVal = cos(p0 + (p1*x)/size) # Ensure radians output is sufficient
            imagVal = sin(p0 + (p1*x)/size)
            realList.append(float(realVal))
            imagList.append(float(imagVal))

        imag = array(imagList)
        self.phase = array(realVal + 1j * imag)

    def func(self, array):
        """
        fn func

        Performs a phase shift operation on 1-D array
        
        Header updating operations are performed outside scope

        Parameters
        ----------
        array : ndarray (1-D)
            Array to perform operation on, passed from run
        Returns
        -------
        array : ndarray
            Modified 1-D array after operation
        """
        return (self.phase * array)


    def updateFunctionHeader(self, data, sizes):
        # Add values to header if noup is off
        if (not self.ps_noup):
            currDim = data.header.getcurrDim()
            setParam = data.modifyParam
            setParam('NDP0', float(self.ps_p0), currDim)
            setParam('NDP1', float(self.ps_p1), currDim)
        
