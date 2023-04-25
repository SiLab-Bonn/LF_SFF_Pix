
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

    #for i in range(0,250):
    #    dut['SEQ']['RESET'][i]=0
    #for i in range(250, 500):
    #    dut['SEQ']['RESET'][i]=1

    #for i in range(0,250):
    #    dut['SEQ']['SEQ3'][i]=0
    #for i in range(250, 500):
    #    dut['SEQ']['SEQ3'][i]=1

    #dut.init_adc(10)
    #dut.get_adc()

    adc_ch = 'fadc1_rx'
    dut[adc_ch].reset()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].set_data_count(10)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_en_trigger(False)
        
    dut['DATA_FIFO'].reset()

    for i in range(10):
        pattern = 10 + i * 100
        dut['fadc_conf'].enable_pattern(pattern)  

        dut[adc_ch].start()
        while not dut[adc_ch].is_done():
            pass

        lost = dut[adc_ch].get_count_lost()
        data = dut['DATA_FIFO'].get_data() 
        print(data)
        data = data & 0x3fff

        if data.tolist() != [pattern]*10 or lost !=0 :
            logging.error("Wrong ("+str(hex(pattern))+") or lost data :" + str(data) + " Lost: " + str(lost))
        else:
            logging.info("OK Data:" + str(data) + " Lost: " + str(lost))

"""
    dut['SEQ'].set_size(500)
    dut['SEQ'].write()
    dut['SEQ'].start()
    print('HELLO 1')
    dut['OUT_1'].set_align_to_sync(True)
    print('Hello2')
    dut['OUT_1'].set_data_count(16)
    dut['OUT_1'].set_single_data(True)
    print('Hello3')
    
    dut['DATA_FIFO'].reset()
    dut['OUT_1'].start()
    data = dut['DATA_FIFO'].get_data()
    print(data)
    print(len(data))
    plt.scatter(np.linspace(0, len(data), len(data)),data, linestyle='None', marker='.')
    plt.show()
"""


SEQ_test()
