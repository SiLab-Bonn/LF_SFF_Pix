
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
    




def SEQ_test():
    
    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()

    dut.boot_seq()
    dut.load_defaults()
    #dut['DIODE_HV'].set_voltage(1, unit='V')
    
    dut['SEQ'].clear()
    dut['SEQ'].init()
  
    for i in range(0,250):
        dut['SEQ']['Trigger'][i]=1
    for i in range(250, 500):
        dut['SEQ']['Trigger'][i]=0
    
    for i in range(0,250):
        dut['SEQ']['RESET'][i]=0
    for i in range(250, 500):
        dut['SEQ']['RESET'][i]=1

    #for i in range(0,250):
    #    dut['SEQ']['SEQ3'][i]=0
    #for i in range(250, 500):
    #    dut['SEQ']['SEQ3'][i]=1

    dut['SEQ'].set_size(500)
    dut['SEQ'].write()
    dut['SEQ'].start()
    time.sleep(0.5)
    data = dut.take_adc_data('OUT_0',10)[0]
    plt.scatter(np.linspace(0, len(data), len(data)),data, linestyle='None', marker='.')
    plt.show()
    data = dut.take_adc_data('OUT_1')[0]
    plt.scatter(np.linspace(0, len(data), len(data)),data, linestyle='None', marker='.')
    plt.show()
    data = dut.take_adc_data('OUT_2')[0]
    plt.scatter(np.linspace(0, len(data), len(data)),data, linestyle='None', marker='.')
    plt.show()
    data = dut.take_adc_data('OUT_3')[0]
    plt.scatter(np.linspace(0, len(data), len(data)),data, linestyle='None', marker='.')
    plt.show()
SEQ_test()
