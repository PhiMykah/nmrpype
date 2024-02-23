import sys
from utils import DataFrame, catchError, PipeBurst
from parse import parser

def fileInput(df : DataFrame, input) -> int:
    """
    fn fileInput

    Parameters
    ----------
    data : DataFrame
        DataFrame object to put input data to

    input : string, sys.stdin, or sys.stdin.buffer
        string: reading file name
        sys.stdin: read from standard input
        sys.stdin.buffer: read from standard input buffer
    
    Returns
    -------
    Integer exit code (e.g. 0 success 1 fail)
    """
    from nmrio import readFromFile, readFromBuffer

    # Determine whether or not reading from the pipeline
    if type(input) == str:
        dic, data = readFromFile(input)
    else:
        dic, data = readFromBuffer(input)
        
    df.setHeader(dic)
    df.setArray(data)
    return 0
    

def fileOutput(data : DataFrame, args) -> int:
    """
    fn fileOutput

    Parameters
    ----------
    data : DataFrame
        DataFrame object reading from to send out to putput

    output : string or sys.stdout.buffer
        string: output file name
        sys.stdin.buffer: read from standard output buffer
    
    Returns
    -------
    Integer exit code (e.g. 0 success 1 fail)
    """
    output = args.output
    overwrite = args.overwrite

    from nmrio import writeToFile, writeToBuffer

    if args.fc:
        # Use alternate output if provided
        if args.output_alt:
            output = args.output_alt
        if args.overwrite_alt:
            overwrite = args.overwrite_alt
    
    # Determine whether or not writing to pipeline
    if type(output) == str:
        return writeToFile(data, output, overwrite)
    else:
        return writeToBuffer(data, output, overwrite)


def headerModify(data : DataFrame, param : str, value : float) -> int:
    """
    fn headerModify

    Updates the header based on parameters and value
    """
    try:
        data.setParam(param, value)
    except:
        return 1
    return 0

def function(data : DataFrame, args) -> int:
    fn = args.fc

    fn_params = {}
    # Add operations based on the function
    for opt in vars(args):
        if (opt.startswith(fn.lower())):
            fn_params[opt] = getattr(args, opt)
        elif (opt.startswith('mp')):
            # Allows for cl args to call regardless of location
            if opt.endswith('alt'):
                if getattr(args,opt) != None:
                    new_opt = opt.rstrip('_alt')
                    fn_params[new_opt] = getattr(args, opt)
            elif opt.endswith('2'):
                if getattr(args,opt) != getattr(args,opt.rstrip('2')):
                    new_opt = opt.rstrip('2')
                    fn_params[new_opt] = getattr(args, opt)
            else:
                fn_params[opt] = getattr(args, opt)

    # Attempt to run operation, error handling within is handled per function
    return (data.runFunc(fn, fn_params))

def main() -> int:
    #from rpy.parse import parser
    
    try:
        data = DataFrame() # Initialize DataFrame

        args = parser(sys.argv[1:]) # Parse user command line arguments

        fileInput(data, args.input) # Determine whether reading from pipeline or not
            
        if hasattr(args.input, 'close'): # Close file/datastream if necessary
            args.input.close()

        # Modify header if modification parameters are provided
        if args.modify:
            headerModify(data, args.modify[0], args.modify[1])

        # Process function from command line if provided
        processLater = False
        if args.fc:
            if args.fc == 'DRAW':
                processLater = True
            else:
                function(data, args)
        
        # Obtain delete imaginary parameter only if no function is called
        runDI = args.di if not args.fc else (args.di or args.di_alt)
        # Delete imaginary element if prompted
        if runDI:
            data.runFunc('DI', {'mp_enable':args.mp_enable,'mp_proc':args.mp_proc,'mp_threads':args.mp_threads})

        # Output Data as Necessary
        fileOutput(data, args)

        # Process function after passing data
        if processLater:
            function(data,args)

    except Exception as e:
        catchError(e, PipeBurst, msg='nmrPype has encountered an error!', ePrint=True)
         
    return 0

if __name__ == '__main__':
    sys.exit(main())