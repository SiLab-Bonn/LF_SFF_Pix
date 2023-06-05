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
from lab_devices.sourcemeter import sourcemeter
import utils.pulse_analyzer as pa 

load_data, chip_version, image_path, data_path = init_meas('IR_LED')
dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()
dut.boot_seq()
dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=1.8)

print(dut.get_DC_offset(chip_version='DC'))