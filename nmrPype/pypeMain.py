"""
pypeMain.py: Functions similarly to nmrPipe but as a python script
"""
import sys 
from utils import NMRData, catchError, PipeBurst

def fileInput(userData, file):
    # Attempt to read the input stream
    try:
        userData.readFile(file)
    except Exception as e:
        msg = "Exception has occured whist attempting to read data stream!"
        catchError(e, msg=msg)


def fileOutput(userData, output, overwrite):
    # Attempt to write to output stream
    try:
        userData.writeOut(output,overwrite)
    except Exception as e:
        msg = "An exception occured when attempting to write data!"
        catchError(e, msg=msg)


def mod(userData, param, value):
    userData.modifyParam(param,value)


def function(userData, args):
    fn = args.fc
    
    fn_params = {}
    # Add operations based on the function
    for opt in vars(args):
        if (opt.startswith(fn.lower())):
            fn_params[opt] = getattr(args, opt)

    # Attempt to run operation, error handling within is handled per function 
    userData.runFunction(fn, fn_params)


def main(): 
    from parse import parser

    try:
        userData = NMRData() # Initialize NMR Data object for handling the data

        args = parser(sys.argv[1:]) # Parse the command line arguments from user
        
        fileInput(userData, args.input) # Process input stream, from file or stdin

        if hasattr(args.input, 'close'): # Close the input file if necessary 
            args.input.close() 

        # Modify header if modification parameters are provided
        if args.modify:
            mod(userData, args.modify[0], args.modify[1])

        # Process function from command line if provided
        if args.fc:
            function(userData, args)

        # Delete imaginary element if prompted
        if args.delete_imaginary:
            userData.deleteImaginary()

        # Output NMR data after changes made
        fileOutput(userData, args.output, args.overwrite)
    except Exception as e:
        catchError(e, PipeBurst, msg='nmrPype has encountered an error!', ePrint=True)


if __name__ == '__main__':
    main()

