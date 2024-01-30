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

    input : string or sys.stdin.buffer
        string: reading file name
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
    

def fileOutput(data : DataFrame, output, overwrite : bool) -> int:
    """
    fn fileOutput

    Parameters
    ----------
    data : DataFrame
        DataFrame object reading from to send out to putput

    input : string or sys.stdout.buffer
        string: output file name
        sys.stdin.buffer: read from standard output buffer
    
    Returns
    -------
    Integer exit code (e.g. 0 success 1 fail)
    """
    return 0


def headerModify(data : DataFrame, param : str, value : float) -> int:
    return 0

def function(data : DataFrame, args) -> int:
    return 0

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
        if args.fc:
            function(data, args)

        # Delete imaginary element if prompted
        if args.di:
            pass

        # Output Data as Necessary
        fileOutput(data, args.output, args.overwrite)

    except Exception as e:
        catchError(e, PipeBurst, msg='nmrPype has encountered an error!', ePrint=False)
         
    return 0

if __name__ == '__main__':
    sys.exit(main())