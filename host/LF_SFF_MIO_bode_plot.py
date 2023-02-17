# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                   _____________ Function Generator________
#                  |                        |               |
#                  | PIX_INPUT              | RS232         |
# -----------------------                   |               |
# | MIO | GPIO | LF_SFF |       MIO------Computer           |
# -----------------------            USB    |               |
#        Pixel 10  |                        | RJ45          |
#        Matrix 1  |                        |               |
#                  |______________________Oszi______________|
#                            CH2                   CH1
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
# If you can't see a trigger at 100Hz like in the picture below, restart the script, until it triggers correctly
#
#  /__________________________________/
#  |Tektronix TDS3034B                |
#  |   ___________________________    |
#  |  |                           | o |
#  |  | ~~~~~~~~~~~~~~\ |~~~~~~~~~| o |
#  |  | ---------------\|---------| o |
#  |  |___________________________| o |
#  |                CH1 o    CH2 o    | /
#  |_________________________________ |/
#
# The function generator is also completely controlled by this script. Please verify BEFORE plugging it into the PIX_INPUT of the
# LFSFF Board that the Ampl and Offset are not bigger than Vpp=100mV and Voff=650mV.
#


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
import bode_plot_analyzer as bp

image_path = './Test_Samples/Test_4_AC/'
data_path = image_path+'./data/'
reset_pulser = False


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

def func_fit_rst(x,a,b,c,d,e):
    #a,b,c,d=p
    return a*np.cos(b*x+c)+d*x+e

def func_fit_lin(x,d,e):
    return d*x+e


def guess_params(x,y,f,reset_pulser=False):
    ampl_limits = [np.amin(y),np.amax(y)]
    ampl_approx = np.abs(np.abs(ampl_limits[0])-np.abs(ampl_limits[1]))/2
    offset_approx = ampl_approx+ampl_limits[0]
    freq  = f*2*np.pi
    first_max_loc = 0
    slope = 0
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
        popt, perr = optimize.curve_fit(func_fit_rst, x, y ,p_func_gen)
        slope = popt[0]
    except:
        print('Failed to find a local maximum')
    if reset_pulser==True:
        return ampl_approx, freq, -first_max_loc, slope, offset_approx
    else:
        return ampl_approx, freq, -first_max_loc, offset_approx




def gen_waveform_x(waveform):
    x= np.linspace(0,waveform[2][0], len(waveform[1]))
    return x
