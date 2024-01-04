class nmrFunction:
    def __init__(self,  data, params : dict = {}):
        self.data = data # Stores the NMRData object
        self.params = params # Store params as a dictionary by default

    def run(self): 
        pass
    
    @staticmethod
    def commands(subparser):
        """
        fn commands (Template)

        Adds function parser to the subparser, with its corresponds
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument}
            e.g. the zf_pad destination stores the pad argument for the zf function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """
        pass 
    
    @staticmethod
    def universalCommands(parser):
        from sys import stdout
        parser.add_argument('-di', '--delete-imaginary', action='store_true', dest = 'di',
                            help='Remove imaginary elements from dataset')
        parser.add_argument('-output', '-out', nargs='?', dest='output',
                            default=(stdout.buffer if hasattr(stdout,'buffer') else stdout))
        parser.add_argument('-overwrite', '-ov', action='store_true', dest='overwrite',
                            help='Call this argument to overwrite when sending output to file.')
        
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
                lenX = np_data.shape[0]
                set('FDSIZE', float(lenX))
            case 2:
                lenY, lenX = np_data.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
            case 3:
                lenZ, lenY, lenX = np_data.shape
                set('FDSIZE', float(lenX))
                set('FDSPECNUM', float(lenY))
                set('FDF3SIZE', float(lenZ))
            case 4:
                lenA, lenZ, lenY, lenX = np_data.shape
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