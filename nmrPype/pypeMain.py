"""
pypeMain.py: Functions similarly to nmrPipe but as a python script
"""

def fileInput(userData, file):
    # Attempt to read the input stream
    try:
        userData.readFile(file)
    except Exception as e:
        if hasattr(e,'message'):
            raise type(e)(e.message + ' Exception has occured whist attempting to read data stream!')
        else:
            raise type(e)(' Exception has occured whist attempting to read data stream!')


def fileOutput(userData, output, overwrite):
    # Attempt to write to output stream
    try:
        userData.writeOut(output,overwrite)
    except Exception as e:
        if hasattr(e,'message'):
            raise Exception(e.message + 'An exception occured when attempting to write data!')
        else:
            raise Exception(' An exception occured when attempting to write data!')


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
    import sys
    from parse import parser
    from utils import NMRData

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
        # Set exception message if exception doesn't have message 
        message = "Unable to run nmrPype!"
        message += "" if not hasattr(e, message) else " {0}".format(e.message)


if __name__ == '__main__':
    main()

