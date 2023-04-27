
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


pulse_width = 200*1e-6


dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()

dut.boot_seq()
dut.load_defaults()

func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
func_gen.init()
func_gen.load_IR_LED_ext_config(1.5, pulse_width, 1/pulse_width)

for i in range(0,int(pulse_width/0.1*1e6)): # 1 unit = 0.1us
    dut['SEQ']['Trigger'][i]=1
    #dut['SEQ']['RESET'][i]=0

for i in range(int(pulse_width/0.1*1e6), int(pulse_width/0.1*1e6)*2):
    dut['SEQ']['Trigger'][i]=0
    #dut['SEQ']['RESET'][i]=1

dut['SEQ'].set_size(pulse_width/0.1*1e6*2)
dut['SEQ'].write()
dut['SEQ'].start()



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
        data = data & 0x3fff
        if data.tolist() != [pattern]*10 or lost !=0 :
            logging.error("Wrong ("+str(hex(pattern))+") or lost data :" + str(data) + " Lost: " + str(lost))
        else:
            logging.info("OK Data:" + str(data) + " Lost: " + str(lost))

def read_adc(nSamples, adc_ch):
    '''dut['sram'].reset()
    dut[adc_ch].reset()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].set_data_count(nSamples)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_en_trigger(False)
    time.sleep(2)

    dut[adc_ch].start()
    while not dut[adc_ch].is_done():
        pass

    lost = dut[adc_ch].get_count_lost()
    data = dut['sram'].get_data() 
    data = data & 0x3fff'''
    data = dut.read_raw_adc(nSamples, adc_ch)
    plt.plot(data, label=adc_ch, alpha=0.5)

#for adc in ['fadc0_rx']:#,'fadc1_rx','fadc2_rx','fadc3_rx']:
#    read_adc(1000000, adc)
#plt.legend()
#plt.show()

def calibrate_adc(adc_ch, nSamples = 1):
    pass
read_adc_testpattern()
