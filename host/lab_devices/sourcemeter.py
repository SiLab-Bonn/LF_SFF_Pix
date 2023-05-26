from basil.dut import Dut
import sys
sys.path.append("../")
import utils.plot_fit as pltfit 
import numpy as np
import matplotlib.pyplot as plt
import time

class sourcemeter(Dut):
    def test(self):
        print('HELLO THERE')

    def pixel_depletion(self, PW_BIAS=-3):
        self['sourcemeter'].set_voltage(PW_BIAS)
        self['sourcemeter'].set_voltage_limit(-4)
        self['sourcemeter'].set_current_limit(1e-6)
        self['sourcemeter'].on()
        print('SET PW_BIAS to ', self['sourcemeter'].get_voltage(), 'V')
        