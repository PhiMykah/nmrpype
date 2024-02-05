def parser(input_args : list):
    import fn
    from argparse import ArgumentParser
    from sys import stdin,stdout, stderr
    import os
    parser = ArgumentParser(prog='nmrPype',description='Handle NMR Data inputted through file or pipeline \
                                    and perform desired operations for output.')
    parser.add_argument('-in', '--input', nargs='?', metavar='File Path', 
                        default=stdin.buffer)
    parser.add_argument('-mod', '--modify', nargs=2, metavar=('Param', 'Value'))
    parser.add_argument('-fn','--function', dest='rf', action='store_true',
                        help='Read for inputted function')
    
    # Add subparsers for each function available
    subparser = parser.add_subparsers(title='Function Commands', dest='fc')

    # Gather list of functions
    fn_list = dict([(name, cls) for name, cls in fn.__dict__.items() if isinstance(cls, type)])

    for fn in fn_list.values():
        if hasattr(fn, 'clArgs'):
            fn.clArgs(subparser)
    
    # Final arguments
    parser.add_argument('-di', '--delete-imaginary', action='store_true', dest='di',
                        help='Remove imaginary elements from dataset')
    parser.add_argument('-out', '--output', nargs='?',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    parser.add_argument('-ov', '--overwrite', action='store_true', 
                        help='Call this argument to overwrite when sending output to file.')

    return parser.parse_args(input_args)