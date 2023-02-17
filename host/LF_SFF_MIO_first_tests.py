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


status = dut.get_status()

data, sync = dut.take_adc_data('OUT_0')
print(data)

dut['CONTROL']=0x00
dut['CONTROL'].write
channel_list = []
test_list = ['ScanVRESET','resetPulse','Test']
while True:
    try:
        channel = input("Activate Channel or run test: ")
        if channel not in test_list:
            if channel in channel_list:
                dut['CONTROL'][channel] = 0x0
                del channel_list[channel_list.index(channel)]
            else:
                if channel == 'exit':
                    break
                
                dut['CONTROL'][channel] = 0x1
                channel_list.append(channel)
            dut['CONTROL'].write()
            if len(channel_list)!= 0:
                print('\nActive channels: ', str(channel_list)[1:-1])
        if channel == "Test":
            dut.get_status()
            print(dut['IBN'].get_current())
            print(dut['IBP'].get_current())

        if channel == "ScanVRESET":
            dut['CONTROL']['RESET']=0x1
            dut['CONTROL'].write()
            measured_VRESET_list = []
            V_out_list = []
            IBN_meas = []
            IBP_meas = []
            for i in range(1,13):
                target_VRESET = i*0.1
                dut['VRESET'].set_voltage(target_VRESET, unit='V')
                print('SET VRESET: ', target_VRESET, 'V')
                measured_VRESET = str(dut['VRESET'].get_voltage(unit='V'))[:6]
                measured_VRESET_list.append(measured_VRESET)
                print('Measured: ',measured_VRESET , 'V')
                V_out = input('Enter Output Voltage / mV: ')
                V_out_list.append(V_out)
                print('\n')
                IBN_meas.append(dut['IBN'].get_current(unit='uA'))
                IBP_meas.append(dut['IBP'].get_current(unit='uA'))
            
            IBN_avrg = np.average(IBN_meas)
            IBP_avrg = np.average(IBP_meas)
            print('IBN: ',IBN_avrg)
            print('IBP: ',IBP_avrg)
            print('VRESET / V, V_Out / mV')
            for i in range(0, len(measured_VRESET_list)):
                print(measured_VRESET_list[i], ',', V_out_list[i])
            print('\nScan done\n')
        
        if channel == 'resetPulse':
            dut['CONTROL']['RESET'] = 0x1
            dut['CONTROL'].write()
            time.sleep(1e-6)  
            dut['CONTROL']['RESET'] = 0x0
            dut['CONTROL'].write()
    except:
        print("Channel or Test does not exist")
    
    time.sleep(1)
    status = dut.get_status()
    