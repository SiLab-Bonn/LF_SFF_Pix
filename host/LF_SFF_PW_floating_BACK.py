# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------


from os import walk
import numpy as np
from utils.initialize_measurement import initialize_measurement as init_meas
import matplotlib.pyplot as plt
import utils.pulse_analyzer as pa
import utils.data_handler as data_handler
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import utils.plot_fit as pltfit
from lab_devices.sourcemeter import sourcemeter
import time

def back_bias_floating(PWELL_selection=[]):
    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()
    oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_MSO54.yaml", 'r'), Loader=yaml.Loader))
    oszi.init() 
    back_bias = []
    for PW_BIAS in PWELL_selection:
        sm.pixel_depletion(PW_BIAS=PW_BIAS, current_limit=300*1e-6)
        CH4 = oszi['Oscilloscope'].get_waveform(channel=4, continue_meas=True)
        back_bias.append(np.average(CH4[1]))
        time.sleep(1)

    pltfit.beauty_plot(xlabel='PW_BIAS / V', ylabel='floating BACK_BIAS / V')
    plt.plot(PWELL_selection, back_bias, marker='x', linestyle='None')
    plt.savefig('./output/miscellaneous/BACK_BIAS_floating_PWELL_dependence.pdf', bbox_inches='tight')
    plt.show()
    data_handler.save_data(data=[PWELL_selection, back_bias], header='PWELL_selection, back_bias', output_path='./output/miscellaneous/data/back_floating.csv')

back_bias_floating(PWELL_selection=[0, -1,-1.5,-2,-2.5,-3,-3.5,-4,-4.5,-5,-5.5,-6])
