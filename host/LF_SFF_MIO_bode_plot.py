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
# LFSFF Board that the Ampl and Offset are not larger than Vpp=100mV and Voff=650mV.
#


import time
from basil.dut import Dut
import numpy as np
from LF_SFF_MIO import LF_SFF_MIO
import matplotlib.pyplot as plt
from scipy import optimize
import uncertainties.unumpy as unp
import yaml
import sys
import bode_plot_analyzer as bp
import utils.plot_fit as bplt


image_path = './Test_Samples/Test_4_AC/'
data_path = image_path+'data/'
reset_pulser = False
hacked_setup = False

def func_fit(x,a,b,c,d):
    #a,b,c,d=p
    return a*np.cos(b*x+c)+d

def func_fit_rst(x,a,b,c,d,e):
    #a,b,c,d=p
    return a*np.cos(b*x+c)+d*x+e

def func_fit_lin(x,d,e):
    return d*x+e

# Function to coarsly guess fit parameters for the both, the func_fit and func_rst_fit functions
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
        if reset_pulser:
            popt, perr = optimize.curve_fit(func_fit_rst, x, y ,p_func_gen)
            slope = popt[0]
    except:
        print('Could not guess all fit parameters')
    if reset_pulser==True:
        return ampl_approx, freq, -first_max_loc, slope, offset_approx
    else:
        return ampl_approx, freq, -first_max_loc, offset_approx

# Generates x values for a taken waveform measurement (We only know the number of dots and the scale width)
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
        data_path = './data/'


    if 'DC' in sys.argv[1:]:
        image_path = './Test_Samples/Test_4_DC/'
        data_path = './data/'

    if 'hack' in sys.argv[1:]:
        print('Hacked setup initiated')
        image_path = './Test_Samples/Test_4_AC_hacked_setup/'
        data_path = './data/'
        hacked_setup = True

    dut = LF_SFF_MIO(cnfg)
    dut.init()

    dut.boot_seq()
    dut.load_defaults()
    dut.set_acquire_state('RUN')

except:
    print('INITIALIZATION ERROR! PLEASE VERIFY THAT THE DUT IS CONNECTED PROPERLY')


oszi = Dut('./lab_devices/tektronix_tds_3034b.yaml')
oszi.init()

# Configure viewport of the oscilloscope
oszi['Oscilloscope'].set_vertical_scale('5.0E-2',channel=1)
oszi['Oscilloscope'].set_vertical_position('-7.0E-1',channel=1)
oszi['Oscilloscope'].set_vertical_offset('0.0E0', channel=1)
oszi['Oscilloscope'].set_coupling('AC', channel=1)
oszi['Oscilloscope'].set_vertical_scale('5.0E-2',channel=2)
oszi['Oscilloscope'].set_vertical_position('2.0E-2',channel=2)
oszi['Oscilloscope'].set_vertical_offset('0.0E0', channel=2)
oszi['Oscilloscope'].set_coupling('AC', channel=2)


if reset_pulser:
    trigger_lvl = -1.8E-2
    oszi['Oscilloscope'].set_trigger_source(channel=2)
else:
    trigger_lvl = 1.0E-2
    oszi['Oscilloscope'].set_trigger_source(channel=1)

oszi['Oscilloscope'].set_trigger_level(trigger_lvl)
oszi['Oscilloscope'].set_trigger_mode('AUTO')

# Configure settings of the function generator
freq_gen = Dut('./lab_devices/agilent33250a_pyserial.yaml')
freq_gen.init()

if hacked_setup:
    dut['VRESET'].set_voltage(0.0, unit='V') 
    dut['CONTROL']['RESET'] = 0x1
    dut['CONTROL'].write()
    oszi['Oscilloscope'].set_vertical_scale('200.0E-3',channel=1)
    oszi['Oscilloscope'].set_vertical_scale('5.0E-3',channel=2)
    freq_gen['Pulser'].set_voltage_high(8.0e-1)
    freq_gen['Pulser'].set_voltage_low(0.0) 
else:
    freq_gen['Pulser'].set_voltage_high(6.75e-1)
    freq_gen['Pulser'].set_voltage_low(5.75e-1)
    
freq_gen['Pulser'].set_enable(1)

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

time.sleep(2)

IBP_default = -10
IBN_default = 100
R_on = np.array([])

