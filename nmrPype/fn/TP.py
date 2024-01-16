from .function import nmrFunction as Function
from utils import catchError, FunctionError

class Transpose(Function):
    def __init__(self,
                tp_noord: bool = False, tp_exch : bool = False,
                tp_minMax: bool = True, params : dict = {}):
        
        self.tp_noord = tp_noord
        self.tp_exch = tp_exch
        self.tp_minMax = tp_minMax

        params.update({'tp_noord':tp_noord,
                  'tp_exch':tp_exch,'tp_minMax':tp_minMax,})
        super().__init__(params)

    @staticmethod
    def commands(subparser):    
        """
        fn commands

        Adds Transpose parser to the subparser, with its corresponding args
        Called in nmrParse.py

        Destinations are formatted typically by {function}_{argument},
            e.g. the ps_p0 destination stores the p0 value for the ps function

        Parameters
        ----------
        subparser : _SubParsersAction[ArgumentParser]
            Subparser object that will receive function and its arguments
        """

        # 2D Transpose subparser
        YTP = subparser.add_parser('YTP', aliases=['TP', 'XY2YX'], help='2D Plane Transpose.')
        group = YTP.add_mutually_exclusive_group()
        group.add_argument('-hyper', action='store_true',
                        dest='tp_hyper', help='Hypercomplex Transpose Mode.')
        group.add_argument('-noauto', action='store_false',
                dest='tp_auto', help='Choose Mode via Command Line.')
        group.add_argument('-nohyper', action='store_false',
                        dest='tp_hyper', help='Suppress Hypercomplex Mode.')
        group.add_argument('-auto', action='store_true',
                        dest='tp_auto', help='Chose Mode Automaticaly (Default).')
        YTP.add_argument('-nohdr', action='store_true',
                        dest='tp_nohdr', help='No Change to Header TRANSPOSE state.')
        YTP.add_argument('-exch', action='store_true',
                dest='tp_exch', help='Exchange Header Parameters for the Two Dimensions.')
        
        # Include universal commands proceeding function call
        Transpose.HeaderCommandsTP(YTP)
        Function.universalCommands(YTP)

        # 3D Transpose subparser
        ZTP = subparser.add_parser('ZTP', aliases=['XYZ2ZYX'], help='3D Matrix Transpose.')
        ZTP.add_argument('-exch', action='store_true',
                dest='tp_exch', help='Exchange Header Parameters for the Two Dimensions.')
        
        # Include universal commands proceeding function call
        Transpose.HeaderCommandsTP(ZTP)
        Function.universalCommands(ZTP)

        # 4D Transpose subparser
        ATP = subparser.add_parser('ATP', aliases=['XYZA2AYZX'], help='4D Matrix Transpose.')

        # Include universal commands proceeding function call
        Transpose.HeaderCommandsTP(ATP)
        Function.universalCommands(ATP)


    @staticmethod
    def HeaderCommandsTP(parser):
        """
        fn HeaderCommandsTP 

        Parse commands related to header adjustment
        """
        parser.add_argument('-noord', action='store_true',
                        dest='tp_noord', help='No Change to Header Orders')
        parser.add_argument('-minMax', action='store_true',
                        dest='tp_minMax', help='Update FDMIN and FDMAX')
            

    def run(self, data):
        """
        fn run 

        Process the transpose function for the data, depending on dimensions

        """
        from utils import EmptyNMRData
        try:
            # Ensure data is available to modify
            array = data.np_data
            if type(array) is None:
                raise EmptyNMRData("No data to modify!")
            

        # Exceptions
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)


class Transpose2D(Transpose):
    def __init__(self, data,
                 tp_hyper : bool = False, tp_auto: bool = True,
                 tp_nohdr : bool = False, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False):
        self.tp_hyper = tp_hyper
        self.tp_auto = tp_auto
        self.tp_nohdr = tp_nohdr

        params = {'tp_hyper':tp_hyper,'tp_auto':tp_auto,
                  'tp_nohdr':tp_nohdr}
        super.__init__(data, tp_noord, tp_exch, tp_minMax, params)

class Transpose3D(Transpose):
    def __init__(self, data, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False):
        super().__init__(data, tp_noord, tp_exch, tp_minMax)

class Transpose4D(Transpose):
    def __init__(self, data, tp_noord: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = False):
        super().__init__(data, tp_noord, tp_exch, tp_minMax)