class nmrFunction:
    def __init__(self):
        pass 
    def updateHeader(self, size : int, function : str = None, fn_params: dict = {}):
        """
        fn updateHeader

        Function that handles the updating of the header
            - Updates parameters based on the dimension count
            - Updates function parameters
            - Updates any miscellaneous fields

        Parameters
        ----------
        size
            The size of the data prior to any operations performed
                used for header storage
        function : str
            function code if a function has been performed to update
                function-specific header parameters
        fn_params : dict
            Operations dictionary provided for a called function if provided
        """

        hdr = self.header # Variable for code simplification

        #Updates particular params based on the dimensions provided
        match int(hdr.getParam('FDDIMCOUNT')):
            case 1:
                self.modifyParam('FDSIZE', float(len(self.np_data)))
            case 2:
                self.modifyParam('FDSIZE', float(len(self.np_data[0])))
                self.modifyParam('FDSPECNUM', float(len(self.np_data)))
            case 3:
                self.modifyParam('FDSIZE', float(len(self.np_data[0][0])))
                self.modifyParam('FDSPECNUM', float(len(self.np_data[0])))
                self.modifyParam('FDF3SIZE', float(len(self.np_data)))
            case 4:
                self.modifyParam('FDSIZE', float(len(self.np_data[0][0][0])))
                self.modifyParam('FDSPECNUM', float(len(self.np_data[0][0])))
                self.modifyParam('FDF3SIZE', float(len(self.np_data[0])))
                self.modifyParam('FDF4SIZE', float(len(self.np_data)))
            case _:
                raise UnsupportedDimension('Dimension provided in \
                                                      header is currently unsupported!')

        # Check if Transform has been performed 
        match function:
            case 'FT':
                self.updateFT(size, fn_params)
            case 'ZF':
                self.updateZF(size, fn_params)
            case 'DI':
                pass