def measure_bode_plot(IBN=IBN_default, IBP=IBP_default,R_on_output=False, load_stored=False):
    try:
        IBP_Gain = np.genfromtxt('./Test_Samples/Reset_Probe/IBP_Gain.csv', delimiter=',')
        IBN_Gain = np.genfromtxt('./Test_Samples/Reset_Probe/IBN_Gain.csv', delimiter=',')
    except:
        print('No Gain measurement found. Please run "python LF_SFF_MIO_RESET_Probe.py ScanVRESET"')
        G=1
    if (IBN!=IBN_default and IBP==IBP_default):
        G = IBN_Gain[0][0]*IBN+IBN_Gain[0][1]
    elif (IBP!=IBP_default and IBN==IBN_default):
        G = IBP_Gain[0][0]*IBP+IBP_Gain[0][1]
    else:
        G = IBN_Gain[0][0]*IBN+IBN_Gain[0][1]

    if not load_stored:
        print('--- Not loaded a stored dataset ---')
        print('Applied Gain G =',G)
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
            plt.xlim(np.min(CH_time_LF_SFF), np.max(CH_time_LF_SFF))
            plt.scatter(CH_time_func_gen, CH_data_func_gen, label='Function Generator Data')
            plt.scatter(CH_time_LF_SFF, CH_data_LF_SFF, label='LF SFF Data', color='orange')
            
            # Find fit area in case of reset pulse
            if(reset_pulser):
                reset_tail = 0.5/f
                plt.scatter(CH_time_LF_SFF, CH_data_LF_SFF, marker='x')
                plt.plot([-100,100], [trigger_lvl, trigger_lvl])
                try:
                    peak = np.amin([i for i in CH_data_LF_SFF if i<=trigger_lvl])
                    peak_pos = np.argmin(np.abs(CH_data_LF_SFF - peak))
                    plt.scatter(CH_time_LF_SFF[peak_pos], CH_data_LF_SFF[peak_pos], color='black')
                    left_edge = CH_time_LF_SFF[peak_pos]+reset_tail
                    left_edge = np.argmin(np.abs(CH_time_LF_SFF - left_edge))
                    right_edge = CH_time_LF_SFF[peak_pos]+5/f
                    right_edge = np.argmin(np.abs(CH_time_LF_SFF - right_edge))
                    plt.vlines(CH_time_LF_SFF[left_edge],-100,100, color='black', linestyles='dashed')
                    plt.vlines(CH_time_LF_SFF[right_edge],-100,100, color='black', linestyles='dashed')

                    CH_data_LF_SFF = CH_data_LF_SFF[left_edge:right_edge]
                    CH_time_LF_SFF = CH_time_LF_SFF[left_edge:right_edge]
                except:
                    print('Could not detect reset pulse')           
                
                oszi['Oscilloscope'].set_trigger_mode('AUTO')
            
            time.sleep(3)

            # Fit data       
            if reset_pulser:
                p_func_gen = guess_params(CH_time_func_gen,CH_data_func_gen, f)
                p_LF_SFF = guess_params(CH_time_LF_SFF,CH_data_LF_SFF, f, True)
                popt_func_gen, perr =  optimize.curve_fit(func_fit, CH_time_func_gen, CH_data_func_gen,p_func_gen)
                popt_LF_SFF, perr =  optimize.curve_fit(func_fit_rst, CH_time_LF_SFF, CH_data_LF_SFF,p_LF_SFF)

                plt.plot(CH_time_func_gen, func_fit(CH_time_func_gen,popt_func_gen[0],popt_func_gen[1],popt_func_gen[2],popt_func_gen[3]), label='Function Generator fit ', color='black')
                plt.plot(CH_time_LF_SFF, func_fit_rst(CH_time_LF_SFF,popt_LF_SFF[0],popt_LF_SFF[1],popt_LF_SFF[2],popt_LF_SFF[3],popt_LF_SFF[4]), label='LF SFF fit', color='black')

            else:    
                p_func_gen = guess_params(CH_time_func_gen,CH_data_func_gen, f)
                p_LF_SFF = guess_params(CH_time_LF_SFF,CH_data_LF_SFF, f)
                popt_func_gen, perr_func_gen =  optimize.curve_fit(func_fit, CH_time_func_gen, CH_data_func_gen,p_func_gen)
                popt_LF_SFF, perr_LF_SFF =  optimize.curve_fit(func_fit, CH_time_LF_SFF, CH_data_LF_SFF,p_LF_SFF)
                            
                plt.plot(CH_time_func_gen, func_fit(CH_time_func_gen,popt_func_gen[0],popt_func_gen[1],popt_func_gen[2],popt_func_gen[3]), label='Function Generator fit ', color='black')
                plt.plot(CH_time_LF_SFF, func_fit(CH_time_LF_SFF,popt_LF_SFF[0],popt_LF_SFF[1],popt_LF_SFF[2],popt_LF_SFF[3]), label='LF SFF fit', color='black')

            # Plot everything
            plt.ylim(-4*CH_yscale_func_gen[0], 4*CH_yscale_func_gen[0])
            plt.title('Frequency '+str(f)+'Hz')
            plt.grid(linestyle='--')
            plt.ylabel('Voltage in V')
            plt.xlabel('Time in s')
            plt.legend()
            plt.savefig(image_path+'measurement_'+str(f)+'.png')
            plt.close()
            fit_params_func_gen.append(popt_func_gen)
            fit_params_LF_SFF.append(popt_LF_SFF)

        if hacked_setup:
            C_ac = 6*1e-15 # Taken from the datasheet
            R_ext = 100
            Z_ac = 1/(2*np.pi*1j*np.array(frequencies)*C_ac)
            R_on = np.abs((R_ext+Z_ac)*(np.abs((np.array(fit_params_func_gen)[:,0])/np.array(fit_params_LF_SFF)[:,0]*G))-R_ext-Z_ac)
            bplt.beauty_plot()
            plt.scatter(frequencies, R_on)
            plt.savefig(image_path+'R_on.png')
            plt.show()    
    
        x_log = np.abs(np.log10(1/np.array(fit_params_func_gen)[:,1]))
        y_db = 10*np.log10(np.abs(np.array(fit_params_LF_SFF)[:,0]/np.array(fit_params_func_gen)[:,0]))

        # Save data   
        file_name = 'data.csv'
        if hacked_setup:
            file_name = 'data_Ron.csv'

        with open(data_path+file_name, 'w') as f:
            f.write('frequency, \tdB\n')
            for i in range(0, len(frequencies)):
                if not hacked_setup:
                    f.write(str(x_log[i])+',\t'+str(y_db[i]))
                else:
                    f.write(str(x_log[i])+',\t'+str(y_db[i])+',\t'+str(R_on[i]))
                f.write('\n')
        print('Saved stored in:', data_path)
    else:
        if hacked_setup:
            data = np.genfromtxt(data_path+'data_Ron.csv',delimiter=',')
            R_on = data[0:,2]
        else:
            data = np.genfromtxt(data_path+'data.csv',delimiter=',')
        x_log = data[0:,0]
        y_log = data[0:,1] 
        

    if R_on_output:
        return x_log, y_db, R_on
    else:
        return x_log, y_db

