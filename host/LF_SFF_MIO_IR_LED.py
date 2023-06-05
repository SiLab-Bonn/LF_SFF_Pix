# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                                 Function Generator________
#                                           |               |
#                                           | RS232         |
# -----------------------                   |               |
# | MIO | GPIO | LF_SFF |       MIO------Computer           |
# -----------------------            USB    |               |
#        Pixel 10  |                        | RJ45          |
#        Matrix 1  |                        |               |
#                  |______________________Oszi______________|__________IR-LED
#                            CH2                   CH1
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
#
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
# The function generator is also completely controlled by this script. 
# Please verify that the IR-LED is connected with the right polarity:
#
#       ###
#      #   #
#      #   #
#      #####
#       # #
#       # #
#       # #
#       # #
#       # # GND
#       #
#


import time
import numpy as np

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
from lab_devices.conifg.config_handler import update_config
from lab_devices.sourcemeter import sourcemeter
from utils.initialize_measurement import initialize_measurement as init_meas
import utils.plot_fit as pltfit
import utils.data_handler as data_handler
import matplotlib.pyplot as plt
import yaml
import sys
import time
from bitarray import bitarray
import utils.data_handler as dh
import utils.pulse_analyzer as pa 

load_data, chip_version, image_path, data_path = init_meas('IR_LED')

def SEQ(dut, overhead, delta_trigger):
    dut['SEQ'].reset()
    dut['SEQ'].set_clk_divide(1)
    reset       = bitarray('0'+'0'*delta_trigger+'0'*overhead)
    trigger     = bitarray('0'*delta_trigger+'1'+'0'*overhead)
    adc_trigger = bitarray('1'+'0'*delta_trigger+'0'*overhead)

    seq_size  = len(trigger)
    dut['SEQ'].set_repeat_start(0) 
    dut['SEQ'].set_repeat(1)  # else records many events
    dut['SEQ'].set_size(len(adc_trigger))
    dut['SEQ']['RESET'][0:len(trigger)] =  reset
    dut['SEQ']['Trigger'][0:len(trigger)] =  trigger
    dut['SEQ']['ADC_Trigger'][0:len(trigger)] = adc_trigger
    dut['SEQ'].write()
    dut['SEQ'].start()



def fast_offline_event_analysis(dut, n_events):
    nSamples=4096
    delta_trigger = 100
    overhead = nSamples

    data_idle = []
    for i in range(n_events): # no events capture
        print('idle data: %i/%i'%(i+1,n_events))
        data_meas = dut.read_raw_adc(nSamples=nSamples, adc_ch='fadc0_rx')
        data_idle.append(np.average(data_meas))
    data_event = []
    for i in range(n_events):
        print('event data: %i/%i'%(i+1,n_events))
        time.sleep(1)
        data_evt_meas, err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead, calibrate_data=False)
        data_event.append(pa.fast_online_analysis(data=data_evt_meas, baseline=np.average(data_evt_meas[:delta_trigger])))

    pltfit.beauty_plot()
    plt.hist(data_idle, label='no pulses')
    plt.hist(data_event, label='with pulsees')
    plt.legend()
    plt.savefig(image_path+'demo_fast_offline_event_analysis.pdf')
    plt.show()


def find_baseline(dut):
    pass

def fast_online_analysis(dut, n_events):
    nSamples=4096
    delta_trigger = 100
    overhead = nSamples
    captured_events = 0 
    event_found=False
    baseline = find_baseline(dut)
    events = []
    while True:
        data = dut.read_raw_adc(nSamples=nSamples, adc_ch='fadc0_rx')
        event = pa.fast_online_analysis(data)
        if event!=-1:
            captured_events+=1
            events.append(event)
        if captured_events == n_events:
            break
        
        


def IR_LED(n_events):
    if not load_data:
        dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
        dut.init()
        dut.boot_seq()
        dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=1.8)

        func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
        func_gen.init()

        sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
        sm.init()
        sm.pixel_depletion(PW_BIAS=-0.5)
    
        analysis_type = 'offline'
        if 'online' in sys.argv[1:]:
            analysis_type = 'online'
        
        if analysis_type == 'offline':
            data = fast_offline_event_analysis(dut, n_events)
        else:
            data = fast_online_analysis(dut, n_events)

    else:
        pass

IR_LED(n_events=100)


#
# Ideen fuer den Online analyzer:
# 1. periodisches lesen des ADCs und hoffen, dass was aufgenommen wird
# 2. firmware ADC schreibt beim ueberschreiten eines schwellwertes
# 3. 
#
#
