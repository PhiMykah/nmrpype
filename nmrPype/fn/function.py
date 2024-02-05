from utils import catchError, FunctionError, DataFrame
import numpy as np

class DataFunction:
    def __init__(self, params : dict = {}):
        """
        class dataFunction

        Data Function is a template class for all types of functions to run on
            the NMR data. New user functions should copy format laid out by this 
            class.

        Parameters
        ----------
        params : dict
            Dictionary of parameters associated with the designated function
        """
        self.params = params

    ############
    # Function #
    ############
        
    def run(self, data : DataFrame) -> int:
        """
        fn run

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
        Integer exit code (e.g. 0 success 1 fail)
        """
        return 0

    def process(self, array : np.ndarray) -> np.ndarray:
        """
        fn process

        Process is called by function's run, returns modified array when completed.
        Likely attached to multiprocessing for speed
        """
        return array
    
    ##################
    # Static Methods #
    ##################
        
    @staticmethod
    def clArgs(subparser):
        """
        fn commands (Template)

        Adds function parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        pass

    @staticmethod
    def clArgsTail(parser):
        """
        fn clArgsTail (tail-end command-line arguments)

        Command-line arguments for the parser that are added to the end of each function.
            Do not overload
        Parameters
        ----------

        Returns
        -------
        """
        from sys import stdout
        import os
        # Add parsers for multiprocessing
    
        parser.add_argument('-mpd', '--disable', action='store_false', dest='mp_enable',
                                    help='Disable Multiprocessing')
        parser.add_argument('-p', '--processors', nargs='?', metavar='Number of Processors', type=int, 
                                default=os.cpu_count(), dest='mp_proc')
        parser.add_argument('-t', '--threads', nargs='?', metavar='Number of Threads', type=int,
                                default=min(os.cpu_count(),4), dest='mp_threads')
        
        # Output settings
        parser.add_argument('-di', '--delete-imaginary', action='store_true', dest = 'di',
                            help='Remove imaginary elements from dataset')
        parser.add_argument('-out', '--output', nargs='?', dest='output',
                            default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
        parser.add_argument('-ov', '--overwrite', action='store_true', dest='overwrite',
                            help='Call this argument to overwrite when sending output to file.')

    ####################
    # Proc Functions #
    ####################
        
    def initialize(self, data):
        """
        fn initialize

        Initialization follows the following steps:
            -Handle function specific arguments
            -Update any header values before any calculations occur
                that are independent of the data, such as flags and parameter storage

        Parameters
        ----------
        data : DataFrame
            target data to manipulate 
        None
        """
        pass

    def updateHeader(self):
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
