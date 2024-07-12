from .function import DataFunction as Function
import numpy as np
import numpy.linalg as la
import os,sys
from pathlib import Path
from ..utils import catchError, DataFrame, FunctionError
from ..nmrio import writeToFile

# type Imports/Definitions
from typing import Literal

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class Decomposition(Function):
    """
    Data Function object for decomposing processed file into coefficients and synthetic
    data set
    
    Parameters
    ----------
    deco_bases : list[str]
        List of basis files in string format
    
    deco_cfile : str
        Output file path as string for coefficient data

    deco_mask : str
        Input mask to use for sample data 

    deco_error : float
        Significant error used to determine the rank by comparing vectors

    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
    """
    def __init__(self, deco_bases : list[str], deco_cfile : str = "coef.dat", 
                 deco_mask : str = "", deco_retain : bool = False, deco_error : float = 1e-8, 
                 mp_enable : bool = False, mp_proc : int = 0, mp_threads : int = 0):
        
        self.deco_bases = deco_bases
        self.deco_cfile = deco_cfile
        self.deco_mask = deco_mask
        self.deco_retain = deco_retain
        self.SIG_ERROR = deco_error
        self.mp = [mp_enable, mp_proc, mp_threads]
        self.name = "DECO"
        self.data_mode = 1

        params = {'deco_bases':deco_bases, 'deco_cfile':deco_cfile, 
                  'deco_mask':deco_mask, 'deco_retain':deco_retain, 'deco_error':deco_error}
        super().__init__(params)
    
    ############
    # Function #
    ############

    def run(self, data : DataFrame) -> int:
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
        int
            Integer exit code (e.g. 0 success, non-zero fail)
        """
        try:
            for file in self.deco_bases:
                if not Decomposition.isValidFile(file):
                    raise OSError("One or more basis files were not properly found")
            
            # Check if there is a mask to be used with the data
            if self.deco_mask:
                # Return error if mask file is unable to be found
                if not Decomposition.isValidFile(self.deco_mask):
                    print("Mask file was not properly found, ignoring", file=sys.stderr)
                    self.deco_mask = ""
                
                
            #if data.array.ndim > 2:
            #    raise Exception("Dimensionality higher than 2 currently unsupported!")
            

            #if data.array.ndim > 2:
            #    raise Exception("Dimensionality higher than 2 currently unsupported!")
            
            self.data_mode = data.getParam('NDQUADFLAG', data.getCurrDim())
            data.array = self.process(data.header, data.array, (data.verb, data.inc, data.getParam('NDLABEL')))
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)

        return 0


    ##############
    # Processing #
    ##############

    def process(self, dic : dict, array : np.ndarray, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        """
        fn process

        Perform a decomposition with a basis set and target data

        Parameters
        ----------
        dic : dict
            Copy of current data frame's header for coefficient output

        array : ndarray
            input array to compare to

        Returns
        -------
        ndarray
            modified array post-process
        """
        try:
            bases, basis_shape = self.collect_bases()

            if verb[0]:
                print("DECO Basis Size: {}".format(len(bases)), file=sys.stderr)

            array_shape = array.shape

            isAsymmetric = True if len(array_shape) > len(basis_shape) else False

            if isAsymmetric:
                if not self.mp[0] or array.ndim == 1:
                    synthetic_data, beta = self.asymmetricDecomposition(array, bases, verb)
                else:
                    synthetic_data, beta = self.parallelize(array, bases, verb)
            else:
                synthetic_data, beta = self.decomposition(array, bases, verb)
            
            if self.deco_cfile.lower() != "none":
                # Save the coefficients to the file given by user
                if self.generateCoeffFile(beta, array_shape, data_dic=dic, isAsymmetric=isAsymmetric,
                                        basis_dim=len(basis_shape), sample_dim=len(array_shape)) != 0:
                    raise CoeffWriteError
        
        

                

            return synthetic_data
            
            
        except la.LinAlgError as e:
            catchError(e, new_e = Exception, 
                       msg="Computation does not converge! Cannot find coefficients!", 
                       ePrint = True)
            return array
        
        except CoeffWriteError as e:
            catchError(e, new_e = Exception, 
                       msg="Failed to create coefficient file, passing synthetic data", 
                       ePrint = True)
            return synthetic_data

    def parallelize(self, array : np.ndarray, bases : list[str], verb : tuple[int,int,str] = (0,16,'H')) -> tuple[np.ndarray,np.ndarray]:
        """
        The General Multiprocessing implementation for function, utilizing cores and threads. 
        Parallelize should be overloaded if array_shape changes in processing
        or process requires more args.

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        bases : list[ndarray]
            List of basis vectors/matrices
        
        verb : tuple[int,int,str], optional
            Tuple containing elements for verbose print, by default (0, 16,'H')
                - Verbosity level
                - Verbosity Increment
                - Direct Dimension Label

        Returns
        -------
        (new_array, beta) : tuple[ndarray,ndarray]
            Approximation matrix and coefficient matrix
        """
        pass

    def decomposition(self, array : np.ndarray, 
                      bases : list[np.ndarray], verb : tuple[int,int,str] = (0,16,'H')) -> tuple[np.ndarray, np.ndarray]:
        """
        Use A and b to solve for the x that minimizes Ax-b = 0

        See :py:func:`asymmetricDecomposition` for the asymmetric implementation

        Parameters
        ----------
        array : ndarray
            Input array to calculate least squares
        bases : list[ndarray]
            List of bases

        verb : tuple[int,int,str], optional
            Tuple containing elements for verbose print, by default (0, 16,'H')
                - Verbosity level
                - Verbosity Increment
                - Direct Dimension Label
        Returns
        -------
        (approx, beta) : tuple[ndarray,ndarray]
            Approximation matrix and coefficient matrix
        """
        # Check if applying the mask is necessary
        # if self.deco_mask:
        #     mask = DataFrame(self.deco_mask).getArray()
        #     beta = _deco(array, np.array(bases), self.SIG_ERROR, True, mask)
        # else:
        #     beta = _deco(array, np.array(bases), self.SIG_ERROR)
        # A = np.reshape(np.array(bases), (len(bases), -1,)).T
        # approx = A @ beta
        
        if self.deco_mask:
            mask = DataFrame(self.deco_mask).getArray()
            beta_real = _deco(array.real, np.array(bases).real, self.SIG_ERROR, True, mask.real)
            beta_imag = _deco(array.imag, np.array(bases).imag, self.SIG_ERROR, True, mask.imag)
        else:
            beta_real = _deco(array.real, np.array(bases).real, self.SIG_ERROR)
            beta_imag = _deco(array.imag, np.array(bases).imag, self.SIG_ERROR)

        A = np.reshape(np.array(bases), (len(bases), -1)).T
        beta = beta_real + 1j*beta_imag

        approx_real = A.real @ beta_real
        approx_imag = A.imag @ beta_imag

        approx = approx_real + 1j*approx_imag

        if verb[0]:
            print("DECO Rank Condition: <={:.2e}".format(self.SIG_ERROR*np.max(A.real)), file=sys.stderr)

        # Check to see if original array should be retained
        if not self.deco_retain:
            return (approx.squeeze().reshape(array.shape), beta)
        
        if self.deco_mask:
            # Apply elements at mask
            gaps = np.invert(mask.astype(bool))
            array[gaps] = approx.squeeze().reshape(array.shape)[gaps]

        return (array, beta)


    
     
    
    def parallelDecomposition(self, array : np.ndarray, bases, mask : np.ndarray, verb : tuple[int,int,str] = (0,16,'H')) -> np.ndarray:
        pass

    def asymmetricDecomposition(self, array : np.ndarray,
                                bases : list[np.ndarray], verb : tuple[int,int,str] = (0,16,'H')) -> tuple[np.ndarray, np.ndarray]:
        """
        Perform a Decomposition with mismatch basis and data dimensions

        See :py:func:`decomposition` for the symmetric implementation

        Parameters
        ----------
        array : ndarray
            Input array to calculate least squares

        bases : list[ndarray]
            List of basis vectors/matrices
        
        verb : tuple[int,int,str], optional
            Tuple containing elements for verbose print, by default (0, 16,'H')
                - Verbosity level
                - Verbosity Increment
                - Direct Dimension Label
        Returns
        -------
        (approx, beta) : tuple[ndarray,ndarray]
            Approximation matrix and coefficient matrix
        """
        ########
        # NOTE #
        ########
        """
        Using the line `b = array.reshape(-1, A.shape[0],order='C').T` 
        instead of a separate asymmetric decomposition function may be faster, but 
        will take up more memory and requires more work to ensure that it works.
        
        Currently feasible in notebooks
        """
        A = np.reshape(np.array(bases), (len(bases), -1)).T
        if self.data_mode: 
            # Check if applying the mask is necessary
            if self.deco_mask:
                mask = DataFrame(self.deco_mask).getArray()
            else:
                mask = np.empty(array.shape)
            beta = self.deco_iter(array, np.array(bases), self.SIG_ERROR, mask, bool(self.deco_mask), verb)

            approx = A @ beta

            rank = self.SIG_ERROR*np.max(A.real)
        else:
            if self.deco_mask:
                mask = DataFrame(self.deco_mask).getArray()
                beta_real = self.deco_iter(array.real, np.array(bases).real, self.SIG_ERROR,
                                            mask.real, bool(self.deco_mask), verb, 'DECO-R')
                beta_imag = self.deco_iter(array.imag, np.array(bases).imag, self.SIG_ERROR,
                                            mask.imag, bool(self.deco_mask), verb, 'DECO-I')
            else:
                beta_real = self.deco_iter(array.real, np.array(bases).real, self.SIG_ERROR,
                                           verb=verb, msg='DECO-R')
                beta_imag = self.deco_iter(array.imag, np.array(bases).imag, self.SIG_ERROR,
                                           verb=verb, msg='DECO-I')

            approx_real = A.real @ beta_real
            approx_imag = A.imag @ beta_imag

            approx = approx_real + 1j*approx_imag
            beta = beta_real + 1j*beta_imag

            rank = self.SIG_ERROR*np.max(A.real)

        if verb[0]:
            print("DECO Rank Condition: <={:.2e}".format(rank), file=sys.stderr)

        # Check to see if original array should be retained
        if not self.deco_retain:
            return (approx.T.reshape(array.shape, order='C'), beta)
        
        if self.deco_mask:
            # Apply elements at mask
            gaps = np.invert(mask.astype(bool))
            array[gaps] = approx.T.reshape(array.shape, order='C')[gaps]

        return (array, beta)

            

    def generateCoeffFile(self, beta : np.ndarray, array_shape : tuple,
                          fmt : Literal['nmr','txt'] = 'nmr', data_dic : dict = {}, 
                          isAsymmetric : bool = False, 
                          basis_dim : int = 0, sample_dim : int = 0) -> int:
        """
        Creates a coefficient file from the least square sum operation

        Parameters
        ----------
        beta : np.ndarray
            coefficient vector array (1 row, 1+ col)

        fmt : Literal['nmr','txt']
            Output type for the coefficient data (NMR Data or text)

        data_dic : dict
            Dictionary used for the coefficient file header when outputting as NMR data

        isAsymmetric : bool 
            Both the sample data shape and the basis data shapes are not equal

        basis_dim : int
            Number of dimensions for each basis array

        sample_dim : int
            Number of dimensions for the sample array

        Returns
        -------
        int
            Integer exit code (e.g. 0 success, non-zero fail)
        """
        # Identify directory for saving file
        directory = os.path.split(self.deco_cfile)[0]

        # Make the missing directories if there are any
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        if fmt == 'txt':
            if beta.ndim >= 2:
                raise CoeffWriteError("Too many dimensions for text output! Dimensions: {}".format(beta.ndim))
            np.savetxt(self.deco_cfile, beta.T)
            return 0
        if fmt != 'nmr':
            return 1
        
        try:
            # Initialize header from template
            dic = HEADER_TEMPLATE
            if isAsymmetric:
                dic = {key: value for key, value in data_dic.items()}
                Decomposition.genCoeffHeader(dic, sample_dim, basis_dim)
            else:
                beta = beta.squeeze()

            beta = beta.T.reshape((array_shape[:-1*basis_dim] + (-1,)), order='C')

            dim = 1
                
            # NOTE: This code is almost identical to ccp4 header formation
            #   Consider extrapolating to general function
            size = float(beta.shape[-1*dim])

            # set NDSIZE, APOD, SW to SIZE
            # OBS is default 1
            # CAR is 0
            # ORIG is 0
            dim_count = paramSyntax('FDDIMCOUNT', dim)
            size_param = paramSyntax('NDSIZE', dim)
            apod_param = paramSyntax('NDAPOD', dim)
            sw_param = paramSyntax('NDSW', dim)
            ft_flag = paramSyntax('NDFTFLAG', dim)
            label = paramSyntax('NDLABEL', dim)
            quad_flag = paramSyntax('NDQUADFLAG', dim)

            # Set parameters in the dictionary
            dic[size_param] = size
            dic[apod_param] = size
            if dim == 1:
                dic['FDREALSIZE'] = size
            dic[sw_param] = size
            dic[label] = 'COEF'

            # Consider the data in frequency domain, 1 for frequency
            dic[ft_flag] = 1

            # Update dimcount
            dic[dim_count] = beta.ndim

            # Update data to be real
            dic[quad_flag] = 1
            
            coeffDF = DataFrame(header=dic, array=beta)

            writeToFile(coeffDF, self.deco_cfile, overwrite=True)
            
        except:
            return 2

        return 0


    
    ####################
    # Helper Functions #
    ####################

    def collect_bases(self) -> tuple[list[np.ndarray], tuple]:
        """Obtain bases from deco basis file list and collect the shape of each basis

        Returns
        -------
        tuple[list[np.ndarray], tuple]
            bases : list[np.ndarray]
                List of all basis sets
            basis_shape : tuple
                Shape of each basis set
        """
        bases = []
        basis_shape = None
        for basis in sorted(self.deco_bases):
            basis_array = DataFrame(basis).getArray()

            # Obtain shape only once
            if not basis_shape:
                basis_shape = basis_array.shape

            bases.append(basis_array)

        return (bases, basis_shape)

    def deco_iter(self, array : np.ndarray, A : np.ndarray, err : float, 
                   mask : np.ndarray | None = None, use_mask : bool = False, 
                   verb : tuple[int,int,str] = (0,0,'16'), msg : str = 'DECO') -> np.ndarray:
        """
        private decomposition function

        Parameters
        ----------
        array : np.ndarray
            Target array to decompose
        A : np.ndarray
            basis array for processing
        err : float
            Rounding error for rank determination
        mask : np.ndarray | None, optional
            Mask used for decomposition, by default None
        verb : tuple[int,int,str], optional
            Tuple containing elements for verbose print, by default (0, 16,'H')
                - Verbosity level
                - Verbosity Increment
                - Direct Dimension Label

        Returns
        -------
        beta : np.ndarray
            Beta array calculated by least squares
        """

        beta_planes = []

        # Collect number of basis dimensions (n) to form iterator
        n = len(A[0].shape)

        it = np.nditer(array[(Ellipsis,) + (0,) * n], flags=['multi_index'], order='C')
        while not it.finished:
            # Extract slice based on iteration
            slice_num = it.iterindex
            slice_array = array[it.multi_index + (slice(None),) * n]
            
            if verb[0]:
                    Function.verbPrint(msg, slice_num, it.itersize, 1, verb[1:])
            if use_mask:
                x = _deco(slice_array, A, err, use_mask, mask[it.multi_index + (slice(None),) * n])
            else:
                x = _deco(slice_array, A, err)

            # approx represents data approximation from beta and bases
            beta_planes.append(x)
            it.iternext()
        if verb[0]:
            print("", file=sys.stderr)

        return np.array(beta_planes).squeeze().T
    
    ##################
    # Static Methods #
    ##################

    @staticmethod
    def isValidFile(file : str) -> bool:
        """
        Check whether or not the inputted file exists

        Parameters
        ----------
        file : str
            String representation of target file

        Returns
        -------
        bool
            True or false value for whether the file exists
        """

        fpath = Path(file)
        if (file.count("%") == 1):
            if not Path(file % 1).is_file(): return False
            return True
        if (file.count("%") == 2):
            if not Path(file % 1).is_file(): return False
            return True
        
        if not fpath.is_file(): return False
        return True

    @staticmethod
    def genCoeffHeader(dic : dict, sample_dim : int, basis_dim : int):
        dim1 = 2
        dim2 = basis_dim+1
        dim_order = dic["FDDIMORDER"]

        # Don't update headers if dim1 and dim2 are equal
        if dim1 == dim2:
            return
        while dim2 < sample_dim:
            Decomposition.setNewDimVals(dic, "NDSIZE", dim1, dim2)
            
            # Half the data size if complex
            if dic[paramSyntax('NDQUADFLAG', dim2, dim_order)] == 0:
                dic[paramSyntax("NDSIZE", dim1, dim_order)] /= 2

            Decomposition.setNewDimVals(dic, "NDFTFLAG", dim1, dim2)

            Decomposition.setNewDimVals(dic, "NDAPOD", dim1, dim2)

            Decomposition.setNewDimVals(dic, "NDLABEL", dim1, dim2)

            i += 1
            dim += 1

    @staticmethod
    def setNewDimVals(dic : dict, flag : str, dim1 : int, dim2 : int):
        """Set the value at dim1 to the value at dim 2

        Parameters
        ----------
        dic : dict
            Target dictionary to update
        flag : str
            Target flag to update in dim1
        dim1 : int
            First dimension, the dimension to change
        dim2 : int
            Second dimension, the dimension to obtain the value from
        """
        dim_order = dic["FDDIMORDER"]
        key1 = paramSyntax(flag, dim1, dim_order)
        key2 = paramSyntax(flag, dim2, dim_order)

        dic[key1] = dic[key2]
    
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Decomposition command-line arguments

        Adds function parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # DECO subparser
        DECO = subparser.add_parser('DECO', parents=[parent_parser], help='Create synthetic decomposition with basis set and original data.')
        DECO.add_argument('-basis', '-bases', type=str, nargs='+', metavar='BASIS FILES', required=True,
                          dest='deco_bases', help='List of basis files to use separated by spaces')
        DECO.add_argument('-cfile', type=str, metavar='COEFFICIENT OUTPUT', default='coef.dat',
                          dest='deco_cfile', help='Output file path for coefficients (WILL OVERWRITE FILE)')
        DECO.add_argument('-mask', type=str, metavar='MASK FILE INPUT', default="", 
                          dest='deco_mask', help='Specify input mask file to multiply with data')
        DECO.add_argument('-retain', action='store_true',
                          dest='deco_retain', help='Retain source data whilst adding synthetic data to gaps.')
        DECO.add_argument('-err', type=float, metavar='SIG ERROR', default=1e-8,
                          dest='deco_error', help='Rank Calculation Significant Error (Determining Dependence)')
        # Include universal commands proceeding function call
        # Function.clArgsTail(DECO)

####################
# Helper Functions #
####################

def _deco(array : np.ndarray, A : np.ndarray, err : float, use_mask : bool = False, mask : np.ndarray | None = None) -> np.ndarray:
    """
    private decomposition function

    Parameters
    ----------
    array : np.ndarray
        Target array to decompose
    A : np.ndarray
        basis array for processing
    err : float
        Rounding error for rank determination
    use_mask : bool, optional
            Whether to use mask or not, by default False
    mask : np.ndarray | None, optional
        Mask used for decomposition, by default None

    Returns
    -------
    beta : np.ndarray
        Beta array calculated by least squares
    """
    max_val = max(np.max(np.abs(A.real)), np.max(np.abs(A.imag)))

    rcond = err*max_val

    if use_mask:
        A = (A * mask)
    
    if not np.any(A):
        return np.zeros((len(A), 1), dtype='float32', order='C')
    
    # A represents the (data length, number of bases) array
    A = np.reshape(A, (A.shape[0], -1,), order='C').T
    # b is the vector to approximate
    b = array.flatten(order='C')[:, np.newaxis]
    
    # beta is the coefficient vector multiplied by the A to approximate the result
    # Output rank if necessary
    beta, residuals, rank, singular_values = la.lstsq(A,b, 
                                                        rcond=rcond)

    return beta

def paramSyntax(param : str, dim : int, dim_order : dict = [2,1,3,4]) -> str:
    """
    Local verison of updateHeaderSyntax defined by
    :py:func:`nmrPype.utils.DataFrame.DataFrame.updateParamSyntax`

    NOTE
    ---- 
    This is nearly identical to :py:func:`nmrPype.nmrio.ccp4.ccp4.paramSyntax`,
    may be extrapolated in the future

    Parameters
    ----------
    param : str
        Starter parameter string before modification

    dim : int
        Target parameter dimension

    dim_order : dict
        Order of ints to use to obtain the dim code integer

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
            dimCode =  int(dim_order[dim])
            param = 'FDF' + str(dimCode) + param[2:]
    else:
        # If unspecified dimension for nd, then set dimension
        if param.startswith('ND'):
            dimCode =  int(dim_order[0])
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
    """
    Exception called when unable to write coefficients to a file
    """
    pass

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