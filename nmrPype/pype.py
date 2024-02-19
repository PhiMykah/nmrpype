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
    from nmrio import readFromFile, readFromBuffer, load_ccp4_map

    # Determine whether or not reading from the pipeline
    if type(input) == str:
        if input.endswith('.map'):
            dic, data = load_ccp4_map(input)
        else:
            dic, data = readFromFile(input)
    else:
        dic, data = readFromBuffer(input)
        
    df.setHeader(dic)
    df.setArray(data)
    return 0
    

def fileOutput(data : DataFrame, output, overwrite : bool) -> int:
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
    from nmrio import writeToFile, writeToBuffer

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
            fn_params[opt] = getattr(args, opt)

    # Attempt to run operation, error handling within is handled per function
    return (data.runFunc(fn, fn_params))

def main() -> int:
    #from rpy.parse import parser
    
    try:
        data = DataFrame() # Initialize DataFrame

        args = parser(sys.argv[1:]) # Parse user command line arguments

        fileInput(data, args.input) # Determine whether reading from pipeline or not

        if type(args.input) == str:
            if args.input.endswith('.map'):
                return 0
            
        if hasattr(args.input, 'close'): # Close file/datastream if necessary
            args.input.close()

        # Modify header if modification parameters are provided
        if args.modify:
            headerModify(data, args.modify[0], args.modify[1])

        # Process function from command line if provided
        if args.fc:
            function(data, args)

        # Delete imaginary element if prompted
        if args.di:
            data.runFunc('DI', {'mp_enable':args.mp_enable,'mp_proc':args.mp_proc,'mp_threads':args.mp_threads})

        # Output Data as Necessary
        fileOutput(data, args.output, args.overwrite)

    except Exception as e:
        catchError(e, PipeBurst, msg='nmrPype has encountered an error!', ePrint=False)
         
    return 0

if __name__ == '__main__':
    sys.exit(main())