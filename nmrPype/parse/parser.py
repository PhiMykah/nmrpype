from ..fn import __dict__ as fn_dict
from argparse import ArgumentParser
from argparse import Namespace
from sys import stdin,stdout, stderr
import os

class Container(Namespace):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
    # Common Operations 
    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument('-in', '--input', nargs='?', metavar='inName', 
                        help='NMRPipe format input file name', default=stdin.buffer)
    parent_parser.add_argument('-mod', '--modify', nargs=2, metavar=('Param', 'Value'))
    parent_parser.add_argument('-fn','--function', dest='rf', action='store_true',
                        help='Read for inputted function')
    parent_parser.add_argument('-help', action='help', help='Use the -fn fnName switch for more')
    parent_parser.add_argument('-verb', '--verbose', metavar='[0]', type=int, const=1, default=0, nargs='?', dest='verb',
                        help='Debug verbose level')
    parent_parser.add_argument('-inc','--increment', metavar='[16]', type=int, default=16, dest='inc',
                        help='Verbose loop print increment')
    # Add parsers for multiprocessing
    parent_parser.add_argument('-mpd', '--disable', action='store_false', dest='mp_enable',
                                help='Disable Multiprocessing')
    parent_parser.add_argument('-proc', '--processors', nargs='?', metavar='#', type=int, 
                            default=os.cpu_count(), dest='mp_proc',
                            help='Number of processors to use for multiprocessing')
    parent_parser.add_argument('-t', '--threads', nargs='?', metavar='#', type=int,
                            default=min(os.cpu_count(),4), dest='mp_threads', 
                            help='Number of threads per process to use for multiprocessing')
    
    # Add file output params
    parent_parser.add_argument('-di', '--delete-imaginary', action='store_true', dest='di',
                        help='Remove imaginary elements from dataset')
    parent_parser.add_argument('-out', '--output', nargs='?', metavar='outName',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout),
                        help='NMRPipe format output file name')
    parent_parser.add_argument('-ov', '--overwrite', action='store_true', 
                        help='Call this argument to overwrite when sending output to file')

    parser = ArgumentParser(prog='nmrPype', parents=[parent_parser], description='Handle NMR Data inputted through file or pipeline \
                                and perform desired operations for output',
                        usage='nmrPype -in inFile -fn fnName') # -out outFile -ov
    
    # Add subparsers for each function available
    subparser = parser.add_subparsers(title='Function Commands', dest='fc')

    # Gather list of functions
    fn_list = dict([(name, cls) for name, cls in fn_dict.items() if isinstance(cls, type)])

    for fn in fn_list.values():
        if hasattr(fn, 'clArgs'):
            fn.clArgs(subparser, parent_parser)
    
    fn_list['DataFunction'].nullDeclare(subparser, parent_parser)
    
    empty_container = Container()
    initial_container = Container()
    container = Container()

    input_args = " ".join(input_args).split(" -fn ")

    general_args = input_args[0].split(" ")

    parser.parse_known_args(args=[], namespace=empty_container)
    _, unknown = parser.parse_known_args(args=general_args, namespace=initial_container)

    if len(input_args) == 1:
        return initial_container
    if len(input_args) == 2:
        fn_args = " ".join(["-fn",*input_args[1].split(" ")]).split(" ")
        _, fn_unknown = parser.parse_known_args(args=fn_args, namespace=container)

    if unknown or fn_unknown:
        print("WARNING! Unknown Arguments:", *unknown, *fn_unknown, file=stderr)

    for attribute in vars(empty_container):
        # Check if the attribute has been changed from default in the initial container
        if ((getattr(container,attribute) != getattr(initial_container,attribute)) and
            (getattr(container,attribute) == getattr(empty_container,attribute))):
            setattr(container,attribute, getattr(initial_container,attribute))

    return container
