from .function import nmrFunction as Function

class DeleteImaginary(Function):
    def __init__(self, data):
        params = {}
        super().__init__(data, params)

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

    def updateFunctionHeader(self, sizes):
        #FDQUADFLAG
        #NDQUADFLAG
        pass