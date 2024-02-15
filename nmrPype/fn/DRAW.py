from .function import DataFunction as Function
import numpy as np
import matplotlib.pyplot as plt
import os

class Draw(Function):
    """
    class Draw

    Data Function object for drawing the current state of the data to a file
    """
    def __init__(self, draw_file : str = "", draw_fmt : str = "",
                 draw_plot : str = "line", draw_slice : int = 5,
                 mp_enable : bool = False, mp_proc : int = 0,
                 mp_threads : int = 0):
        
        desired_path = os.path.abspath(draw_file)

        self.dir, self.file = os.path.split(desired_path)

        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)

        self.fmt = draw_fmt
        self.plot = draw_plot
        self.slice = draw_slice
        self.mp = [mp_enable, mp_proc, mp_threads]

        params = { 'draw_file':draw_file, 'draw_fmt':draw_fmt,
                  'draw_plot':draw_plot, 'draw_slice':draw_slice}
        super().__init__(params)

    ############
    # Function #
    ############

    def run(self, data) -> int:
        """
        fn run

        Main body of DRAW code.
            - determines saving file
            - identifies format
            - graphs to file based on plot type

        Overload run for function specific operations

        Parameters
        ----------
        data : DataFrame
            Target data to run function on

        Returns
        -------
        Integer exit code (e.g. 0 success 1 fail)
        """
        import sys

        # Check if format is provided, and set it manually if needed
        if not self.fmt:
            # If not given a file extension, use default
            if len(self.file.split('.')) == 1:
                self.fmt = 'png'
            else:
                self.fmt = self.file.split('.')[-1]

        if self.plot.lower() == 'line':
            return self.graphLine(data)
        if self.plot.lower() == 'contour':
            return self.graphContour(data)
        if data.array.ndim == 1:
            return self.graphLine(data)
        
        return self.graphContour(data)


    def graphLine(self, data, **kwargs) -> int:
        """
        fn graphLine

        Graph a certain amount of lines based on the user parameters and data

        Parameters
        ----------
        data : DataFrame
            Target data to plot

        **kwargs
            Plotting arguments, *** CURRENTLY UNUSED ***

        Returns
        -------
        Integer exit code (e.g. 0 success 1 fail)
        """
        shape = data.array.shape

        # Obtain title function, number of total slices, and slice per plane
        title, slice_num, slices = self.graphSyntax(data.array.ndim, shape)

        # Set the limit to be whichever value is smallest
        limit = min(slice_num, self.slice)

        # Generate figure and axes based on amount of slices
        fig, ax = plt.subplots(limit, 2, squeeze=False, figsize=(20,9*limit))

        # Create xlabel with NDLABEL and the direct dimension's index
        xLabel = "{} pts {}".format(data.getParam('NDLABEL'), chr(87+data.getDimOrder(1)))

        return self.drawLineToFile(data.array, title, fig, ax, limit, slices, xLabel, **kwargs)


    def graphContour(self, array, limit, cmap="", **kwargs):
        pass
        """
        import seaborn as sns

        cmap = cmap if cmap else plt.get_cmap('RdBu')

        aReal = array.real
        aImag = array.imag
        
        from numpy import nditer
        it = nditer(array, flags=['multi_index'])
        with it:
            slice_num = 1
            while not it.finished:
                indices = it.multi_index
                slice_indices = tuple(indices[:-2])
                # Obtain 2D slice from current axes
                slice_2d = it.operands[0][slice_indices]

                f, ax = plt.subplots() 
                f.suptitle("Plot Number {0}".format(slice_num))
                #sns.heatmap(slice_2d, cmap=cmap, vmin=vmin, vmax=vmax, ax = ax, **kwargs)

                # Skip over duplicate iterations by moving to the next non 2D array
                bound2D = tuple(x - 1 for x in it.shape[-2:])
                it.multi_index = indices[:-2] + bound2D
                
                slice_num += 1
                it.iternext()

                if slice_num > limit:
                        break
        """

    ####################
    # Helper Functions #
    ####################
    
    def drawLineToFile(self, array : np.ndarray, title,
                       fig, ax, limit : int, slices : int, xLabel, **kwargs) -> int:
        """
        fn drawLineToFile

        Takes parameters processed in graphLine and plots using matplotlib

        Parameters
        ----------
        array : np.ndarray
            ndarray to plot

        title : function
            Title lambda function for outputting the title (see graphSyntax)

        fig : pyplot.Figure
            Figure used to plot 

        ax : np.ndarray[pyplot.Axes]
            ndarray of axes objects to plot 1D vectors onto

        limit : int
            Maximum number of plots to output

        slices : int
            Number of 1D vectors in a plane

        xLabel : str
            x-axis label (eg. H1 pts X)

        **kwargs
            Plotting arguments, *** CURRENTLY UNUSED ***

        Returns
        -------
        Integer exit code (e.g. 0 success 1 fail)
        """
        # Avoid division by 0 through assertion
        assert slices != 0

        # Datalength for buffer is based on number of points in vector
        dataLength = array.shape[-1]

        # Iterate over each vector and plot with proper formatting
        with np.nditer(array, flags=['external_loop','buffered'], op_flags=['readonly'], buffersize=dataLength) as it:
            graph_num = 1
            
            for vector in it:
                # Make sure index 0 is the amount of 1D slices per plane
                x = slices if (graph_num % slices == 0) else graph_num % slices
                
                # Number of planes and cubes essentially in base(slices)
                y = int(np.floor(graph_num / slices) + 1)
                z = int(np.floor(graph_num / slices**2) + 1)

                # Generate title
                fig.suptitle(title(x,y,z, graph_num), fontsize='xx-large')

                # Plot real and imaginary axes and label
                ax[graph_num - 1,0].plot(vector.real, 'r', **kwargs)
                ax[graph_num - 1,0].set_title("Real", fontsize='x-large')
                ax[graph_num - 1,0].set_xlabel(xLabel, fontsize='x-large')
                
                ax[graph_num - 1,1].plot(vector.imag, 'b', **kwargs)
                ax[graph_num - 1,1].set_title("Imaginary", fontsize='x-large')
                ax[graph_num - 1,1].set_xlabel(xLabel, fontsize='x-large')
                
                graph_num += 1
                # Ensure limit has not been reached
                if limit:
                    if graph_num > limit:
                        break

            # Generate out file for saving
            outfile = os.path.join(self.dir, "{0}.{1}".format(self.file.split('.')[0], self.fmt))
            fpath = os.path.abspath(outfile)
            fig.savefig(fpath, format=self.fmt)


    def graphSyntax(self, ndim, shape):
        """
        fn graphSyntax

        Obtain number of slices given shape and dimension
            then create title lambda function to output information for plotting

        Parameters
        ----------
        ndim : int
            Number of dimensions in array
        shape : tuple(int)
            Shape of array being plotted

        Returns
        -------
            title : function
                Information output lambda function
            slice_num : int 
                Total number of 1D vectors
            lenY : int
                Number of 1D vectors per plane
        """
        lenY = 1
        slice_num = 1
        match ndim:
            case 1:
                title = lambda x,y,z,a : f"1D Graph"
            case 2:
                title = lambda x,y,z,a : f"1D Slice Number {x}"
                lenY = shape[-2]
                slice_num = lenY
            case 3:
                title = lambda x,y,z,a : f"2D Plane Number {y} | 1D Slice Number {x}"
                lenZ, lenY = shape[:-1]
                slice_num = lenZ * lenY
            case 4:
                title = lambda x,y,z,a : f"3D Cube Number {z} | 2D Plane Number {y} | Slice Number {x}"
                lenA, lenZ, lenY = shape[:-1]
                slice_num = lenA * lenZ * lenY
            case _:
                title = lambda x,y,z,a : f"Slice Number {a}"
                lenY = shape[-2]
                slice_num = np.prod(shape)
        return title, slice_num, lenY
    

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
        DRAW = subparser.add_parser('DRAW', help='Draw the current state of the data out to a file')
        DRAW.add_argument('-file', type=str, metavar='PATH/NAME.FMT', required=True,
                          dest='draw_file', help='Destination file to output')
        DRAW.add_argument('-fmt', type=str, metavar='File Format', default='pself',
                          dest='draw_fmt', help='File Save format')
        DRAW.add_argument('-plot', type=str.lower, choices=['line', 'contour'], default='line',
                          dest='draw_plot', help='Plotting method (line or contour)')
        DRAW.add_argument('-slice', type=int, metavar='SLICECOUNT', default=5,
                          dest='draw_slice', help='Number of data 1D/2D slices to draw from full set')
        
        # Include universal commands proceeding function call
        Function.clArgsTail(DRAW)


    ####################
    #  Proc Functions  #
    ####################