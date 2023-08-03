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

   
        
    #################################
    # General measurement methods
    #################################
        # Generates x values for a taken waveform measurement (We only know the number of dots and the scale width)
    def gen_waveform_x(self, waveform):
        return np.linspace(0, waveform[2][0]*len(waveform[1]),len(waveform[1]))