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

data, sync = dut.take_adc_data('OUT_0')
print(data)

dut['CONTROL']=0x00
dut['CONTROL'].write
channel_list = []
while True:
    try:
        channel = input("Activate Channel: ")
        if channel in channel_list:
            dut['CONTROL'][channel] = 0x0
            del channel_list[channel_list.index(channel)]
        else:
            if channel == 'exit':
                break
            dut['CONTROL'][channel] = 0x1
            channel_list.append(channel)
        dut['CONTROL'].write()  
    except:
        print("Channel does not exist")
    if len(channel_list)!= 0:
        print('\nActive channels: ', str(channel_list)[1:-1])
    time.sleep(1)
    status = dut.get_status()
    

""" 
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
"""