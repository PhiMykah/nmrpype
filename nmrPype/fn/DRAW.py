from .function import DataFunction as Function
import numpy as np
import matplotlib.pyplot as plt

class Draw(Function):
    """
    class Draw

    Data Function object for drawing the current state of the data to a file
    """
    def __init__(self):
        pass

    ############
    # Function #
    ############

    def run(self, data) -> int:
        pass

    ##################
    # Static Methods #
    ##################

    @staticmethod
    def clArgs(subparser):
        """
        fn clArgs (Template command-line arguments)

        Adds function parser to the subparser, with its corresponding default args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # DRAW subparser
        DRAW = subparser.addparser('DRAW', help = 'Draw the current state of the data out to a file')
        DRAW.add_argument('-file', type=str, metavar='PATH/NAME.FMT', required=True,
                          dest='drw_file',help='Destination file to output')
        DRAW.add_argument('-fmt', type=str, metavar='File Format', default='pdf',
                          dest='drw_fmt',help='File Save format')
        DRAW.add_argument('-plot', type=str.lower, choices=['line', 'contour'],
                          dest='drw_plot',help='Plotting method (line or contour)')
        DRAW.add_argument('-slice', type=int, metavar='SLICECOUNT', default=5,
                          dest='drw_slice',help='Number of data 1-D/2-D slices to draw from full set')
        
        # Include universal commands proceeding function call
        Function.clArgsTail(DRAW)


    ####################
    #  Proc Functions  #
    ####################