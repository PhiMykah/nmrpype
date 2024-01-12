def parseArgs(input_args : list):
    from fn import fn_list
    from argparse import ArgumentParser
    from sys import stdin,stdout
    parser = ArgumentParser(prog='nmrPype',description='Handle NMR Data inputted through file or pipeline \
                                    and perform desired operations for output.')
    parser.add_argument('-input', '-in', nargs='?', metavar='File Path', 
                        default=stdin.buffer)
    parser.add_argument('-modify', '-mod', nargs=2, metavar=('Param', 'Value'))
    parser.add_argument('-function','-fn', dest='rf', action='store_true',
                        help='Read for inputted function')
    parser.add_argument('-di', '--delete-imaginary', action='store_true', dest='di',
                        help='Remove imaginary elements from dataset')
    
    # Add subparsers for each function available
    subparser = parser.add_subparsers(title='Function Commands', dest='fc')
    for fn in fn_list:
        fn.commands(subparser)

    parser.add_argument('-output', '-out', nargs='?',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    parser.add_argument('-overwrite', '-ov', action='store_true', 
                        help='Call this argument to overwrite when sending output to file.')

    return parser.parse_args(input_args)