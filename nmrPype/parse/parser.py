from ..fn import __dict__ as fn_dict
from argparse import ArgumentParser
from argparse import Namespace
from sys import stdin,stdout, stderr
import os

def parser(input_args : list[str]) -> Namespace:
    """
    nmrPype's dedicated argument parser function.
    Takes arguments defined within functions as well to allow for
    easier integration of custom functions.

    Parameters
    ----------
    input_args : list[str]
        List of arguments from the command-line to parse

    Returns
    -------
    Namespace
        argparse Namespace object which has attributes and values
        properly handled to use in processing
    """
    parser = ArgumentParser(prog='nmrPype',description='Handle NMR Data inputted through file or pipeline \
                                    and perform desired operations for output',
                            usage='nmrPype -in inFile -fn fnName -out outFile -ov')
    parser.add_argument('-help', action='help', help='Use the -fn fnName switch for more')
    parser.add_argument('-in', '--input', nargs='?', metavar='inName', 
                        help='NMRPipe format input file name', default=stdin.buffer)
    parser.add_argument('-mod', '--modify', nargs=2, metavar=('Param', 'Value'))
    parser.add_argument('-fn','--function', dest='rf', action='store_true',
                        help='Read for inputted function')
    
    # Add subparsers for each function available
    subparser = parser.add_subparsers(title='Function Commands', dest='fc')

    # Gather list of functions
    fn_list = dict([(name, cls) for name, cls in fn_dict.items() if isinstance(cls, type)])

    for fn in fn_list.values():
        if hasattr(fn, 'clArgs'):
            fn.clArgs(subparser)
    
    fn_list['DataFunction'].nullDeclare(subparser)
    
    # Final arguments
    # Add parsers for multiprocessing
    
    parser.add_argument('-mpd', '--disable', action='store_false', dest='mp_enable',
                                help='Disable Multiprocessing')
    parser.add_argument('-proc', '--processors', nargs='?', metavar='#', type=int, 
                            default=os.cpu_count(), dest='mp_proc',
                            help='Number of processors to use for multiprocessing')
    parser.add_argument('-t', '--threads', nargs='?', metavar='#', type=int,
                            default=min(os.cpu_count(),4), dest='mp_threads', 
                            help='Number of threads per process to use for multiprocessing')
    
    # Add file output params
    parser.add_argument('-di', '--delete-imaginary', action='store_true', dest='di',
                        help='Remove imaginary elements from dataset')
    parser.add_argument('-out', '--output', nargs='?', metavar='outName',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout),
                        help='NMRPipe format output file name')
    parser.add_argument('-ov', '--overwrite', action='store_true', 
                        help='Call this argument to overwrite when sending output to file')

    return parser.parse_args(input_args)
