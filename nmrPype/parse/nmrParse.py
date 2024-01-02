def fnSubparser(subparser):
    from sys import stdin,stdout
    # FT subparser
    FT = subparser.add_parser('FT', help='Perform a Fourier transform (FT) on the data')
    FT.add_argument('-inverse', '-inv', action='store_true',
                    dest='ft_inv', help='Perform inverse FT')
    FT.add_argument('-real', action='store_true',
                    dest='ft_real', help='Perform a FT only on the real portion of the data')
    FT.add_argument('-neg', action='store_true',
                    dest='ft_neg', help='Negate imaginaries when performing FT')
    FT.add_argument('-alt', action='store_true',
                    dest='ft_alt', help='Use sign alternation when performing FT')
    
    # Handle output following function
    FT.add_argument('-output', '-out', nargs='?', dest='output',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    FT.add_argument('-overwrite', '-ov', action='store_true', dest='overwrite',
                        help='Call this argument to overwrite when sending output to file.')
    

    # ZF subparser
    ZF = subparser.add_parser('ZF', help='Perform a Zero Fill (ZF) Operation on the data')
    
    group = ZF.add_mutually_exclusive_group() 
    group.add_argument('-zf', type=int, metavar='count', default=0,
                    dest='zf_count', help='-Number of Times to Double the size')
    group.add_argument('-pad', type=int, metavar='padCount', default=0,
                    dest='zf_pad', help='Zeros to Add by Padding')
    group.add_argument('-size', type=int, metavar='xSize', default=0,
                    dest='zf_size', help='Desired Final size')
    group.add_argument('-auto', action='store_true',
                    dest='zf_auto', help='Round Final Size to Power of 2.')
    group.add_argument('-inv', action='store_true',
                    dest='zf_inv', help='Extract Original Time Domain.')

    # Handle output following function
    ZF.add_argument('-output', '-out', nargs='?', dest='output',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    ZF.add_argument('-overwrite', '-ov', action='store_true', dest='overwrite',
                        help='Call this argument to overwrite when sending output to file.')
    

    # PS subparser
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
    
    # Handle output following function
    PS.add_argument('-output', '-out', nargs='?', dest='output',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    PS.add_argument('-overwrite', '-ov', action='store_true', dest='overwrite',
                        help='Call this argument to overwrite when sending output to file.')
    
    
def parseArgs(input_args : list):
    from argparse import ArgumentParser
    from sys import stdin,stdout
    parser = ArgumentParser(prog='nmrPype',description='Handle NMR Data inputted through file or pipeline \
                                    and perform desired operations for output.')
    parser.add_argument('-input', '-in', nargs='?', metavar='File Path', 
                        default=stdin.buffer)
    parser.add_argument('-modify', '-mod', nargs=2, metavar=('Param', 'Value'))
    parser.add_argument('-function','-fn', dest='rf', action='store_true',
                        help='Read for inputted function')
    parser.add_argument('-di', '--delete-imaginary', action='store_true', 
                        help='Remove imaginary elements from dataset')
    subparser = parser.add_subparsers(title='Function Commands', dest='fc')
    fnSubparser(subparser)

    parser.add_argument('-output', '-out', nargs='?',
                        default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
    parser.add_argument('-overwrite', '-ov', action='store_true', 
                        help='Call this argument to overwrite when sending output to file.')

    return parser.parse_args(input_args)