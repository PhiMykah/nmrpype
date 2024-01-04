from .function import nmrFunction as Function

class FourierTransform(Function):
    def __init__(self, data, ft_inv: bool = False, ft_real: bool = False, ft_neg: bool = False, ft_alt: bool = False):
        self.ft_inv = ft_inv 
        self.ft_real = ft_real
        self.ft_neg = ft_neg
        self.ft_alt = ft_alt
        params = {'ft_inv':ft_inv, 'ft_real': ft_real, 'ft_neg': ft_neg, 'ft_alt': ft_alt}
        super().__init__(data, params) 

    @staticmethod
    def commands(subparser):
        """
        fn commands

        Adds Fourier Transform parser to the subparser, with its corresponds
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

    def run(self):
        from utils import EmptyNMRData
        from scipy import fft
        from numpy import flip
        """
        fn run

        Performs a fast fourier transform operation on the data
            Afterwards, update the header accordingly
        """
        try:
            data = self.data
            if (type(data.np_data) == type(None)):
                raise EmptyNMRData("No data to modify!")

            # Obtain size before operation
            size = data.getParam('NDAPOD', data.header.currDim)

            # Calculate which axes to perform the operation over based on
            #   the number of axes (dimCount) and the current dimension (currDim)
            dimCount = int(data.getParam('FDDIMCOUNT'))
            currDim = int(data.header.currDim)
            targetAxis = dimCount - currDim

            # Obtain the options and parse the options accordingly
            try:
                if (self.ft_inv):
                    data.np_data = fft.ifftn(data.np_data, axes=(targetAxis))
                    
                elif (self.ft_real):
                    data.np_data = fft.rfftn(data.np_data.real, axes=(targetAxis))
                elif (self.ft_neg):
                    # Negate imaginaries when performing FT
                    pass 
                elif (self.ft_alt):
                    # Use sign alternation when performing FT
                    pass
                else:
                    data.np_data = fft.fftn(data.np_data, axes=(targetAxis))
            except KeyError:
                data.np_data = fft.fftn(data.np_data, axes=(targetAxis))
            if (self.ft_inv):
                data.np_data = fft.ifftshift(data.np_data, axes=(targetAxis))
            else:
                data.np_data = fft.fftshift(data.np_data, axes=(targetAxis))
            data.np_data = flip(data.np_data, axis=targetAxis)

            """
            After performing operation, the header must be updated
            """
            # Update header values as a result of the FFT completing
            self.updateHeader()
            self.updateFunctionHeader(size)

        except Exception as e:
            if hasattr(e, 'message'):
                raise type(e)(e.message + ' Unable to perform Fourier transform.')
            else:
                raise type(e)(' Unable to perform Fourier transform.')


    def updateFunctionHeader(self, size):
        nmrData = self.data
        get = nmrData.getParam
        mod = nmrData.modifyParam
        currDim = nmrData.header.getcurrDim()
        # Flip FT flag
        if (bool(get('NDFTFLAG'))):
            mod('NDFTFLAG', float(0), currDim) 
        else:
            mod('NDFTFLAG', float(1), currDim) 

        # Set NDAQSIGN and NDFTSIZE
        if (bool(get('NDFTFLAG'))):
            mod('NDAQSIGN', float(0), currDim)
            mod('NDFTSIZE', nmrData.getTDSize(), currDim)
        else:
            # Implement `dataInfo->outQuadState = 2`
            mod('NDFTSIZE', nmrData.getTDSize(), currDim) 

        # Add flag for complex
        mod('FDQUADFLAG', float(0))
        mod('NDQUADFLAG', float(0), currDim)  
        
        # Check for real flag, and update based on real (divide the size by 2)
        size = size/2 if self.ft_real else size
        mod('NDAPOD', float(size), currDim)  