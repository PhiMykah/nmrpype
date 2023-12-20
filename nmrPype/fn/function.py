class nmrFunction:
    from utils import NMRData
    def __init__(self,  data: NMRData, params : dict = {}):
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

        #Updates particular params based on the dimensions provided
        match int(hdr.getParam('FDDIMCOUNT')):
            case 1:
                set('FDSIZE', float(len(np_data)))
            case 2:
                set('FDSIZE', float(len(np_data[0])))
                set('FDSPECNUM', float(len(np_data)))
            case 3:
                set('FDSIZE', float(len(np_data[0][0])))
                set('FDSPECNUM', float(len(np_data[0])))
                set('FDF3SIZE', float(len(np_data)))
            case 4:
                set('FDSIZE', float(len(np_data[0][0][0])))
                set('FDSPECNUM', float(len(np_data[0][0])))
                set('FDF3SIZE', float(len(np_data[0])))
                set('FDF4SIZE', float(len(np_data)))
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')

    def updateFunctionHeader(size = 0):
        # Empty function for parent function class, implemented in the child classes
        pass 