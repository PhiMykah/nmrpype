from .function import DataFunction
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF

fn_list = {'function':DataFunction, 'FT':FT, 'ZF':ZF}
__all__ = ['DataFunction', 'FT', 'ZF']