from .function import DataFunction as Function
import numpy as np
import matplotlib.pyplot as plt
import os

# type Imports/Definitions
from matplotlib.colors import LinearSegmentedColormap
from ..utils import DataFrame
type ColorMap = LinearSegmentedColormap | str

class Draw(Function):
    """
    Data Function object for drawing the current state of the data to a file

    Parameters
    ----------
    draw_file : str
        Output file for drawing graphic in string format

    draw_fmt : str
        Format to save the file in (e.g png, pdf)

    draw_plot : str
        Plotting method for drawing output (e.g line plot or contour plot)
    
    draw_slice : int
        Number of 1D/2D slices to draw out of the total vectors/planes

    mp_enable : bool
        Enable multiprocessing

    mp_proc : int
        Number of processors to utilize for multiprocessing

    mp_threads : int
        Number of threads to utilize per process
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

    def run(self, data : DataFrame) -> int:
        """
        See :py:func:`nmrPype.fn.function.DataFunction.run` for documentation
        """
        
        # Check if format is provided, and set it manually if needed
        if not self.fmt:
            # If not given a file extension, use default
            if len(self.file.split('.')) == 1:
                self.fmt = 'png'
            else:
                self.fmt = self.file.split('.')[-1]

        if self.plot.lower() == 'line':
            return self.graphLine(data)
        if self.plot.lower() == 'contour' and data.array.ndim > 1:
            return self.graphContour(data)
        if data.array.ndim == 1:
            return self.graphLine(data)
        
        return self.graphContour(data)


    def graphLine(self, data : DataFrame, **kwargs) -> int:
        """
        Graph a certain amount of lines based on the user parameters and data

        Parameters
        ----------
        data : DataFrame
            Target data to plot

        **kwargs
            Plotting arguments, *** CURRENTLY UNUSED ***

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        shape = data.array.shape

        # Obtain title function, number of total slices, and slice per plane
        title, slice_num, slices = self.graphLineSyntax(data.array.ndim, shape)

        # Set the limit to be whichever value is smallest
        limit = min(slice_num, self.slice)

        # Generate figure and axes based on amount of slices
        fig, axs = plt.subplots(limit, 2, squeeze=False, figsize=(20,9*limit))

        # Create xlabel with NDLABEL and the direct dimension's index
        xLabel = "{} pts {}".format(data.getParam('NDLABEL'), chr(87+data.getDimOrder(1)))

        return self.drawLineToFile(data.array, title, fig, axs, limit, slices, xLabel, **kwargs)


    def graphContour(self, data : DataFrame, cmap : ColorMap ="", **kwargs) -> int:
        """
        Graph a certain amount of contour planes based on the user parameters and data

        Parameters
        ----------
        data : DataFrame
            Target data to plot

        cmap : ColorMap [LinearSegmentedColorMap or str]
            Designated color map for contour plot 

        **kwargs
            Plotting arguments, *** CURRENTLY UNUSED ***

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        shape = data.array.shape

        # Obtain title function, number of total slices, and slice per cube
        title, slice_num, slices = self.graphContourSyntax(data.array.ndim, shape)

        # Set the limit to be whichever value is the smallest
        limit = min(slice_num, self.slice)

        # Generate figure and axes based on amount of slices
        fig, axs = plt.subplots(limit, 2, squeeze=False, figsize=(20,9*limit))

        # Create xLabel with NDLABEL and the direct dimension's index
        xLabel = "{} pts {}".format(data.getParam('NDLABEL'), chr(87+data.getDimOrder(1)))

        # Create yLabel with NDLABEL and the first indirect dimension's index
        yLabel = "{} pts {}".format(data.getParam('NDLABEL', data.getDimOrder(2)), chr(87+data.getDimOrder(2)))

        # Configure color map
        cmap = cmap if cmap != "" else plt.get_cmap('RdBu')
        cmap = plt.get_cmap(cmap) if type(cmap) == str else cmap
 
        return self.drawContourToFile(data.array, cmap, title, fig, axs, limit, slices, xLabel, yLabel, **kwargs)


    ####################
    # Helper Functions #
    ####################
    
    def drawLineToFile(self, array : np.ndarray, title,
                       fig, axs, limit : int, slices : int, xLabel : str, **kwargs) -> int:
        """
        Takes parameters processed in graphLine and plots using matplotlib

        Parameters
        ----------
        array : np.ndarray
            ndarray to plot

        title : function
            Title lambda function for outputting the title (see graphLineSyntax)

        fig : pyplot.Figure
            Figure used to plot 

        axs : np.ndarray[pyplot.Axes]
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
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        # Avoid division by 0 through assertion
        assert slices != 0

        # Datalength for buffer is based on number of points in vector
        dataLength = array.shape[-1]

        
        gridspec = axs[0, 0].get_subplotspec().get_gridspec()

        for ax in axs.flat:
            ax.remove()

        # Iterate over each vector and plot with proper formatting
        with np.nditer(array, flags=['external_loop','buffered'], op_flags=['readonly'], buffersize=dataLength) as it:
            graph_num = 1
            
            for vector in it:
                subfig = fig.add_subfigure(gridspec[graph_num-1, :])
                ax = subfig.subplots(1,2, squeeze=False)

                # Make sure index 0 is the amount of 1D slices per plane
                x = slices if (graph_num % slices == 0) else graph_num % slices
                
                # Number of planes and cubes essentially in base(slices)
                y = int(np.floor(graph_num / slices) + 1)
                z = int(np.floor(graph_num / slices**2) + 1)

                # Generate title
                subfig.suptitle(title(x,y,z, graph_num), fontsize='xx-large')

                # Plot real and imaginary axes and label
                #subfig.colorbar(pc, shrink=0.6, ax=axsLeft, location='bottom')
                ax[0,0].plot(vector.real, 'r', **kwargs)
                ax[0,0].set_title("Real", fontsize='x-large')
                ax[0,0].set_xlabel(xLabel, fontsize='x-large')
                
                ax[0,1].plot(vector.imag, 'b', **kwargs)
                ax[0,1].set_title("Imaginary", fontsize='x-large')
                ax[0,1].set_xlabel(xLabel, fontsize='x-large')
                
                graph_num += 1
                # Ensure limit has not been reached
                if limit:
                    if graph_num > limit:
                        break       

        # Generate out file for saving
        outfile = os.path.join(self.dir, "{0}.{1}".format(self.file.split('.')[0], self.fmt))
        fpath = os.path.abspath(outfile)
        fig.savefig(fpath, format=self.fmt)


    def drawContourToFile(self, array : np.ndarray, cmap : ColorMap, title,
                       fig : plt.Figure, axs : plt.Axes, limit : int, 
                       slices : int, xLabel : str, yLabel : str, **kwargs) -> int:
        """
        Takes parameters processed in graphContour and plots using matplotlib

        Parameters
        ----------
        array : np.ndarray
            ndarray to plot

        cmap : ColorMap [LinearSegmentedColorMap or str]
            Designated color map for contour plot 

        title : function
            Title lambda function for outputting the title (see graphContourSyntax)

        fig : pyplot.Figure
            Figure used to plot 

        axs : np.ndarray[pyplot.Axes]
            ndarray of axes objects to plot 1D vectors onto

        limit : int
            Maximum number of plots to output

        slices : int
            Number of 1D vectors in a plane

        xLabel : str
            x-axis label (eg. H1 pts X)

        yLabel : str
            y-axis label (eg. N pts Y)

        **kwargs
            Plotting arguments, *** CURRENTLY UNUSED ***

        Returns
        -------
        int
            Integer exit code (e.g. 0 success 1 fail)
        """
        # Avoid division by 0 through assertion
        assert slices != 0

        gridspec = axs[0, 0].get_subplotspec().get_gridspec()

        for ax in axs.flat:
            ax.remove()

        # Iterate over each vector and plot with proper formatting
        it = np.nditer(array, flags=['multi_index'])
        with it:
            graph_num = 1
            while not it.finished:
                indices = it.multi_index
                slice_indices = tuple(indices[:-2])
                # Obtain 2D slice from current axes
                slice_2d = it.operands[0][slice_indices]
            
                subfig = fig.add_subfigure(gridspec[graph_num-1, :])
                ax = subfig.subplots(1,2, squeeze=False)

                # Make sure index 0 is the amount of 1D slices per plane
                x = slices if (graph_num % slices == 0) else graph_num % slices
                
                # Number of planes and cubes essentially in base(slices)
                y = int(np.floor(graph_num / slices) + 1)

                # Generate title
                subfig.suptitle(title(x,y, graph_num), fontsize='xx-large')
                
                # Find min and max
                vmin = min(np.min(slice_2d.real), np.min(slice_2d.imag))
                vmax = max(np.max(slice_2d.real), np.max(slice_2d.imag))
                
                # Plot real and imaginary axes and label
                plots = (slice_2d.real, slice_2d.imag)
                plot_type = ('Real', 'Imaginary')
                for i in range(len(plots)):
                    ax[0,i].pcolormesh(plots[i], cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)
                    ax[0,i].set_title(plot_type[i], fontsize='x-large')
                    ax[0,i].set_xlabel(xLabel, fontsize='x-large')
                    ax[0,i].set_ylabel(yLabel, fontsize='x-large')

                
                # Skip over duplicate iterations by moving to the next non 2-D array
                bound2D = tuple(x - 1 for x in it.shape[-2:])
                it.multi_index = indices[:-2] + bound2D
                
                graph_num += 1
                it.iternext()

                # Ensure limit has not been reached
                if limit:
                    if graph_num > limit:
                        break    

        # Generate out file for saving
        outfile = os.path.join(self.dir, "{0}.{1}".format(self.file.split('.')[0], self.fmt))
        fpath = os.path.abspath(outfile)
        fig.savefig(fpath, format=self.fmt)


    def graphLineSyntax(self, ndim : int, shape : tuple[int, ...]):
        """
        Obtain number of slices given shape and dimension
        then create title lambda function to output information for plotting

        Parameters
        ----------
        ndim : int
            Number of dimensions in array
        shape : tuple[int, ...]
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
    

    def graphContourSyntax(self, ndim : int, shape : tuple[int, ...]):
        """
        Obtain number of slices given shape and dimension
        then create title lambda function to output information for plotting

        Parameters
        ----------
        ndim : int
            Number of dimensions in array
        shape : tuple[int, ...]
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
        lenZ = 1
        slice_num = 1
        match ndim:
            case 2:
                title = lambda x,y,a : f"2D Contour Plot"
            case 3:
                title = lambda x,y,a : f"2D Contour Plot Number {x}"
                lenZ = shape[-3]
                slice_num = lenZ
            case 4:
                title = lambda x,y,a : f"3D Cube Number {y} | 2D Contour Plot Number {x}"
                lenA, lenZ = shape[:-2]
                slice_num = lenA * lenZ
            case _:
                title = lambda x,y,a : f"Slice Number {a}"
                lenZ = shape[-3]
                slice_num = np.prod(shape)
        return title, slice_num, lenZ
    

    ##################
    # Static Methods #
    ##################

    @staticmethod
    def clArgs(subparser):
        """
        Draw command-line arguments

        Adds function parser to the subparser, with its corresponding default args
        Called by :py:func:`nmrPype.parse.parser`.
        
        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # DRAW subparser
        DRAW = subparser.add_parser('DRAW', help='Draw the current state of the data out to a file')
        DRAW.add_argument('-help', action='help', help='')
        DRAW.add_argument('-file', type=str, metavar='PATH/NAME.FMT', required=True,
                          dest='draw_file', help='Destination file to output')
        DRAW.add_argument('-fmt', type=str, metavar='File Format', default='',
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