stream = open("LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)

try:
    if 'resetPulse' in sys.argv[1:]:
        print('----------> RESETPULSE activated!')
        reset_pulser = True
        image_path = './Test_Samples/Test_4_AC_resetPulse/'
        data_path = image_path+'./data/'


    if 'DC' in sys.argv[1:]:
        image_path = './Test_Samples/Test_4_DC/'
        data_path = image_path+'./data/'


    dut = LF_SFF_MIO(cnfg)
    dut.init()

    dut.boot_seq()
    dut.load_defaults()
    dut.set_acquire_state('RUN')

except:
    print('INITIALIZATION ERROR! PLEASE VERIFY THAT THE DUT IS CONNECTED PROPERLY')


oszi = Dut('./lab_devices/tektronix_tds_3034b.yaml')
oszi.init()
oszi['Oscilloscope'].set_trigger_mode('AUTO')

# Configure viewport of the oscilloscope
oszi['Oscilloscope'].set_vertical_scale('5.0E-2',channel=1)
oszi['Oscilloscope'].set_vertical_position('-7.0E-1',channel=1)
oszi['Oscilloscope'].set_vertical_offset('0.0E0', channel=1)
oszi['Oscilloscope'].set_vertical_scale('5.0E-2',channel=2)
oszi['Oscilloscope'].set_vertical_position('2.0E-2',channel=2)
oszi['Oscilloscope'].set_vertical_offset('0.0E0', channel=2)
if reset_pulser:
    oszi['Oscilloscope'].set_trigger_source(channel=2)
    oszi['Oscilloscope'].set_trigger_level(-1.8E-2)
else:
    oszi['Oscilloscope'].set_trigger_level(1.0E-2)
    oszi['Oscilloscope'].set_trigger_source(channel=1)

freq_gen = Dut('./lab_devices/agilent33250a_pyserial.yaml')
freq_gen.init()
freq_gen['Pulser'].set_voltage_high(6.75e-1)
freq_gen['Pulser'].set_voltage_low(5.75e-1)

time.sleep(2)

frequency_oszi = [1e2,1e3,1e4,1e5,1e6]

# generate frequency scale that shall be scanned
frequencies = []
for i in frequency_oszi:
    frequencies.extend([i*j for j in range(1,10)])


# Add supported time scale by the oscilloscope
add_freq = []
for freq in frequency_oszi:
    add_freq.extend([freq*i for i in [2,4]])
frequency_oszi.extend(add_freq)

frequency_oszi = np.sort(frequency_oszi)


def nearest_value_in_list(value, data):
    nearest_value = 0
    for i in range(0,len(data)):
        if np.abs(data[i]-value) <= np.abs(data[nearest_value]-value):
            nearest_value = i
    return nearest_value


def measure_bode_plot():
    fit_params_func_gen = []
    fit_params_LF_SFF = []
    print('Measure at Frequency:')

    # Set correct frequencies
    for f in frequencies:
        if f in frequency_oszi:
            set_oszi_freq = f
        else:
            for i in range(1,6):
                if (f-i*len(str(f)[1:]) in frequency_oszi):
                    set_oszi_freq = i*len(str(f)[1:])
                    break
        print(f,' Hz')
        if(reset_pulser):
            set_oszi_freq=set_oszi_freq
        period = 1/f
        freq_gen['Pulser'].set_pulse_period(period)
        oszi['Oscilloscope'].set_horizontal_scale(1/set_oszi_freq)
        if(reset_pulser):
            time.sleep(1)
            oszi['Oscilloscope'].set_trigger_mode('NORM')

        time.sleep(5)

        # Create Reset Pulse
        if(reset_pulser):
            print('RESET')
            dut['CONTROL']['RESET'] = 0x1
            dut['CONTROL'].write()
            time.sleep(200e-6)  
            dut['CONTROL']['RESET'] = 0x0
            dut['CONTROL'].write()
            time.sleep(1)

        # make measurement for CH2 -> LF SFF
        meas_waveform_LF_SFF = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=False)
        CH_LF_SFF         = meas_waveform_LF_SFF[0]
        CH_data_LF_SFF    = meas_waveform_LF_SFF[1]
        CH_xscale_LF_SFF  = meas_waveform_LF_SFF[2]
        CH_yscale_LF_SFF  = meas_waveform_LF_SFF[3]
        CH_time_LF_SFF    = np.linspace(0,CH_xscale_LF_SFF[0]*len(CH_data_LF_SFF),len(CH_data_LF_SFF))#np.linspace(0,len(CH_data_LF_SFF),len(CH_data_LF_SFF))#
        
        # make measurement for CH1 -> function generator
        meas_waveform_func_gen = oszi['Oscilloscope'].get_waveform(channel=1)
        CH_func_gen         = meas_waveform_func_gen[0]
        CH_data_func_gen    = meas_waveform_func_gen[1]
        CH_xscale_func_gen  = meas_waveform_func_gen[2]
        CH_yscale_func_gen  = meas_waveform_func_gen[3]
        CH_time_func_gen    = np.linspace(0,CH_xscale_func_gen[0]*len(CH_data_func_gen),len(CH_data_func_gen))#np.linspace(0,len(CH_data_func_gen),len(CH_data_func_gen))
        np.savetxt(data_path+str(f)+'.csv', (CH_time_LF_SFF, CH_data_LF_SFF, CH_time_func_gen, CH_data_func_gen), delimiter=',')
        
        # Plot data
        plt.figure(figsize=(16,9))
        plt.scatter(CH_time_func_gen, CH_data_func_gen, label='Function Generator Data')
        plt.scatter(CH_time_LF_SFF, CH_data_LF_SFF, label='LF SFF Data', color='orange')

        
        # Find fit area in case of reset pulse
        if(reset_pulser):
            reset_tail = 0.5/f
            plt.scatter(CH_time_LF_SFF, CH_data_LF_SFF)
            peak_pos=None
            for i in range(0, len(CH_data_LF_SFF)-1):
                if np.abs(np.abs(CH_data_LF_SFF[i+1])-np.abs(CH_data_LF_SFF[i]))>=0.02:
                    peak_pos=i+1
            
            if peak_pos!=None:
                plt.scatter(CH_time_LF_SFF[peak_pos], CH_data_LF_SFF[peak_pos], color='black')
                plt.text(CH_time_LF_SFF[peak_pos], CH_data_LF_SFF[peak_pos]-0.02, 'RESET')
                print('edge detected')
                left_edge = CH_time_LF_SFF[peak_pos]+reset_tail
                left_edge = nearest_value_in_list(left_edge, CH_time_LF_SFF)
                right_edge = CH_time_LF_SFF[peak_pos]+5/f
                right_edge = nearest_value_in_list(right_edge, CH_time_LF_SFF)
            else:
                print('NO edge detected')
                left_edge=0
                right_edge=-1
            
            plt.vlines(CH_time_LF_SFF[left_edge],-100,100, color='black', linestyles='dashed')
            plt.vlines(CH_time_LF_SFF[right_edge],-100,100, color='black', linestyles='dashed')

            CH_data_LF_SFF = CH_data_LF_SFF[left_edge:right_edge]
            CH_time_LF_SFF = CH_time_LF_SFF[left_edge:right_edge]
            
            oszi['Oscilloscope'].set_trigger_mode('AUTO')
        
            
        time.sleep(3)

        # Fit data
        if reset_pulser:
            p_func_gen = guess_params(CH_time_func_gen,CH_data_func_gen, f)
            p_LF_SFF = guess_params(CH_time_LF_SFF,CH_data_LF_SFF, f, True)
            print(p_LF_SFF)
            popt_func_gen, perr =  optimize.curve_fit(func_fit, CH_time_func_gen, CH_data_func_gen,p_func_gen)
            popt_LF_SFF, perr =  optimize.curve_fit(func_fit_rst, CH_time_LF_SFF, CH_data_LF_SFF,p_LF_SFF)

            plt.plot(CH_time_func_gen, func_fit(CH_time_func_gen,popt_func_gen[0],popt_func_gen[1],popt_func_gen[2],popt_func_gen[3]), label='Function Generator fit ', color='black')
            plt.plot(CH_time_LF_SFF, func_fit_rst(CH_time_LF_SFF,popt_LF_SFF[0],popt_LF_SFF[1],popt_LF_SFF[2],popt_LF_SFF[3],popt_LF_SFF[4]), label='LF SFF fit', color='black')
            print(popt_LF_SFF)

        else:    
            p_func_gen = guess_params(CH_time_func_gen,CH_data_func_gen, f)
            p_LF_SFF = guess_params(CH_time_LF_SFF,CH_data_LF_SFF, f)
            popt_func_gen, perr =  optimize.curve_fit(func_fit, CH_time_func_gen, CH_data_func_gen,p_func_gen)
            popt_LF_SFF, perr =  optimize.curve_fit(func_fit, CH_time_LF_SFF, CH_data_LF_SFF,p_LF_SFF)
            
            plt.plot(CH_time_func_gen, func_fit(CH_time_func_gen,popt_func_gen[0],popt_func_gen[1],popt_func_gen[2],popt_func_gen[3]), label='Function Generator fit ', color='black')
            plt.plot(CH_time_LF_SFF, func_fit(CH_time_LF_SFF,popt_LF_SFF[0],popt_LF_SFF[1],popt_LF_SFF[2],popt_LF_SFF[3]), label='LF SFF fit', color='black')


        plt.ylim(-4*CH_yscale_func_gen[0], 4*CH_yscale_func_gen[0])
        plt.title('Frequency '+str(f)+'Hz')
        plt.grid(linestyle='--')
        plt.ylabel('Voltage in V')
        plt.xlabel('Time in s')
        plt.legend()
        plt.savefig(image_path+'measurement_'+str(f)+'.png')
        #plt.show()
        plt.close()
        fit_params_func_gen.append(popt_func_gen)
        fit_params_LF_SFF.append(popt_LF_SFF)

    x_log = np.abs(np.log10(1/np.array(fit_params_func_gen)[:,1]))
    y_db = 10*np.log10(np.abs(np.array(fit_params_LF_SFF)[:,0]/np.array(fit_params_func_gen)[:,0]))

    plt.figure(figsize=(16,9))
    plt.scatter(x_log, 10*np.log10(np.abs(np.array(fit_params_LF_SFF)[:,0]/np.array(fit_params_func_gen)[:,0])))
    plt.xlabel('log10(f)')
    plt.ylabel('$V_{pp}(LF SFF)/V_{pp}(Frequence Generator)$ in dB')

    plt.grid(linestyle='--')
    plt.savefig(image_path+'bodeplot_log.png')
    plt.show()
    plt.close()
    
    #np.savetxt(data_path+'bode.csv', (x_log, y_db), delimiter=',')
    with open(data_path+'bode.csv', 'w') as f:
        f.write('frequency, \tdB\n')
        for i in range(0, len(frequencies)):
            f.write(str(x_log[i])+',\t'+str(y_db[i]))
            f.write('\n')
    return x_log, y_db


x_log, y_db = measure_bode_plot()
f_hp, f_tp = bp.analyse_bode_plot(x_log, y_db, 'Bode Plot', image_path+'bodeplot.png')

C_ac = 6*1e-15

print('------ RESULTS ------')
print('$f_{hp}=$',f_hp,'Hz\n','$f_{tp}=$',f_tp,'Hz')
R_off = 2*np.pi/f_hp/C_ac
print('$R_{off}=$',R_off,'$\\Omega$')

