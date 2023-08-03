import numpy as np

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
from lab_devices.conifg.config_handler import update_config

import utils.plot_fit as pltfit
from host.bode_plot_analyzer import analyse_bode_plot
import utils.data_handler as data_handler
from utils.initialize_measurement import initialize_measurement as init_meas
import matplotlib.pyplot as plt
import yaml
import sys
import time
    
import logging
from lab_devices.conifg.config_handler import update_config

from bitarray import bitarray
from lab_devices.sourcemeter import sourcemeter
import utils.pulse_analyzer as pa 
from scipy.stats import norm
import matplotlib.mlab as mlab
import random as ran

load_data, chip_version, image_path, data_path = init_meas('IR_LED')
if not load_data:
    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.boot_seq()
    
    if chip_version == 'AC':
        dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=dut.get_DC_offset(chip_version=chip_version), print_out=True, opAMP_offset=0.5)
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage())
        print('ADC_REF:' , dut['ADC_REF'].get_voltage())
    else:
        dut.load_defaults(VRESET=0, DIODE_HV=dut.get_DC_offset(chip_version=chip_version), print_out=True, opAMP_offset=0.5)
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage(),'V')
    print('0')
    dut['CONTROL'] =0x1 # Select Matrix 
    dut['CONTROL'].write()  

    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()
    sm.settings(voltage=0, current_limit=400*1e-6)
    sm['sourcemeter'].set_current_autorange()

    try:
        sm_back_bias = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
        sm_back_bias.init()
        sm_back_bias.pixel_depletion(PW_BIAS=0, current_limit=400*1e-6, voltage_limit=-10)
        sm_back_bias['sourcemeter'].set_current_autorange()
    except:
        print('No SMU for back bias connected')

    try:
        sm_DIODE_HV = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_3.yaml", 'r'), Loader=yaml.Loader))
        sm_DIODE_HV.init()
        sm_DIODE_HV.settings(voltage=0, current_limit=350*1e-6, voltage_limit=3)
        smu_HV = True
    except:smu_HV = False


    #while True:
    #    dut.single_signal_SEQ(overhead=100, delta_trigger=0)
    #    time.sleep(0.1)

def configure_setup():
    while True:
        print('\n------------------\ncurrent config:\nDIODE_HV=%.2f, PW_BIAS=%s, BACK_BIAS=%s, opAmpOffset=%s'%(dut['DIODE_HV'].get_voltage(),sm['sourcemeter'].get_voltage(),sm_back_bias['sourcemeter'].get_voltage(), dut['opAMP_offset'].get_voltage()))
        user_in = input('>')
        if 'HV=' in user_in:
            if smu_HV:
                sm_DIODE_HV['sourcemeter'].set_voltage(float(user_in[3:]))
            else:
               dut['DIODE_HV'].set_voltage(float(user_in[3:]))
        if 'PW=' in user_in:
            sm['sourcemeter'].set_voltage(float(user_in[3:]))
        if 'BB=' in user_in:
            sm_back_bias['sourcemeter'].set_voltage(float(user_in[3:]))
        if 'op=' in user_in:
            dut['opAMP_offset'].set_voltage(float(user_in[3:]))


configure_setup()