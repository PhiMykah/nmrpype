from .function import DataFunction
from .FT import FourierTransform as FT

fn_list = {'function':DataFunction, 'FT':FT}
__all__ = ['DataFunction', 'FT']