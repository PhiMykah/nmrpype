from .function import DataFunction
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .DI import DeleteImaginary as DI
from .SP import SineBell as SP

fn_list = {
    'function':DataFunction,
    'FT':FT,
    'ZF':ZF,
    'DI':DI,
    'SP':SP}

__all__ = ['DataFunction', 'FT', 'ZF', 'DI','SP']