
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




dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()

dut.boot_seq()
dut.load_defaults()

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
# dut['SEQ']['Trigger'][i]=0
dut['SEQ'].set_size(500)
dut['SEQ'].write()
dut['SEQ'].start()


dut['CONTROL']['RESET']=0x0
dut['CONTROL']['SEL0']=0x0
dut['CONTROL']['SEL1']=0x0
dut['CONTROL']['SEL2']=0x0
dut['CONTROL']['LED5']=0x0
dut['CONTROL'].write()
time.sleep(0.5)
dut['CONTROL']['RESET']=0x1
dut['CONTROL']['SEL0']=0x1
dut['CONTROL']['SEL1']=0x1
dut['CONTROL']['SEL2']=0x1
dut['CONTROL']['LED5']=0x1
dut['CONTROL'].write()
time.sleep(0.5)


adc_ch = 'fadc0_rx'

def read_adc_testpattern():
    dut['sram'].reset()
    dut[adc_ch].reset()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].set_data_count(10)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_en_trigger(False)

    for i in range(10):
        pattern = 10 + i * 100
        dut['fadc_conf'].enable_pattern(pattern)  

        dut[adc_ch].start()
        while not dut[adc_ch].is_done():
            pass

        lost = dut[adc_ch].get_count_lost()
        data = dut['sram'].get_data() 
        print([hex(i) for i in data])
        data = data & 0x3fff
        print([hex(i) for i in data])
        if data.tolist() != [pattern]*10 or lost !=0 :
            logging.error("Wrong ("+str(hex(pattern))+") or lost data :" + str(data) + " Lost: " + str(lost))
        else:
            logging.info("OK Data:" + str(data) + " Lost: " + str(lost))

def read_adc(nSamples):
    dut['sram'].reset()
    dut[adc_ch].reset()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].set_data_count(nSamples)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_en_trigger(False)

    dut[adc_ch].start()
    while not dut[adc_ch].is_done():
        pass

    lost = dut[adc_ch].get_count_lost()
    data = dut['sram'].get_data() 
    data = data & 0x3fff
    plt.plot(data)
    plt.show()

#read_adc(19)
read_adc_testpattern()
