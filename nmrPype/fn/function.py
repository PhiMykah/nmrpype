class nmrFunction:
    def __init__(self,  data, params : dict = {}):
        self.data = data # Stores the NMRData object
        self.params = params # Store params as a dictionary by default

    def run(self): 
        pass

    def updateHeader(self):
        from utils import UnsupportedDimension
        """
        fn updateHeader

        Function that handles the updating of the header
            - Updates parameters based on the dimension count
            - Updates function parameters
            - Updates any miscellaneous fields

        Parameters
        ----------
        nmrData : NMRData
            The data object receiving the modifications to the header
        size
            The size of the data prior to any operations performed
                used for header storage
        fn_params : dict
            Operations dictionary provided for a called function if provided
        """
        # Variables for code simplification
        nmrData = self.data
        set = nmrData.modifyParam
        np_data = nmrData.np_data
        hdr = nmrData.header 

        # Extract sizes from the np array axes, then
        # Updates particular params based on the dimension count
        match int(hdr.getParam('FDDIMCOUNT')):
            case 1:
                lenX = self.np_data.shape
                set('FDSize', float(lenX))
            case 2:
                lenY, lenX = self.np_data.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
            case 3:
                lenZ, lenY, lenX = self.np_data.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
                set('FDF3SIZE', float(lenZ))
            case 4:
                lenA, lenZ, lenY, lenX = self.np_data.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
                set('FDF3SIZE', float(lenZ))
                set('FDF4SIZE', float(lenA))
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')

    def updateFunctionHeader(size = 0):
        # Empty function for parent function class, implemented in the child classes
        pass 