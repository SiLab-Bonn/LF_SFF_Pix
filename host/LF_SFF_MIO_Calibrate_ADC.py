# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#               _________________
#              | ______________  |                    
# ADC[0,1,2,3] | | ADC_0,1,2,3 | |                 
#   --------------             | |                     
#   | MIO | GPIO |__VSRC1______| |        MIO------Computer           
#   --------------__VSRC3________|          
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
# If you can't see a trigger at 100Hz like in the picture below, restart the script, until it triggers correctly
#


from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.function_generator import function_generator
import matplotlib.pyplot as plt
import yaml
import numpy as np
import utils.plot_fit as pltfit
import utils.data_handler as dh
import time

# This script automatically calibrates the ADC on the GPAC Card by applying external voltages and reading them in

def calibrate_ADC():
    nSamples = 10000
    offset = 0.5
    #func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    #func_gen.init()

    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.load_defaults()
    dut['ADC_REF'].set_voltage(offset)
    voltages = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    ch_list =['fadc0_rx','fadc1_rx','fadc2_rx','fadc3_rx']
    data = [[[] for i in voltages] for j in ch_list]
    data_err = [[[] for i in voltages] for j in ch_list]
    input_data = [[[] for i in voltages] for j in ch_list]
    input_data_err = [[[] for i in voltages] for j in ch_list]
    for adc_ch in ch_list:    
        pltfit.beauty_plot()
        input('Plug in %s and enter something to continue'%(adc_ch))
        for V in voltages:
            dut['opAMP_offset'].set_voltage(offset+V)
            input_data[ch_list.index(adc_ch)][voltages.index(V)] = dut['opAMP_offset'].get_voltage()
            input_data_err[ch_list.index(adc_ch)][voltages.index(V)] = 0.005
            time.sleep(0.1)
            meas = dut.read_raw_adc(nSamples, adc_ch)
            data[ch_list.index(adc_ch)][voltages.index(V)] = np.average(meas)
            data_err[ch_list.index(adc_ch)][voltages.index(V)] = np.std(meas)
            plt.plot(meas,np.linspace(offset+np.min(voltages), np.max(voltages)+offset,len(meas)), alpha=0.3, label=str(V)+'V')
        plt.errorbar(y=input_data[ch_list.index(adc_ch)],yerr=input_data_err[ch_list.index(adc_ch)],x=data[ch_list.index(adc_ch)], xerr=data_err[ch_list.index(adc_ch)], color='black', marker='x', linestyle='None')
        popt, perr = pltfit.double_err(function=pltfit.func_lin,y=input_data[ch_list.index(adc_ch)],y_error=input_data_err[ch_list.index(adc_ch)], x=data[ch_list.index(adc_ch)], x_error=data_err[ch_list.index(adc_ch)], presets=[0,8000])        
        x = np.array([np.min(data[ch_list.index(adc_ch)])-100,np.max(data[ch_list.index(adc_ch)])+100])
        y = popt[0]*x+popt[1]
        plt.plot(x,y, label='$U(x)=(%.3f\pm%.3f)10^{-5}$V$\cdot x+(%.3f\pm%.3f)$V'%(popt[0]*1e5, perr[0]*1e5, popt[1], perr[1]), color='black')
        plt.legend()
        plt.savefig('./output/ADC_Calibration/'+adc_ch+'.pdf')
        dh.save_data(data=[popt, perr], output_path='./output/ADC_Calibration/data/'+adc_ch+'.csv')
        plt.show()
        plt.close()

calibrate_ADC()