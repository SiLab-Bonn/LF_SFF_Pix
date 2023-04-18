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

import utils.plot_fit as pltfit
from host.bode_plot_analyzer import analyse_bode_plot
import utils.data_handler as data_handler
from utils.initialize_measurement import initialize_measurement as init_meas
import matplotlib.pyplot as plt
import yaml
import sys
import time

image_format = '.pdf'

def gen_pulse(dut, func_gen):
    #dut.reset(0.25)
    func_gen.send_trigger()
    time.sleep(0.25)

def IR_LED(frequency, pulse_width, CH2_DC):
    dut_config = update_config('./lab_devices/conifg/LF_SFF_IR_LED.csv')

    # Instantiate devices and initialize measurement setting
    load_data, chip_version, image_path, data_path = init_meas('IR_LED')

    oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_tds_3034b.yaml", 'r'), Loader=yaml.Loader))
    oszi.init()
    oszi.load_IR_LED_config(frequency=frequency, CH2_DC=CH2_DC)

    func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    func_gen.init()
    if chip_version == 'AC': func_gen.load_IR_LED_config(voltage_high=1.5, frequency=frequency, pulse_width=pulse_width)
    else: func_gen.load_IR_LED_config(voltage_high=2.2, frequency=frequency, pulse_width=pulse_width)
    IBP_end_of_dynamic_area = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBP_end_of_dynamic_area.csv', delimiter=',')
    IBN_end_of_dynamic_area = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBN_end_of_dynamic_area.csv', delimiter=',')
    DC_offset = np.average([IBP_end_of_dynamic_area[1][1],IBN_end_of_dynamic_area[1][1]])
    
    try:
        dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
        dut.init()

        dut.boot_seq()
        dut.set_acquire_state('RUN')
        dut['DIODE_HV'].set_voltage(1, unit='V')

    except:
        print('Firmware not flashed. This can be because a firmware was already flashed or your setup is broken')
        exit
    """dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.boot_seq()"""

    if DC_offset <=1.2:
        dut.load_defaults(VRESET = DC_offset)
    
    # Test trigger
    #for i in range(0,10):

    while True:
        dut_config.check_config(dut)
        gen_pulse(dut, func_gen)
        #ch1 = oszi['Oscilloscope'].get_waveform(channel=1, continue_meas=False)
        #ch2 = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
        #pltfit.beauty_plot_two_y_scales(x=oszi.gen_waveform_x(waveform=ch2),data2=ch1[1], data1=ch2[1],xlabel='time / s', ylabel2='Voltage / V', ylabel1='Voltage / V', label2='Function Generator', label1='LF SFF', alpha1=1, alpha2=0.7, show=False, image_path=image_path+'test_sample_'+str(i)+image_format, title='Test Pulse')


IR_LED(frequency=10, pulse_width=10e-6,CH2_DC=True)
