
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
dut.load_defaults()

func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
func_gen.init()

def test_SEQ():
    pulse_width = 200*1e-6


    dut.boot_seq()
    dut.load_defaults()



    for i in range(0,int(pulse_width/0.1*1e6)): # 1 unit = 0.1us
        dut['SEQ']['Trigger'][i]=1
        #dut['SEQ']['RESET'][i]=0

    for i in range(int(pulse_width/0.1*1e6), int(pulse_width/0.1*1e6)*2):
        dut['SEQ']['Trigger'][i]=0
        #dut['SEQ']['RESET'][i]=1

    dut['SEQ'].set_size(pulse_width/0.1*1e6*2)
    dut['SEQ'].write()
    dut['SEQ'].start()





def read_adc_testpattern(adc_ch):
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
    data = dut.read_raw_adc(nSamples, adc_ch)
    plt.plot(data, label=adc_ch, alpha=0.5)


def adc_test_offset(adc_ch='fadc0_rx'):
    freq = 1e3
    nSamples = 15000
    offset_list = [0.2,0.4,0.6,0.8,1.0, 1.2]
    colors = ['red', 'orange', 'purple', 'green', 'blue', 'navy']
    i = 0
    pltfit.beauty_plot(xlim=[0, nSamples])
    for offset in offset_list:
        dut['ADC_REF'].set_voltage(offset)
        func_gen.adc_test_config(0.2,dut['ADC_REF'].get_voltage(),1e3)
        data = dut.read_raw_adc(nSamples, adc_ch)
        data_max = np.max(data[100:-100])
        data_min = np.min(data[100:-100])
        data_avrg = (data_max-data_min)/2+data_min
        plt.plot(data, alpha= 0.7, label='ADC_REF='+str(offset)+'V, meas: '+str(np.round(dut['ADC_REF'].get_voltage(),3))+'V, funcgen offset='+str(np.round(float(func_gen['Pulser'].get_voltage_offset()),3))+'V, measured offset= '+str(round(data_avrg,0)) +', $V_{pp}$='+str(data_max-data_min),color=colors[i])
        plt.hlines(8000,-1e10,+1e10, colors='black')
        plt.hlines(data_avrg, -1e6, 1e6, alpha=0.5, color=colors[i], linestyles='--')
        i+=1
        print('Calibration:', 0.1/(data_max-data_min), 'V/Unit')
    plt.legend()
    plt.savefig('ADC_offset_test.pdf')
    plt.show()

#for adc in ['fadc0_rx']:#,'fadc1_r
# x','fadc2_rx','fadc3_rx']:
#    read_adc(1000000, adc)
#plt.legend()
#plt.show()
#for adc_ch in ['fadc0_rx','fadc1_rx','fadc2_rx','fadc3_rx']:
#    read_adc_testpattern(adc_ch)
adc_test_offset('fadc3_rx')