
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

dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()
dut.boot_seq()

dut.load_defaults(VRESET=0)

func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
func_gen.init()

def test_SEQ(dut, overhead):
    
    dut['SEQ'].reset()
    dut['SEQ'].set_clk_divide(1)

    reset       = bitarray('0000000000000000000000000')
    trigger     = bitarray('0000000100000000000000000')
    adc_trigger = bitarray('0100000000000000000000000')
    seq_size  = len(trigger)
    dut['SEQ'].set_repeat_start(0) 
    dut['SEQ'].set_repeat(0) 
    dut['SEQ'].set_size(seq_size+overhead)
    dut['SEQ']['RESET'][0:len(trigger)] =  reset
    dut['SEQ']['Trigger'][0:len(trigger)] =  trigger
    dut['SEQ']['ADC_Trigger'][0:len(trigger)] = adc_trigger
    dut['SEQ'].write()
    dut['SEQ'].start()

def read_adc(nSamples, adc_ch):
    data = dut.read_adc(nSamples, adc_ch)
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

def test_read_pulse():
    pulse_width = 0.3*1e-6
    test_SEQ(pulse_width)
    func_gen.load_IR_LED_ext_config(1.8, pulse_width, int(1/pulse_width*0.1))
    time.sleep(1)
    pltfit.beauty_plot(tight=False)
    for adc_ch in ['fadc0_rx','fadc1_rx','fadc2_rx','fadc3_rx']:
        data, data_err = dut.read_adc(adc_ch=adc_ch, nSamples=10000)
        plt.plot(data, label=adc_ch)
    plt.legend()
    plt.show()
    dut_config = update_config('./lab_devices/conifg/LF_SFF_SEQ_ADC_test.csv')

    while True:
        dut_config.check_config(dut)

#test_read_pulse()
def read_test_input(adc_ch = 'fadc0_rx'):
    dut[adc_ch].reset()
    dut['sram'].reset()
    dut[adc_ch].set_data_count(100)
    dut[adc_ch].set_en_trigger(True)
    test_SEQ()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].start()
    while not dut[adc_ch].is_done():
        pass
    data = dut['sram'].get_data() 
    data = data & 0x3fff
    plt.plot(data)
    plt.show()

def demo_capture_one_event():
    pltfit.beauty_plot(tight=False)
    data, data_err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=40000)
    plt.plot(data)
    plt.show()
demo_capture_one_event()
dut.close()
