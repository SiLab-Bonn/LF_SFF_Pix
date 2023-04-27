# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#             ________________ Function Generator
#            | |                       |               
#     ADC[0] | | ADC_0                 | RS232         
# --------------                       |               
# | MIO | GPIO |          MIO------Computer           
# --------------          
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
# If you can't see a trigger at 100Hz like in the picture below, restart the script, until it triggers correctly
#
#  /__________________________________/
#  |Tektronix TDS3034B                |
#  |   ___________________________    |
#  |  |                           | o |
#  |  | ~~~~~~~~~~~~~~\ |~~~~~~~~~| o |
#  |  | ---------------\|---------| o |
#  |  |___________________________| o |
#  |                CH1 o    CH2 o    | /
#  |_________________________________ |/
#
# The function generator is also completely controlled by this script except the function form. Set it to SINE. 
# Please verify BEFORE plugging it into the PIX_INPUT of the LFSFF Board that the Ampl and Offset are not larger 
# than Vpp=100mV and Voff=650mV.
#

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.function_generator import function_generator
import matplotlib.pyplot as plt
import yaml
import numpy as np


# This script automatically calibrates the ADC on the GPAC Card by applying external voltages and reading them in

def calibrate_ADC():
    nSamples = 10000
    offset = 0.7
    #func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    #func_gen.init()

    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.load_defaults()
    dut['VDD'].set_enable(True)


    dut['ADC_REF'].set_voltage(offset)
    #for adc_ch in ['fadc0_rx']:#,'fadc1_rx','fadc2_rx','fadc3_rx']:    
        #input('Plug in %s and enter something to continue'%(adc_ch))
        #for V in [0.1, 0.2, 0.3, 0.4, 0.5]:
            #func_gen.calibrate_conf_config(V, offset, pulse_width, 1/pulse_width)
    data = dut.read_raw_adc(nSamples, 'fadc0_rx')
    plt.plot(data, label=str(offset))
    offset = 0.6
    dut['ADC_REF'].set_voltage(offset)
    data = dut.read_raw_adc(nSamples, 'fadc0_rx')
    plt.plot(data, label=str(offset))


    plt.legend()
    plt.show()

calibrate_ADC()