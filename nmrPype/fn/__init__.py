from .function import DataFunction
from .DRAW import Draw
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .DI import DeleteImaginary as DI
from .SP import SineBell as SP
from .PS import PhaseCorrection as PS
from .TP import Transpose as TP
from .TP import Transpose2D as YTP
from .TP import Transpose3D as ZTP
from .TP import Transpose4D as ATP

fn_list = {
    'function':DataFunction,
    'NULL':DataFunction,
    'DRAW':Draw,
    'FT':FT,
    'ZF':ZF,
    'DI':DI,
    'SP':SP,
    'PS':PS,
    'TP':YTP, 'YTP':YTP, 'XY2YX':YTP,
    'ZTP':ZTP, 'XYZ2ZYX':ZTP,
    'ATP':ATP, 'XYZA2AYZX':ATP}


__all__ = ['DataFunction', 'Draw', 'FT', 'ZF', 
           'DI','SP', 'PS', 
           'YTP', 'ZTP', 'ATP']