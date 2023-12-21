# Set fn to import all of the data from the folder
from .function import nmrFunction as Function
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .PS import PhaseCorrection as PS 

__all__ = ['Function', 'FT', 'ZF', 'PS']