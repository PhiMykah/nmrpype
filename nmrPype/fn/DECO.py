from .function import DataFunction as Function
import numpy as np
import numpy.linalg as la
import os
from utils import catchError, DataFrame, FunctionError
from nmrio import writeToFile

class Decomposition(Function):
    """
    class Decomposition

    Data Function object for decomposing processed file into coefficients and synthetic
        data set
    """
    def __init__(self, deco_bases : list[str], deco_cfile : str, deco_error : 1e-8,
                 mp_enable : bool = False, mp_proc : int = 0,
                 mp_threads : int = 0):
        
        self.deco_bases = deco_bases
        self.deco_cfile = deco_cfile
        self.mp = [mp_enable, mp_proc, mp_threads]
        self.SIG_ERROR = deco_error

        params = {'deco_bases':deco_bases}
        super().__init__(params)

    ############
    # Function #
    ############

    def run(self, data) -> int:
        """
        fn run

        Main body of Deocomposition code
            - Checks for valid files
            - Compute least sum squares calculation
            - Output coefficients to designated file

        Parameters
        ----------
        data : DataFrame
            Target data to to run function on

        Returns
        -------
        Integer exit code (e.g. 0 success, non-zero fail)
        """
        try: 
            for file in self.deco_bases:
                if not Decomposition.isValidFile(file):
                    raise OSError("One or more files were not properly found!")
                
            if data.array.ndim >= 2:
                raise Exception("Dimensionality higher than 2 currently unsupported!")
            
            data.array = self.process(data.array)
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)

        return 0
            
        
    ##############
    # Processing #
    ##############

    def process(self, array) -> np.ndarray:
        """
        fn process

        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed

        Parameters
        ----------
        array : np.ndarray
            input array to compare to

        Returns
        -------
        np.ndarray
            modified array post-process
        """
        match array.ndim:
            case 1:
                return self.decomposition1D(array)
            case 2:
                return self.decomposition2D(array)
            case _:
                return array
            

    def decomposition1D(self, array) -> np.ndarray:
        """
        fn decomposition1D

        Perform a 1D Decomposition with provided basis set and target data

        Parameters
        ----------
        array : np.ndarray
            input array to compare to

        Returns
        -------
        np.ndarray
            modified array post-process
        """
        try:
            bases = []
            # Format matrix multiplication as A @ beta = b
            for basis in sorted(self.deco_bases):
                bases.append(DataFrame(basis).getArray())

            # A represents the len(array) x len(bases) array
            A = np.array(bases).T
            # b is the target len(array) x 1 vector to approximate
            b = array[:, np.newaxis]
            # beta is the coefficient vector of length len(bases) approximating result
            beta, residuals, rank, singular_values = la.lstsq(A,b, rcond=self.SIG_ERROR*np.max(A))
            # approx represents data approximation from beta and bases
            approx = A @ beta

            # Identify directory for saving file
            directory = os.path.split(self.deco_cfile)[0]

            # Make the missing directories if there are any
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Save the coefficients to the file given by user
            if self.generateCoeffFile(beta.T.real) != 0:
                raise CoeffWriteError

            # Only return complex data if data has complex elements
            if not np.all(approx.imag):
                return approx.real
            else:
                return approx

        except la.LinAlgError as e:
            catchError(e, new_e = Exception, 
                       msg="Computation does not converge! Cannot find coefficients!", 
                       ePrint = True)
            return array
        
        except CoeffWriteError as e:
            catchError(e, new_e = Exception, 
                       msg="Failed to create coefficient file, passing synthetic data", 
                       ePrint = True)
            return approx
        

    def decomposition2D(self, array) -> np.ndarray:
        """
        fn decomposition2D

        Perform a 2D Decomposition with provided basis set and target data

        Parameters
        ----------
        array : np.ndarray
            input array to compare to

        Returns
        -------
        np.ndarray
            modified array post-process
        """
        try:
            bases = []
            # Format matrix multiplication as A @ beta = b
            for basis in sorted(self.deco_bases):
                bases.append(DataFrame(basis).getArray())
            # Check if bases are 1D or 2D
            if bases[0].ndim != 1:
                return self.decomposition2D2D
            
            # A represents the len(array) x len(bases) array
            A = np.array(bases).T
            # b is the target number of data points x number of vectors to approximate
            b = array.T
            # beta is the coefficient vector of length len(bases) approximating result
            # Output rank if necessary
            beta, residuals, rank, singular_values = la.lstsq(A,b, rcond=self.SIG_ERROR*np.max(A))
            # approx represents data approximation from beta and bases
            approx = A @ beta

            # Identify directory for saving file
            directory = os.path.split(self.deco_cfile)[0]

            # Make the missing directories if there are any
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Save the coefficients to the file given by user
            if self.generateCoeffFile(beta.T) != 0:
                raise CoeffWriteError
            

        except la.LinAlgError as e:
            catchError(e, new_e = Exception, 
                       msg="Computation does not converge! Cannot find coefficients!", 
                       ePrint = True)
            return array
        

        except CoeffWriteError as e:
            catchError(e, new_e = Exception, 
                       msg="Failed to create coefficient file, passing synthetic data", 
                       ePrint = True)
            return approx


    def decomposition2D2D(self, array) -> np.ndarray:
        """
        fn decomposition2D2D

        Perform a 2D Decomposition with provided 2D basis set and target data

        Parameters
        ----------
        array : np.ndarray
            input array to compare to

        Returns
        -------
        np.ndarray
            modified array post-process
        """
        # Currently unimplemented
        return array


    def generateCoeffFile(self, beta : np.ndarray, fmt : str = 'nmr') -> int:
        """
        fn generateCoeffFile

        Creates a coefficient file from the least square sum operation

        Parameters
        ----------
        beta : np.ndarray
            coefficient 1D vector array (1 row)

        fmt : Literal['nmr','txt']

        Returns
        -------
        Integer exit code (e.g. 0 success, non-zero fail)
        """
        if fmt == 'txt':
            np.savetxt(self.deco_cfile, beta.T)
            return 0
        if fmt != 'nmr':
            return 1
        
        try:
            # Initialize header from template
            dic = HEADER_TEMPLATE

            # Since beta is vector, first dimension is used
            dim = 1 

            # NOTE: This code is almost identical to ccp4 header formation
            #   Consider extrapolating to general function
            size = float(beta.shape[-1*dim])

            # set NDSIZE, APOD, SW to SIZE
            # OBS is default 1
            # CAR is 0
            # ORIG is 0
            size_param = paramSyntax('NDSIZE', dim)
            apod_param = paramSyntax('NDAPOD', dim)
            sw_param = paramSyntax('NDSW', dim)
            ft_flag = paramSyntax('NDFTFLAG', dim)

            # Set parameters in the dictionary
            dic[size_param] = size
            dic[apod_param] = size
            if dim == 1:
                dic['FDREALSIZE'] = size
            dic[sw_param] = size

            # Consider the data in frequency domain, 1 for frequency
            dic[ft_flag] = 1

            coeffDF = DataFrame(header=dic, array=beta)

            writeToFile(coeffDF, self.deco_cfile, overwrite=True)

        except:
            return 2

        return 0
    
        
        
    ####################
    # Helper Functions #
    ####################
        
    @staticmethod
    def isValidFile(file) -> bool:
        """
        fn isValidFile

        Check whether or not the inputted file exists
        """

        fpath = os.path.abspath(file)
        if not os.path.isfile(fpath):
            return False
        
        return True


    ##################
    # Static Methods #
    ##################

    @staticmethod
    def clArgs(subparser):
        """
        fn clArgs (Template command-line arguments)

        Adds function parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # DECO subparser
        DECO = subparser.add_parser('DECO', help='Draw the current state of the data out to a file')
        DECO.add_argument('-basis', '-bases', type=str, nargs='+', metavar='BASIS FILES', required=True,
                          dest='deco_bases', help='List of basis files to use separated by spaces')
        DECO.add_argument('-cfile', type=str, metavar='COEFFICIENT OUTPUT', required=True,
                          dest='deco_cfile', help='Outpit file path for coefficients (WILL OVERWRITE FILE)')
        # Include universal commands proceeding function call
        Function.clArgsTail(DECO)

        ####################
        #  Proc Functions  #
        ####################
        def updateHeader(self, data):
            """
            fn updateHeader

            Update the header following the main function's calculations.
                Typically this includes header fields that relate to data size.

            Parameters
            ----------
            None
            """
            # Update ndsize here 
            pass

######################
#  Helper Functions  #
######################

def paramSyntax(param : str, dim : int) -> str :
    """
    fn paramSyntax

    local verison of updateHeaderSyntax found in DataFrame.py

    NOTE: This is identical to the function seen in ccp4, consider extrapolating

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
    if dim:
        # The try clause is omitted because we expect the paramter to exist
        # Since this function is not meant to be user-accessed
        dim = int(dim-1)
        if param.startswith('ND'):
            dimCode =  int(FDDIMORDER[dim])
            param = 'FDF' + str(dimCode) + param[2:]
    else:
        # If unspecified dimension for nd, then set dimension
        if param.startswith('ND'):
            dimCode =  int(FDDIMORDER[0])
            param = 'FDF' + str(dimCode) + param[2:]

    # Check if the param ends with size and fix to match sizes
    if param.endswith('SIZE'):
        match param:
            case 'FDF2SIZE':
                param = 'FDSIZE'
            case 'FDF1SIZE':
                param = 'FDSPECNUM'
    return param

