# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------

import time
from basil.dut import Dut
import numpy as np
from LF_SFF_MIO import LF_SFF_MIO
import matplotlib.pyplot as plt
from scipy import odr
from scipy import optimize
import uncertainties.unumpy as unp
import yaml
import sys

image_path = './Test_Samples/Test_4_DC/'

def double_err(function, x,y,presets): #x_error, y, y_error, presets):
    model = odr.Model(function)
    data = odr.RealData(x, y)#, sy=y_error)
    out = odr.ODR(data, model, beta0=presets).run()

    popt = out.beta
    perr = out.sd_beta

    return popt,perr

def func_fit(x,a,b,c,d):
    #a,b,c,d=p
    return a*np.cos(b*x+c)+d


def guess_params(x,y,f,period,time_max):
    ampl_limits = [np.amin(y),np.amax(y)]
    ampl_approx = np.abs(np.abs(ampl_limits[0])-np.abs(ampl_limits[1]))/2
    offset_approx = ampl_approx+ampl_limits[0]
    freq  = f*2*np.pi
    print(freq)
    first_max_loc = 0
    try:
        for i in range(0,len(y)):
            current_max = 0
            if y[i] >= current_max:
                pass_if = 100
                pass_count = 0
                for j in range(0,pass_if):
                    if(y[i]>=y[i+j]):
                        pass_count+=1
                if pass_if == pass_count:
                    current_max = y[i]
                    first_max_loc = i
                    break
    except:
        print('Failed to find a local maximum')
    
    return ampl_approx,freq, -first_max_loc, offset_approx


def gen_waveform_x(waveform):
    x= np.linspace(0,waveform[2][0], len(waveform[1]))
    return x
stream = open("LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)

try:
    if sys.argv[1]=='flash':
        dut = LF_SFF_MIO(cnfg)
        dut.init()

        dut.boot_seq()
        dut.load_defaults()
except:
    print('')



oszi = Dut('./lab_devices/tektronix_tds_3034b.yaml')
oszi.init()

freq_gen = Dut('./lab_devices/agilent33250a_pyserial.yaml')
freq_gen.init()
voltage=freq_gen['Pulser'].get_voltage(0, unit='mV')
print(voltage)

channel = 1
frequency_steps = 20
frequency_range = [100,1e3,1e4,1e5,1e6]
add_freq = []
for f in frequency_range:
    if f != 1e6:
        add_freq.extend([f*i for i in range(2,5)])
print(add_freq)
frequency_range.extend(add_freq)
print(frequency_range)

meas_waveform = np.array([])

fit_params_func_gen = []
fit_params_LF_SFF = []

for f in frequency_range:
    print('Frequency: ',f)
    plt.figure(figsize=(16,9))
    period = 1/f
    freq_gen['Pulser'].set_pulse_period(period)
    oszi['Oscilloscope'].set_horizontal_scale(period)
    time.sleep(1)
    # make measurement for CH2 -> LF SFF
    meas_waveform_LF_SFF = oszi['Oscilloscope'].get_waveform(channel=2)
    CH_LF_SFF         = meas_waveform_LF_SFF[0]
    CH_data_LF_SFF    = meas_waveform_LF_SFF[1]
    CH_xscale_LF_SFF  = meas_waveform_LF_SFF[2]
    CH_yscale_LF_SFF  = meas_waveform_LF_SFF[3]
    CH_time_LF_SFF    = np.linspace(0,CH_xscale_LF_SFF[0]*len(CH_data_LF_SFF),len(CH_data_LF_SFF))#np.linspace(0,len(CH_data_LF_SFF),len(CH_data_LF_SFF))#
    

    time.sleep(1)

    # make measurement for CH1 -> function generator
    meas_waveform_func_gen = oszi['Oscilloscope'].get_waveform(channel=1)
    CH_func_gen         = meas_waveform_func_gen[0]
    CH_data_func_gen    = meas_waveform_func_gen[1]
    CH_xscale_func_gen  = meas_waveform_func_gen[2]
    CH_yscale_func_gen  = meas_waveform_func_gen[3]
    CH_time_func_gen    = np.linspace(0,CH_xscale_func_gen[0]*len(CH_data_func_gen),len(CH_data_func_gen))#np.linspace(0,len(CH_data_func_gen),len(CH_data_func_gen))
    

    time_max_func_gen = CH_time_func_gen.max()
    time_max_LF_SFF = CH_time_LF_SFF.max()
    print(CH_xscale_func_gen)

    plt.scatter(CH_time_func_gen, CH_data_func_gen, label='Function Generator Data')
    plt.scatter(CH_time_LF_SFF, CH_data_LF_SFF, label='LF SFF Data')

    p_func_gen = guess_params(CH_time_func_gen,CH_data_func_gen, f, period, time_max_func_gen)
    p_LF_SFF = guess_params(CH_time_LF_SFF,CH_data_LF_SFF, f, period, time_max_LF_SFF)

    #plt.plot(CH_time_LF_SFF, func_fit(CH_time_LF_SFF, p_LF_SFF[0], p_LF_SFF[1], p_LF_SFF[2], p_LF_SFF[3]), color='pink')
    #plt.plot(CH_time_LF_SFF, func_fit(CH_time_func_gen, p_func_gen[0], p_func_gen[1], p_func_gen[2], p_func_gen[3]), color='pink')

    #popt, perr = double_err(func_fit, CH_time_func_gen, CH_data_func_gen,p)
    popt_func_gen, perr =  optimize.curve_fit(func_fit, CH_time_func_gen, CH_data_func_gen,p_func_gen)
    popt_LF_SFF, perr =  optimize.curve_fit(func_fit, CH_time_LF_SFF, CH_data_LF_SFF,p_LF_SFF)

    fit_params_func_gen.append(popt_func_gen)
    fit_params_LF_SFF.append(popt_LF_SFF)

    print(popt_func_gen)
    plt.plot(CH_time_func_gen, func_fit(CH_time_func_gen,popt_func_gen[0],popt_func_gen[1],popt_func_gen[2],popt_func_gen[3]), label='Function Generator fit ', color='black')
    plt.plot(CH_time_LF_SFF, func_fit(CH_time_LF_SFF,popt_LF_SFF[0],popt_LF_SFF[1],popt_LF_SFF[2],popt_LF_SFF[3]), label='LF SFF fit', color='black')


    plt.ylim(-4*CH_yscale_func_gen[0], 4*CH_yscale_func_gen[0])
    plt.title('Frequency '+str(f))
    plt.grid(linestyle='--')
    plt.ylabel('Time in V')
    plt.xlabel('Voltage in s')
    plt.legend()
    plt.savefig(image_path+'measurement_'+str(f)+'.png')
    plt.close()


plt.scatter((frequency_range), np.array(fit_params_LF_SFF)[:,0]/np.array(fit_params_func_gen)[:,0])
plt.xlabel('f / Hz')
plt.ylabel('$V_{pp}(LF SFF)/V_{pp}(Frequence Generator)$')

plt.grid(linestyle='--')
plt.savefig(image_path+'bodeplot.png')
plt.show()