if hacked_setup:
    x_log, y_db, R_on = measure_bode_plot(R_on_output=True)
    while True:
        change_setup = input("Now connect the Pix In withouth the resistor in series. [y to continue]")
        if change_setup == 'y':
            dut['CONTROL']['RESET'] = 0x0
            dut['CONTROL'].write()
            freq_gen['Pulser'].set_voltage_high(6.75e-1)
            freq_gen['Pulser'].set_voltage_low(5.75e-1)
            oszi['Oscilloscope'].set_vertical_scale('5.0E-3',channel=2)
            oszi['Oscilloscope'].set_vertical_scale('5.0E-2',channel=1)
            break
    time.sleep(1)
x_log, y_db = measure_bode_plot()
f_hp, f_tp, C_in = bp.analyse_bode_plot(x_log, y_db, 'Bode Plot', image_path+'bodeplot.png')

C_ac = 6*1e-15 # Taken from the datasheet

print('------ RESULTS ------')
print('$f_{hp}=$',f_hp,'Hz \n$f_{tp}=$',f_tp,'Hz')
print('$C_{in}=$', C_in,' fF')
if(f_hp != None or f_tp != None):
    R_off = 2*np.pi/f_hp/C_ac
    print('$R_{off}=$',R_off,'$\\Omega$')
if hacked_setup:
    print('R_on=', np.average(R_on))