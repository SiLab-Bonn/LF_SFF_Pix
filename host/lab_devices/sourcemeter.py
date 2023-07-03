from basil.dut import Dut
import sys
sys.path.append("../")
import utils.plot_fit as pltfit 
import numpy as np
import matplotlib.pyplot as plt
import time

class sourcemeter(Dut):
    def pixel_depletion(self, PW_BIAS=-3):
        if PW_BIAS <= 0:
            self['sourcemeter'].set_voltage(PW_BIAS)
            self['sourcemeter'].set_voltage_limit(-6)
            self['sourcemeter'].set_current_limit(10*1e-6)
            self['sourcemeter'].on()
            print('SET PW_BIAS to ', self['sourcemeter'].get_voltage(), 'V')
        else:
            print('WARNING!!! YOU ARE TRYING TO APPLY A POSITIVE PWELL_BIAS!!!')
        