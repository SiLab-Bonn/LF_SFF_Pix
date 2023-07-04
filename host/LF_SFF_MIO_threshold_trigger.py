import time
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
        dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=dut.get_DC_offset(chip_version=chip_version))
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage())
        print('ADC_REF:' , dut['ADC_REF'].get_voltage())
    else:
        dut.load_defaults(VRESET=0, DIODE_HV=dut.get_DC_offset(chip_version=chip_version))
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage(),'V')
    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()
    sm.pixel_depletion(PW_BIAS=-3)

    #func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    #func_gen.init()
    #pulse_width = 100*1e-9 #int(1/pulse_width*0.1)
    #func_gen.load_IR_LED_ext_config(3.0, pulse_width, 10)


def demo_threshold_trigger(adc_ch='fadc0_rx', nSamples = 4096):
    dut.reset()
    dut[adc_ch].reset()
    dut['sram'].reset()
    
    dut[adc_ch].set_data_count(nSamples)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_threshold_trigger_value(1)
    dut[adc_ch].set_threshold_trigger(3)
    print('THRESHOLD MODE: ', dut[adc_ch].get_threshold_trigger_mode())
    print(dut[adc_ch].get_threshold_trigger_value())
    while True:
        print('check:',dut[adc_ch].get_threshold_trigger_feedback())
    time.sleep(5)
    dut['sram'].reset()
    while not dut[adc_ch].is_done():
        pass
    i = 1
    while dut['sram'].get_FIFO_INT_SIZE()<=nSamples-1:
        print(dut['sram'].get_FIFO_INT_SIZE())
    lost = dut[adc_ch].get_count_lost()
    data = dut['sram'].get_data() 
    data = data & 0x3fff
    plt.plot(data)
    plt.show()

demo_threshold_trigger()