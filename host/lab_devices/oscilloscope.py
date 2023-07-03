from basil.dut import Dut
import sys
sys.path.append("../")
import utils.plot_fit as pltfit 
import numpy as np
import matplotlib.pyplot as plt
import time

class oscilloscope(Dut):

    #################################
    # Configs for experiments
    #################################

    def load_dc_sweep_config(self):
        self['Oscilloscope'].set_horizontal_scale(200e-6)
        self['Oscilloscope'].set_vertical_scale('2.0E-1',channel=1)
        self['Oscilloscope'].set_vertical_scale('200.0E-3',channel=2)
        self['Oscilloscope'].set_vertical_position('-2.0E0',channel=2)
        self['Oscilloscope'].set_vertical_position('-3.0E0',channel=1)
        self['Oscilloscope'].set_vertical_offset('0.0E0', channel=1)
        self['Oscilloscope'].set_coupling('DC', channel=1)
        self['Oscilloscope'].set_coupling('DC', channel=2)
        self['Oscilloscope'].set_acquire_state('RUN')
        time.sleep(2)

    def load_ac_sweep_config(self):
        self['Oscilloscope'].set_horizontal_scale(200e-6)
        self['Oscilloscope'].set_vertical_scale('50.0E-3',channel=1)
        self['Oscilloscope'].set_vertical_scale('50.0E-3',channel=2)
        self['Oscilloscope'].set_vertical_position('20E-3',channel=2)
        self['Oscilloscope'].set_vertical_position('-2.0E0',channel=1)
        self['Oscilloscope'].set_vertical_offset('0.0E0', channel=1)
        self['Oscilloscope'].set_coupling('AC', channel=1)
        self['Oscilloscope'].set_coupling('AC', channel=2)
        self['Oscilloscope'].set_trigger_source(channel=1)
        self['Oscilloscope'].set_trigger_level(-12e-3)
        self['Oscilloscope'].set_acquire_state('RUN')

        time.sleep(2)

    def load_IR_LED_config(self, frequency, CH2_DC):
        self['Oscilloscope'].set_horizontal_scale(20*1e-3)
        self['Oscilloscope'].set_vertical_scale('1',channel=1)
        self['Oscilloscope'].set_vertical_scale('100e-3',channel=2)
        self['Oscilloscope'].set_vertical_position('-2.0E0',channel=1)
        self['Oscilloscope'].set_vertical_position('2.28E0',channel=2)
        self['Oscilloscope'].set_vertical_offset('0.0E0', channel=1)
        self['Oscilloscope'].set_coupling('DC', channel=1)
        self['Oscilloscope'].set_coupling('AC', channel=2)
        self['Oscilloscope'].set_trigger_source(channel=1)
        self['Oscilloscope'].set_trigger_level(600e-3)
        self['Oscilloscope'].set_trigger_mode('NORM')
        self['Oscilloscope'].set_trigger_type('EDG')
        self['Oscilloscope'].set_acquire_state('RUN')
        if CH2_DC:
            self['Oscilloscope'].set_coupling('DC', channel=2)
            self['Oscilloscope'].set_vertical_position('-5.0E0',channel=2)
       

    def load_PWELL_VRESET_conifg(self):
        self['Oscilloscope'].set_horizontal_scale(200e-6)
        self['Oscilloscope'].set_vertical_scale('200.0E-3',channel=2)
        self['Oscilloscope'].set_vertical_position('0',channel=2)
        self['Oscilloscope'].set_coupling('DC', channel=2)
        self['Oscilloscope'].set_acquire_state('RUN')
        time.sleep(2)

        
    #################################
    # General measurement methods
    #################################

        
    def get_cos_fit(self,frequency, channel=1, continue_meas=True):
        meas = self['Oscilloscope'].get_waveform(channel=channel, continue_meas=continue_meas)
        y = meas[1]
        x = np.linspace(0,meas[2][0]*len(y),len(y))
        p_approx = pltfit.guess_cos_params(y,frequency)
        popt, perr =  pltfit.fit_no_err(function=pltfit.func_cos, x=x, y=y, presets=p_approx)
        return popt, perr

    
    # Generates x values for a taken waveform measurement (We only know the number of dots and the scale width)
    def gen_waveform_x(self, waveform):
        return np.linspace(0, waveform[2][0]*len(waveform[1]),len(waveform[1]))

