from .function import DataFunction
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .DI import DeleteImaginary as DI

fn_list = {'function':DataFunction, 'FT':FT, 'ZF':ZF, 'DI':DI}
__all__ = ['DataFunction', 'FT', 'ZF', 'DI']