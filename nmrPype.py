"""
Constant definitions
NAMELEN = 1023
BYTESPERWORD = 4
BITSPERWORD = 32
LARGENUM = 10.0E+16
PI = 3.14159265
"""

import sys
from utils.nmrParse import argParser as parse
from utils.nmrData import *

functions_dict = {'FT': 'fnFourierTransform',
                  'ZF': 'fnZeroFill'
}

def fileInput(userData, file):
    # Attempt to read the input stream
    try:
        userData.readFile(file)
    except Exception as e:
        raise type(e)(e.message + ' Exception has occured whist attempting to read data stream!')


def fileOutput(userData, output, overwrite):
    # Attempt to write to output stream
    try:
        userData.writeOut(output,overwrite)
    except Exception as e:
        raise type(e)(e.message + 'An exception occured when attempting to write data!')


def mod(userData, param, value):
    userData.modifyParam(param,value)


def runFunction(userData, args):
    fn = args.fc

    # Run function based on what function key the user has inputted.
    operation = getattr(userData, functions_dict[fn])
    
    fn_params = {}
    # Add operations based on the function
    for opt in vars(args):
        if (opt.startswith(fn.lower())):
            fn_params[opt] = getattr(args, opt)
    # Attempt to run operation, error handling within is handled per function 
    operation(fn_params)


if __name__ == '__main__': 
    userData = NMRData() # Initialize NMR Data object for handling the data

    args = parse(sys.argv[1:]) # Parse the command line arguments from user
    
    fileInput(userData, args.input) # Process input stream, from file or stdin

    if hasattr(args.input, 'close'): # Close the input file if necessary 
        args.input.close() 

    # Modify header if modification parameters are provided
    if args.modify:
        mod(userData, args.modify[0], args.modify[1])

    # Process function from command line if provided
    if args.fc:
        runFunction(userData, args)

    # Delete imaginary element if prompted
    if args.delete_imaginary:
        userData.deleteImaginary()

    # Output NMR data after changes made
    fileOutput(userData, args.output, args.overwrite)



