from .errorHandler import PipeBurst, FileIOError, FunctionError, catchError
from .fdata import get_fdata, fdata2dic, dic2fdata, get_fdata_data, reshape_data, unshape_data
from .fdata import unappend_data, append_data, find_shape
from .fdata import pipe_2d, pipe_3d, pipestream_3d, pipe_4d, pipestream_4d
from .fdata import fdata_nums, fdata_dic
from .DataFrame import DataFrame

fdata = [get_fdata, fdata2dic, dic2fdata, get_fdata_data, reshape_data, unshape_data,
         unappend_data, append_data, find_shape, pipe_2d, pipe_3d,
         pipestream_3d, pipe_4d, pipestream_4d]

err = [PipeBurst, FileIOError, FunctionError, catchError]

df = [DataFrame]

all = ['fdata_dic','fdata_nums']
all.extend(m.__name__ for m in fdata)
all.extend(m.__name__ for m in err)
all.extend(m.__name__ for m in df)

__all__ = all