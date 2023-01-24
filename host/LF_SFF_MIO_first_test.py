# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------

import time
from basil.dut import Dut
import numpy as np
from LF_SFF_MIO import LF_SFF_MIO
import yaml


## VDD -> PWR0
## ISRC0 -> IBP
## ISRC1 -> IBN
## DOUT[0:2] -> SEL[0:2]
## DOUT3 -> RESET
## VSRC0 -> VRESET
## FAST_ADC[0:3] -> Out[0:3]
## VSRC1 -> Offset opAMP

stream = open("LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)

dut = LF_SFF_MIO(cnfg)
dut.init()

dut.boot_seq()


print('\n----------------------- Starting Configuration -----------------------\n')

dut.load_defaults()

print('\n----------------------- Ending Configuration -----------------------\n')

##################### DIGITAL ####################


status = dut.get_status()
print(status)

data, sync = dut.take_adc_data('OUT_0')
print(data)

while True:
    dut['CONTROL']['SEL0'] = 0x1
    dut['CONTROL']['SEL1'] = 0x1
    dut['CONTROL']['SEL2'] = 0x1
    dut['CONTROL']['RESET'] = 0x1
    dut['CONTROL'].write()
    time.sleep(5)
    dut['CONTROL'] = 0x00
    dut['CONTROL'].write()
    time.sleep(2)
    dut['CONTROL']['SEL0'] = 0x1
    dut['CONTROL'].write()
    time.sleep(0.2)
    dut['CONTROL']['SEL1'] = 0x1
    dut['CONTROL'].write()
    time.sleep(0.2)
    dut['CONTROL']['SEL2'] = 0x1
    dut['CONTROL'].write()
    time.sleep(0.2)
    dut['CONTROL']['RESET'] = 0x1
    dut['CONTROL'].write()
    time.sleep(0.2)
    dut['CONTROL']['LED5'] = 0x1
    dut['CONTROL'].write()
    time.sleep(0.2)
