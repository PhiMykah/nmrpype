from .function import nmrFunction as Function

class DeleteImaginary(Function):
    def __init__(self, data):
        params = {}
        super().__init__(data, params)


def run(self):
    """
    fn run (Delete Imaginary)

    Remove imaginary element from data
        Then update the header to indicate performa
    """
    from numpy import real
    data = self.data
    get = data.getParam
    try:
        # Delete imaginary elements
        data.np_data = real(data.np_data)
        dimCount = int(get('FDDIMCOUNT'))
        # Remove imaginary elements in direct dimensions
        
        if (dimCount > 1):
            currDim = int(data.header.currDim)
            # Check if direct dimension and real or complex
            isReal = True # NYI
            if (isReal):
                # Obtain direct dimensions and slice based on size
                match dimCount:
                    case 2:
                        realIndex = int(len(data.np_data)/2)
                        data.np_data = data.np_data[:realIndex]

        # Update header properly based on deleting Imaginary values
        self.updateHeader()
        self.updateFunctionHeader(data.getTDSize())
    except:
        pass

def updateFunctionHeader(self, size):
    pass