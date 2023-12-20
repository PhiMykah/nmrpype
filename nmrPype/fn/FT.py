from .function import nmrFunction as Function

class FourierTransform(Function):
    from utils import NMRData
    def __init__(self, data : NMRData, ft_inv, ft_real, ft_neg, ft_alt):
        self.ft_inv = ft_inv 
        self.ft_real = ft_real
        self.ft_neg = ft_neg
        self.ft_alt = ft_alt
        params = {'ft_inv':ft_inv, 'ft_real': ft_real, 'ft_neg': ft_neg, 'ft_alt': ft_alt}
        super().__init__(data, params) 


    def run(self):
        from utils import EmptyNMRData
        from scipy.fft import fft,ifft
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

            # Obtain the options and parse the options accordingly
            try:
                if (self.ft_inv):
                    data.np_data = ifft(data.np_data)
                elif (self.ft_real):
                    data.np_data = fft(data.np_data.real)
                elif (self.ft_neg):
                    # Negate imaginaries when performing FT
                    pass 
                elif (self.ft_alt):
                    # Use sign alternation when performing FT
                    pass
                else:
                    data.np_data = fft(data.np_data)
            except KeyError:
                data.np_data = fft(data.np_data)

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