# Set fn to import all of the data from the folder
from .function import nmrFunction as Function
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .PS import PhaseCorrection as PS 
from .DI import DeleteImaginary as DI
from .TP import Transpose as TP
from .TP import Transpose2D as YTP
from .TP import Transpose3D as ZTP
from .TP import Transpose4D as ATP
from .SP import SineBell as SP

from utils import catchError, FunctionError

__all__ = ['Function', 'FT', 'ZF', 'PS', 'DI', 
           'TP', 'YTP', 'ZTP', 'ATP',
           'SP']