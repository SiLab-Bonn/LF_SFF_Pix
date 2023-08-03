# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#
# This script tests if one can deplete the AC coupled chip just by applying a positive 
# voltage to DIODE_HV while PW_BIAS and BACK_BIAS are at GND
#
# CHECK BEFORE YOU START THIS SCRIPT, IF THE SMU IS CONNECTED TO DIODE_HV!!!!
#

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import matplotlib.pyplot as plt
from lab_devices.sourcemeter import sourcemeter
import time
import utils.plot_fit as pltfit
import numpy as np

sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm.init()
sm.setttings(voltage=+3, current_limit=300*1e-6)

dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()
dut.boot_seq()
dut.load_defaults(VRESET = dut.get_DC_offset(chip_version='AC'))

def configure_setup():
    while True:
        print('\n------------------\ncurrent config: DIODE_HV=%s, opAmpOffset=%s'%(sm['sourcemeter'].get_voltage(), dut['opAMP_offset'].get_voltage()))
        user_in = input('>')
        if 'HV=' in user_in:
            sm['sourcemeter'].set_voltage(float(user_in[3:]))
        if 'op=' in user_in:
            dut['opAMP_offset'].set_voltage(float(user_in[3:]))
        if 'reset' in user_in:
            dut.reset()


configure_setup()