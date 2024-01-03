from .function import nmrFunction as Function

class Transpose(Function):
    def __init__(self, data,
                tp_noOrd: bool = False, tp_exch : bool = False,
                tp_minMax: bool = True, params : dict = {}):
        
        self.tp_noOrd = tp_noOrd
        self.tp_exch = tp_exch
        self.tp_minMax = tp_minMax

        params.update({'tp_noOrd':tp_noOrd,
                  'tp_exch':tp_exch,'tp_minMax':tp_minMax,})
        super().__init__(data, params)
    
    def run(self):
        pass

class Transpose2D(Transpose):
    def __init__(self, data,
                 tp_hyper : bool = True, tp_auto: bool = True,
                 tp_nohdr : bool = False, tp_noOrd: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = True):
        self.tp_hyper = tp_hyper
        self.tp_auto = tp_auto
        self.tp_nohdr = tp_nohdr

        params = {'tp_hyper':tp_hyper,'tp_auto':tp_auto,
                  'tp_nohdr':tp_nohdr}
        super.__init__(data, tp_noOrd, tp_exch, tp_minMax, params)

class Transpose3D(Transpose):
    def __init__(self, data, tp_noOrd: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = True):
        super().__init__(data, tp_noOrd, tp_exch, tp_minMax)

class Transpose4D(Transpose):
    def __init__(self, data, tp_noOrd: bool = False,
                 tp_exch : bool = False, tp_minMax: bool = True):
        super().__init__(data, tp_noOrd, tp_exch, tp_minMax)