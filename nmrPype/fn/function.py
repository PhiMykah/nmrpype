from ..utils import UnsupportedDimension, NMRData

class nmrFunction:
    def __init__(self, **params):
        self.params = params

    def updateHeader(self, nmrData: NMRData, size : int, fn_params: dict = {}):
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

        hdr = nmrData.header # Variable for code simplification

        #Updates particular params based on the dimensions provided
        match int(hdr.getParam('FDDIMCOUNT')):
            case 1:
                nmrData.modifyParam('FDSIZE', float(len(self.np_data)))
            case 2:
                nmrData.modifyParam('FDSIZE', float(len(self.np_data[0])))
                nmrData.modifyParam('FDSPECNUM', float(len(self.np_data)))
            case 3:
                nmrData.modifyParam('FDSIZE', float(len(self.np_data[0][0])))
                nmrData.modifyParam('FDSPECNUM', float(len(self.np_data[0])))
                nmrData.modifyParam('FDF3SIZE', float(len(self.np_data)))
            case 4:
                nmrData.modifyParam('FDSIZE', float(len(self.np_data[0][0][0])))
                nmrData.modifyParam('FDSPECNUM', float(len(self.np_data[0][0])))
                nmrData.modifyParam('FDF3SIZE', float(len(self.np_data[0])))
                nmrData.modifyParam('FDF4SIZE', float(len(self.np_data)))
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')

        # Modify function specific header values
        self.updateFunctionHeader(nmrData, size)

    def updateFunctionHeader(nmrData, size):
        # Empty function for parent function class, implemented in the child classes
        pass 