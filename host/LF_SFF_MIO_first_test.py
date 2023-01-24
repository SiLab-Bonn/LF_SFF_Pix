# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------

import time
from basil.dut import Dut
import numpy as np
from LF_SFF_MIO import LF_SFF_MIO
import yaml

stream = open("LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)

dut = LF_SFF_MIO(cnfg)
dut.init()

dut.boot_seq()


# Voltages
VDD = 1.2
VDD_Unit = 'V'
VRESET = 1.1
VRESET_Unit = 'V'

# Currents
IBN =  100 
IBN_Unit = 'uA'
IBP = 10
IBP_Unit = 'uA'

dut['VDD'].set_voltage(VDD, unit=VDD_Unit)
print('VDD:', dut['VDD'].get_voltage(unit='V'), 'V', dut['VDD'].get_current(), 'mA')

dut['IBN'].set_current(IBN, unit=IBN_Unit)
print('IBN:', dut['IBN'].get_voltage(unit='V'), 'V', dut['IBN'].get_current(), 'uA')

dut['IBP'].set_current(IBP, unit=IBP_Unit)
print('IBP:', dut['IBP'].get_voltage(unit='V'), 'V', dut['IBP'].get_current(), 'uA')

dut['VRESET'].set_voltage(VRESET, unit=VRESET_Unit)
print('VRESET:', dut['VRESET'].get_voltage(unit='V'), VRESET_Unit, dut['VRESET'].get_current(), 'uA')

print('\n----------------------- Ending Configuration -----------------------\n')

##################### DIGITAL ####################


status = dut.get_status()
print(status)

data, sync = dut.take_adc_data('OUT_0')
print(data)