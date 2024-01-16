from .function import nmrFunction as Function

class FourierTransform(Function):
    def __init__(self, ft_inv: bool = False, ft_real: bool = False, ft_neg: bool = False, ft_alt: bool = False):
        self.ft_inv = ft_inv 
        self.ft_real = ft_real
        self.ft_neg = ft_neg
        self.ft_alt = ft_alt
        params = {'ft_inv':ft_inv, 'ft_real': ft_real, 'ft_neg': ft_neg, 'ft_alt': ft_alt}
        super().__init__(params) 

    @staticmethod
    def commands(subparser):
        """
        fn commands

        Adds Fourier Transform parser to the subparser, with its corresponding args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument},
            e.g. the ft_inv destination stores the inv bool argument for the ft function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        # FT subparser
        FT = subparser.add_parser('FT', help='Perform a Fourier transform (FT) on the data')
        FT.add_argument('-inverse', '-inv', action='store_true',
                        dest='ft_inv', help='Perform inverse FT')
        FT.add_argument('-real', action='store_true',
                        dest='ft_real', help='Perform a FT only on the real portion of the data')
        FT.add_argument('-neg', action='store_true',
                        dest='ft_neg', help='Negate imaginaries when performing FT')
        FT.add_argument('-alt', action='store_true',
                        dest='ft_alt', help='Use sign alternation when performing FT')
        
        # Include universal commands proceeding function call
        Function.universalCommands(FT)

    def func(self, array):
        from scipy import fft
        from numpy import flip, roll
        """
        fn func

        Performs a fast fourier transform operation on 1-D array
        
        Header updating operations are performed outside scope

        Parameters
        ----------
        array : ndarray (1-D)
            Array to perform operation on, passed from run
        Returns
        -------
        array : ndarray
            Modified 1-D array after operation
        """
        # Operations to perform on the data, transform then shift
        ft = fft.fft
        shift = fft.fftshift

        # Change operations based on the parameters
        if (self.ft_inv):
            # Perform an inverse fft
            ft = fft.ifft
            shift = fft.ifftshift
            
        elif (self.ft_real):
            # Perform a real fft
            ft = fft.rfft

        elif (self.ft_neg):
            # Negate imaginaries when performing FT
            pass 

        elif (self.ft_alt):
            # Use sign alternation when performing FT
            pass
        
        # Perform operation
        array = ft(array)
        
        # Shift the data 
        array = shift(array)

        # Flip data, then move the data over by 1 (correction based on previous operations)
        array = flip(array)
        array = roll(array, 1)

        return array


    def updateFunctionHeader(self, data, sizes):
        """ 
        fn updateFunctionHeader

        Update the header after function processing
            based on the function itself 

        Parameters
        ----------
        sizes : list of ints
            Parameter sizes before function operation
        """
        get = data.getParam
        mod = data.modifyParam
        currDim = data.header.getcurrDim()
        # Flip FT flag
        if (bool(get('NDFTFLAG'))):
            mod('NDFTFLAG', float(0), currDim) 
        else:
            mod('NDFTFLAG', float(1), currDim) 

        # Set NDAQSIGN and NDFTSIZE
        if (bool(get('NDFTFLAG'))):
            mod('NDAQSIGN', float(0), currDim)
            mod('NDFTSIZE', data.getTDSize(), currDim)
        else:
            # Implement `dataInfo->outQuadState = 2`
            mod('NDFTSIZE', data.getTDSize(), currDim) 

        # Add flag for complex
        mod('FDQUADFLAG', float(0))
        mod('NDQUADFLAG', float(0), currDim)  
        
        # Check for real flag, and update based on real (divide the size by 2)
        apod = data.header.checkParamSyntax('NDAPOD', currDim)
        currDimSize = sizes[apod]
        
        currDimSize = currDimSize/2 if self.ft_real else currDimSize
        mod('NDAPOD', float(currDimSize), currDim)  
        