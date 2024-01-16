from .function import nmrFunction as Function

class DeleteImaginary(Function):
    def __init__(self):
        params = {}
        super().__init__(params)

    def run(self, data):
        """
        fn run

        Zerofill has a unique run operation due to modifying ndarrays

        Parameters
        ----------
        data : NMRData
            dataset to process
        """
        from utils import EmptyNMRData, catchError, FunctionError

        try:
            from numpy import nditer

            # Ensure data is available to modify
            array = data.np_data
            if type(array) is None:
                raise EmptyNMRData("No data to modify!")
            
            dataLength = array.shape[-1]

            # Update header before processing data
            self.updateHeader(data)

            # Take parameters from dictionary and allocate to designated header locations
            sizes = self.obtainSizes(data)

            # Process data stream in a series of 1-D arrays
            with nditer(array, flags=['external_loop','buffered'], op_flags=['readwrite'], buffersize=dataLength) as it:
                for x in it:
                    x[...] = self.func(x)

            # Cut the 2nd dimension in half if it exists
            if len(data.np_data.shape) >= 2:
                lenY = data.np_data.shape[-2]
                data.np_data = data.np_data[...,:int(lenY/2),:]

            self.updateHeader(data)
            self.updateFunctionHeader(data, sizes)

        # Exceptions
        except Exception as e:
            msg = "Unable to run function {0}!".format(type(self).__name__)
            catchError(e, new_e=FunctionError, msg=msg)

    def func(self, array):
        """
        fn func

        Deletes imaginaries of 1-D array sent to the function
        
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
        return array.real

    def updateFunctionHeader(self, data, sizes):
        # Variables for code simplification
        get = data.getParam
        mod = data.modifyParam
        currDim = data.header.getcurrDim()
        shape = data.np_data.shape 

        # Set curr dimension's quad flag to real
        mod('NDQUADFLAG', float(1), currDim)

        qFlags = []
        # Get the flags for all dimensions
        for dim in range(len(shape)):
            qFlags.append(get('NDQUADFLAG', dim+1))
        
        # Check if all dimensions are real
        isReal = all(bool(flag) for flag in qFlags)

        mod('FDQUADFLAG', float(1) if isReal else float(0))

        from numpy import prod
        # Update Slicecount
        slices = prod(shape[:-1])

        mod('FDSLICECOUNT', float(slices))