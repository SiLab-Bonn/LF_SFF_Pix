from basil.dut import Dut
import sys
sys.path.append("../")
import utils.plot_fit as pltfit 
import numpy as np
import matplotlib.pyplot as plt
import time

class sourcemeter(Dut):

    def settings(self, voltage=-3, voltage_limit=-6, current_limit=100*1e-6):
            self['sourcemeter'].set_voltage_limit(voltage_limit)
            self['sourcemeter'].set_current_limit(current_limit)
            self['sourcemeter'].set_voltage(voltage)
            self['sourcemeter'].on()
            print('SET voltage to ', self['sourcemeter'].get_voltage(), 'V')
            
    def pixel_depletion(self, PW_BIAS=-3, voltage_limit=-12, current_limit=100*1e-6):
        '''if PW_BIAS <= 0:
            self['sourcemeter'].set_voltage_limit(voltage_limit)
            self['sourcemeter'].set_current_limit(current_limit)
            self['sourcemeter'].set_voltage(PW_BIAS)
            self['sourcemeter'].on()
            print('SET PW_BIAS to ', self['sourcemeter'].get_voltage(), 'V')
        else:
            print('WARNING!!! YOU ARE TRYING TO APPLY A POSITIVE PWELL_BIAS!!!')
        '''
        self.settings(voltage=PW_BIAS, voltage_limit=voltage_limit, current_limit=current_limit)


         