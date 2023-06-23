from lab_devices.sourcemeter import sourcemeter
import yaml
from lab_devices.LF_SFF_MIO import LF_SFF_MIO
import time 
import utils.plot_fit as pltfit
'''
dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
dut.init()
dut.load_defaults(DIODE_HV=1.8)
dut.boot_seq()

import matplotlib.pyplot as plt
import numpy as np

sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm.init()

avrg = []
PW_list = [0,-0.1,-0.2,-0.3,-0.5,-0.6,-0.7,-1,-2, -3, -5]
for i in PW_list:
    
    sm.pixel_depletion(PW_BIAS=i)
    time.sleep(1)
    data, data_err = dut.read_adc(adc_ch='fadc0_rx',nSamples=4096)
    avrg.append(np.average(data))
    print('############################\n',avrg[-1],'\n############################')
    print(i)
    input('press enter')

pltfit.beauty_plot(xlabel='PW_BIAS', ylabel='Baseline / V', figsize=[10,10])
plt.plot(PW_list, avrg, marker='x')
plt.savefig('output/testing/PWELL_Baseline.pdf',bbox_inches='tight')

plt.show()'''

sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm.init()    
sm.pixel_depletion(PW_BIAS=-1)
