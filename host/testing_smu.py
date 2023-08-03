from lab_devices.multimeter import multimeter
import yaml
from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import matplotlib.pyplot as plt
from lab_devices.sourcemeter import sourcemeter
from lab_devices.multimeter import multimeter
import time
import utils.plot_fit as pltfit
import numpy as np
from utils.initialize_measurement import initialize_measurement as init_meas
print('DUT start')

#dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
#dut.init()
#dut.boot_seq()
#dut.load_defaults(VRESET = dut.get_DC_offset(chip_version='AC'))

print('SMU0 start')
sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm.init()
sm.settings(voltage=1, current_limit=350*1e-6)
print('SMU0')
time.sleep(2)
print('SMU1 start')

sm_back_bias = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
sm_back_bias.init()
sm_back_bias.settings(voltage=2, current_limit=350*1e-6, voltage_limit=-12)
print('SMU1')
time.sleep(2)
print('SMU2 start')

sm_x = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_3.yaml", 'r'), Loader=yaml.Loader))
sm_x.init()
sm_x.settings(voltage=3, current_limit=350*1e-6, voltage_limit=3)

sm_GND = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_4.yaml", 'r'), Loader=yaml.Loader))
sm_GND.init()
sm_GND.settings(voltage=4, current_limit=350*1e-6, voltage_limit=4)

sm_5 = sourcemeter(yaml.load(open("./lab_devices/keithley_2400.yaml", 'r'), Loader=yaml.Loader))
sm_5.init()
sm_5.settings(voltage=5, current_limit=350*1e-6, voltage_limit=5)