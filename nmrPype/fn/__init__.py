# Set fn to import all of the data from the folder
from .function import nmrFunction as Function
from .FT import FourierTransform as FT
from .ZF import ZeroFill as ZF
from .PC import PhaseCorrection as PC 

__all__ = ['Function', 'FT', 'ZF', 'PC']