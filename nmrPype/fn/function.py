from ..utils import catchError, FunctionError, DataFrame
import numpy as np
from sys import stderr
from sys import stderr

# Multiprocessing
from multiprocessing import Pool, TimeoutError
from concurrent.futures import ThreadPoolExecutor

class DataFunction:
    """
    Data Function is a template class for all types of functions to run on
    the NMR data. New user functions should copy format laid out by this 
    class.

    Parameters
    ----------
    params : dict
        Dictionary of parameters associated with the designated function
    """
    def __init__(self, params : dict = {}):
        if not params:
            params = {'mp_enable':False,'mp_proc':0,'mp_threads':0}
            self.mp = [params['mp_enable'], params['mp_proc'], params['mp_threads']]
        self.params = params

    ############
    # Function #
    ############
        
    def run(self, data : DataFrame) -> int:
        """
        Main body of function code.
            - Initializes Header
            - Start Process (process data vector by vector in multiprocess)
            - Update Header
            - Return information if necessary

        Overload run for function specific operations

        Parameters
        ----------
        data : DataFrame
            Target data to to run function on

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        try:
            self.initialize(data)

            # Perform fft without multiprocessing
            if not self.mp[0] or data.array.ndim == 1:
                data.array = self.process(data.array, (data.verb, data.inc, data.getParam('NDLABEL')))
            else:
                data.array = self.parallelize(data.array)

            # Update header once processing is complete
            self.updateHeader(data)
            
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)

        return 0


    def parallelize(self, array : np.ndarray) -> np.ndarray:
        """
        The General Multiprocessing implementation for function, utilizing cores and threads. 
        Parallelize should be overloaded if array_shape changes in processing
        or process requires more args.

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        Returns
        -------
        new_array : ndarray
            Updated array after function operation
        """
        # Save array shape for reshaping later
        array_shape = array.shape

        # Split array into manageable chunks
        chunk_size = int(array_shape[0] / self.mp[1])

        # Assure chunk_size is nonzero
        chunk_size = array_shape[0] if chunk_size == 0 else chunk_size
        
        chunks = [array[i:i+chunk_size] for i in range(0, array_shape[0], chunk_size)]

        # Process each chunk in processing pool
        with Pool(processes=self.mp[1]) as pool:
            output = pool.map(self.process, chunks, chunksize=chunk_size)

        # Recombine and reshape data
        new_array = np.concatenate(output).reshape(array_shape)
        return new_array
    

    def process(self, array : np.ndarray, verb : tuple[int,int, str] = (0,16,'H')) -> np.ndarray:
        """
        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed

        Parameters
        ----------
        array : ndarray
            Target data array to process with function

        Returns
        -------
        ndarray
            Updated array after function operation
        """
        return array
    
    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser, parent_parser):
        """
        Command-line arguments template 

        clArgs adds function parser to the subparser, with its corresponding default args
        called by :py:func:`nmrPype.parse.parser`.
        The Destinations are formatted typically by {function}_{argument},
        e.g. the zf_pad destination stores the pad argument for the zf function.

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        pass


    @staticmethod
    def nullDeclare(subparser, parent_parser):
        """
        Null Function declaration

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive null function
        """
        NULL = subparser.add_parser('NULL', parents=[parent_parser], help='Null Function, does not apply any function')
        # DataFunction.clArgsTail(NULL)

    @staticmethod
    def verbPrint(func_name : str, index, size, step, verb : tuple[int,str] = (16,'H'), keepIndex : bool = False):
        """
        Print out progress through each array using verbosity

        Parameters
        ----------
        func_name : str
            Name of function to display on verbose print
        index : _type_
            Current array out of total arrays to print
        size : _type_
            Total array count to print
        step : _type_
            How many elements are in each array
        verb : tuple[int,int,str], optional
            Tuple containing elements for verbose print, by default (16,'H')
                - Verbosity Increment
                - Direct Dimension Label
        keepIndex : bool, optional
            Whether or not to divide index by step size, by default False
        """
        iter_index = index if keepIndex else int(np.floor(index / step) + 1)
        iter_size = int(size / step)
        digits = len(str(iter_size))
        loop_string = f"{{}}\t{{:0{digits}d}} of {{:0{digits}d}}\t{{}}"
        if (iter_index % verb[0] == 0) or (iter_index == 1) or (iter_index == iter_size):
            print(loop_string.format(func_name, iter_index, iter_size, verb[1]),end='\r',file=stderr)

    # @staticmethod
    # def clArgsTail(parser):
    #     """
    #     Tail-end command-line arguments

    #     Command-line arguments for the parser that are added to the end of each function.
        
    #     Note
    #     ----
    #     Do not overload!
        
    #     Parameters
    #     ----------
    #     parser : ArgumentParser
    #         Parser to add tail-end arguments to
    #     """
    #     from sys import stdout
    #     import os
    #     # Add parsers for multiprocessing
    
    #     parser.add_argument('-mpd', '--disable', action='store_false', dest='mp_enable2',
    #                                 help='Disable Multiprocessing')
    #     parser.add_argument('-proc', '--processors', nargs='?', metavar='', type=int, 
    #                             default=None, dest='mp_proc_alt',
    #                             help='Number of processors to use for multiprocessing')
    #     parser.add_argument('-t', '--threads', nargs='?', metavar='', type=int,
    #                             default=None, dest='mp_threads_alt',
    #                             help='Number of threads per process to use for multiprocessing')
        
    #     # Output settings
    #     parser.add_argument('-di', '--delete-imaginary', action='store_true', dest = 'di_alt',
    #                         help='Remove imaginary elements from dataset')
    #     parser.add_argument('-out', '--output', nargs='?', dest='output_alt', metavar='outName',
    #                         help='NMRPipe format output file name', default=None)
    #     parser.add_argument('-ov', '--overwrite', action='store_true', dest='overwrite_alt',
    #                         help='Call this argument to overwrite when sending output to file')

    ####################
    #  Proc Functions  #
    ####################
        
    def initialize(self, data : DataFrame):
        """
        Initialization follows the following steps:
            - Handle function specific arguments
            - Update any header values before any calculations occur
              that are independent of the data, such as flags and parameter storage


        Parameters
        ----------
        data : DataFrame
            Target data to manipulate 
        """
        pass

    def updateHeader(self, data : DataFrame):
        """
        Update the header following the main function's calculations.
        Typically this includes header fields that relate to data size.

        Parameters
        ----------
        data : DataFrame
            Target data frame containing header to update
        """
        # Update ndsize here 
        pass
