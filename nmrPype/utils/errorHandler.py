import sys
"""
Error Classes 
"""
class PipeBurst(Exception):
    """
    Exception called when the main script reaches an exception,
    a.k.a. something broke. Just done for the nice name opportunity honestly
    """
    pass 

class FileIOError(Exception):
    """
    Exception called when there is an error in reading/writing the data
    """
    pass

class UnknownHeaderParam(Exception):
    """
    Exception called when there is an attempt to call
    a nonexistent header param
    """
    pass

class FunctionError(Exception):
    """
    Exception called when attempting to run a function fails
    """
    pass

def catchError(e, new_e = Exception, msg : str = "", ePrint = False):
    """
    This function is an error-handling helper function for nmrPype.
    It can output to the stderr and continue, or terminate running.

    Parameters
    ----------
    e : Exception
        Exception that called this error handler
    new_e : Exception
        New exception to pass onto the chain
    msg : str
        Error message to output to the screen
    ePrint : bool
        Whether to print to standard error stream or raise and error
    """
    # Obtain error names and initialize new argument tuple
    e_name = type(e).__name__
    new_e_name = new_e.__name__
    new_args = ()

    if len(e.args) == 1: 
        e.args = (" - ".join((e_name, e.args[-1])),)
    elif len(e.args) == 0:
        e.args = (e_name,)
    
    new_e_args = (" - ".join((new_e_name, msg)),) if msg else (new_e_name,)
    new_args = new_e_args + e.args

    if ePrint:
        import traceback
        stack_end = traceback.extract_stack()[-2]
        exc_line = stack_end.lineno
        exc_func = stack_end.name
        exc_file = stack_end.filename
        err_count = len(new_args)
        for i in range(err_count-1, -1, -1):
            print("{0}. {1}".format(err_count-i, new_args[i]), file=sys.stderr)
            if i == 0:
                print(f"Exception was caught on line {exc_line} in module {exc_func}", file=sys.stderr)
                print(f"File: {exc_file}", file=sys.stderr, end="\n\n")
            if i-1 != -1:
                print("The above exception was the cause of the following exception:", file=sys.stderr)
    else:
        raise new_e(*new_args) from e
