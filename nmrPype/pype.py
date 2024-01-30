import sys
from utils import DataFrame
from utils import catchError
from utils import PipeBurst

def fileInput():
    pass
def main() -> int:
    #from rpy.parse import parser
    
    try:
        data = DataFrame()

        #args = parser(sys.argv[1:])

        # Determine whether reading from pipeline or no
    except Exception as e:
        catchError(e, PipeBurst, msg='nmrPype has encountered an error!', ePrint=True)
         
    return 0

if __name__ == '__main__':
    sys.exit(main())