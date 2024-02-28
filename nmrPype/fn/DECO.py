from .function import DataFunction as Function
import numpy as np
import numpy.linalg as la
import os
from utils import catchError, DataFrame, FunctionError

class Decomposition(Function):
    """
    class Decomposition

    Data Function object for decomposing processed file into coefficients and synthetic
        data set
    """
    def __init__(self, deco_bases : list[str], deco_file : str,
                 mp_enable : bool = False, mp_proc : int = 0,
                 mp_threads : int = 0):
        
        self.deco_bases = deco_bases
        self.deco_file = deco_file
        self.mp = [mp_enable, mp_proc, mp_threads]

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


        Returns
        -------

        """
        try: 
            for file in self.deco_bases:
                if not Decomposition.isValidFile(file):
                    raise OSError("One or more files were not properly found!")
                
            if data.array.ndim != 1:
                raise Exception("Dimensionality higher than 1 currently unsupported!")
            
            data.array = self.process(data.array)
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)
            
        
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
            beta = la.lstsq(A,b, rcond=None)[0]
            # approx represents data approximation from beta and bases
            approx = A @ beta

            # Identify directory for saving file
            directory = os.path.split(self.deco_file)[0]

            # Make the missing directories if there are any
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Save the coefficients to the file given by user
            np.savetxt(self.deco_file, beta.real)

            return approx

        except la.LinAlgError as e:
            catchError(e, new_e = Exception, 
                       msg="Computation does not converge! Cannot find coefficients!", 
                       ePrint = True)
            return array
        

    
        
        
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
        DECO.add_argument('-file', type=str, metavar='OUTPUT FILE', required=True,
                          dest='deco_file', help='Outpit file path for coefficients (WILL OVERWRITE FILE)')
        # Include universal commands proceeding function call
        Function.clArgsTail(DECO)


    ####################
    #  Proc Functions  #
    ####################