#############
# Constants #
#############

class CoeffWriteError(Exception):
    pass

FDDIMORDER = [2,1,3,4]

# Originally I was going to load with json, but I am unsure which is better to itilize
# Snce this appears in both the deco and ccp4 files, json might be better
HEADER_TEMPLATE = {"FDMAGIC": 0.0,
"FDFLTFORMAT": 4008636160.0,
"FDFLTORDER": 2.3450000286102295,
"FDSIZE": 0.0,
"FDREALSIZE": 0.0,
"FDSPECNUM": 1.0,
"FDQUADFLAG": 1.0,
"FD2DPHASE": 3.0,
"FDTRANSPOSED": 0.0,
"FDDIMCOUNT": 1.0,
"FDDIMORDER": [2.0, 1.0, 3.0, 4.0],
"FDDIMORDER1": 2.0,
"FDDIMORDER2": 1.0,
"FDDIMORDER3": 3.0,
"FDDIMORDER4": 4.0,
"FDNUSDIM": 0.0,
"FDPIPEFLAG": 0.0,
"FDCUBEFLAG": 0.0,
"FDPIPECOUNT": 0.0,
"FDSLICECOUNT": 0.0,
"FDSLICECOUNT1": 0.0,
"FDFILECOUNT": 1.0,
"FDTHREADCOUNT": 0.0,
"FDTHREADID": 0.0,
"FDFIRSTPLANE": 0.0,
"FDLASTPLANE": 0.0,
"FDPARTITION": 0.0,
"FDPLANELOC": 0.0,
"FDMAX": 0.0,
"FDMIN": 0.0,
"FDSCALEFLAG": 1.0,
"FDDISPMAX": 0.0,
"FDDISPMIN": 0.0,
"FDPTHRESH": 0.0,
"FDNTHRESH": 0.0,
"FDUSER1": 0.0,
"FDUSER2": 0.0,
"FDUSER3": 0.0,
"FDUSER4": 0.0,
"FDUSER5": 0.0,
"FDUSER6": 0.0,
"FDLASTBLOCK": 0.0,
"FDCONTBLOCK": 0.0,
"FDBASEBLOCK": 0.0,
"FDPEAKBLOCK": 0.0,
"FDBMAPBLOCK": 0.0,
"FDHISTBLOCK": 0.0,
"FD1DBLOCK": 0.0,
"FDMONTH": 4.0,
"FDDAY": 27.0,
"FDYEAR": 2002.0,
"FDHOURS": 10.0,
"FDMINS": 23.0,
"FDSECS": 30.0,
"FDMCFLAG": 0.0,
"FDNOISE": 0.0,
"FDRANK": 0.0,
"FDTEMPERATURE": 0.0,
"FDPRESSURE": 0.0,
"FD2DVIRGIN": 1.0,
"FDTAU": 0.0,
"FDDOMINFO": 0.0,
"FDMETHINFO": 0.0,
"FDSCORE": 0.0,
"FDSCANS": 0.0,
"FDSRCNAME": "",
"FDUSERNAME": "",
"FDOPERNAME": "",
"FDTITLE": "",
"FDCOMMENT": "",
"FDF2LABEL": "X",
"FDF2APOD": 0.0,
"FDF2SW": 0.0,
"FDF2OBS": 1.0,
"FDF2OBSMID": 0.0,
"FDF2ORIG": 0.0,
"FDF2UNITS": 0.0,
"FDF2QUADFLAG": 1.0,
"FDF2FTFLAG": 0.0,
"FDF2AQSIGN": 0.0,
"FDF2CAR": 0.0,
"FDF2CENTER": 0.0,
"FDF2OFFPPM": 0.0,
"FDF2P0": 0.0,
"FDF2P1": 0.0,
"FDF2APODCODE": 0.0,
"FDF2APODQ1": 0.0,
"FDF2APODQ2": 0.0,
"FDF2APODQ3": 0.0,
"FDF2LB": 0.0,
"FDF2GB": 0.0,
"FDF2GOFF": 0.0,
"FDF2C1": 0.0,
"FDF2APODDF": 0.0,
"FDF2ZF": 0.0,
"FDF2X1": 0.0,
"FDF2XN": 0.0,
"FDF2FTSIZE": 0.0,
"FDF2TDSIZE": 0.0,
"FDDMXVAL": 0.0,
"FDDMXFLAG": 0.0,
"FDDELTATR": 0.0,
"FDF1LABEL": "Y",
"FDF1APOD": 0.0,
"FDF1SW": 0.0,
"FDF1OBS": 1.0,
"FDF1OBSMID": 0.0,
"FDF1ORIG": 0.0,
"FDF1UNITS": 0.0,
"FDF1FTFLAG": 0.0,
"FDF1AQSIGN": 0.0,
"FDF1QUADFLAG": 1.0,
"FDF1CAR": 0.0,
"FDF1CENTER": 1.0,
"FDF1OFFPPM": 0.0,
"FDF1P0": 0.0,
"FDF1P1": 0.0,
"FDF1APODCODE": 0.0,
"FDF1APODQ1": 0.0,
"FDF1APODQ2": 0.0,
"FDF1APODQ3": 0.0,
"FDF1LB": 0.0,
"FDF1GB": 0.0,
"FDF1GOFF": 0.0,
"FDF1C1": 0.0,
"FDF1ZF": 0.0,
"FDF1X1": 0.0,
"FDF1XN": 0.0,
"FDF1FTSIZE": 0.0,
"FDF1TDSIZE": 0.0,
"FDF3LABEL": "Z",
"FDF3APOD": 0.0,
"FDF3OBS": 1.0,
"FDF3OBSMID": 0.0,
"FDF3SW": 0.0,
"FDF3ORIG": 0.0,
"FDF3FTFLAG": 0.0,
"FDF3AQSIGN": 0.0,
"FDF3SIZE": 1.0,
"FDF3QUADFLAG": 1.0,
"FDF3UNITS": 0.0,
"FDF3P0": 0.0,
"FDF3P1": 0.0,
"FDF3CAR": 0.0,
"FDF3CENTER": 1.0,
"FDF3OFFPPM": 0.0,
"FDF3APODCODE": 0.0,
"FDF3APODQ1": 0.0,
"FDF3APODQ2": 0.0,
"FDF3APODQ3": 0.0,
"FDF3LB": 0.0,
"FDF3GB": 0.0,
"FDF3GOFF": 0.0,
"FDF3C1": 0.0,
"FDF3ZF": 0.0,
"FDF3X1": 0.0,
"FDF3XN": 0.0,
"FDF3FTSIZE": 0.0,
"FDF3TDSIZE": 0.0,
"FDF4LABEL": "A",
"FDF4APOD": 0.0,
"FDF4OBS": 1.0,
"FDF4OBSMID": 0.0,
"FDF4SW": 0.0,
"FDF4ORIG": 0.0,
"FDF4FTFLAG": 0.0,
"FDF4AQSIGN": 0.0,
"FDF4SIZE": 1.0,
"FDF4QUADFLAG": 1.0,
"FDF4UNITS": 0.0,
"FDF4P0": 0.0,
"FDF4P1": 0.0,
"FDF4CAR": 0.0,
"FDF4CENTER": 1.0,
"FDF4OFFPPM": 0.0,
"FDF4APODCODE": 0.0,
"FDF4APODQ1": 0.0,
"FDF4APODQ2": 0.0,
"FDF4APODQ3": 0.0,
"FDF4LB": 0.0,
"FDF4GB": 0.0,
"FDF4GOFF": 0.0,
"FDF4C1": 0.0,
"FDF4ZF": 0.0,
"FDF4X1": 0.0,
"FDF4XN": 0.0,
"FDF4FTSIZE": 0.0,
"FDF4TDSIZE": 0.0}