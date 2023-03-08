# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                                                           
# -----------------------                               
# | MIO | GPIO | LF_SFF |       MIO------Computer           
# -----------------------            USB    |               
#        Pixel 10  |                        | RJ45          
#        Matrix 1  |                        |               
#                  |______________________Oszi
#                            CH2              
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
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


import time
from basil.dut import Dut
import numpy as np
from LF_SFF_MIO import LF_SFF_MIO
import matplotlib.pyplot as plt
import yaml
import sys
import matplotlib.ticker as ticker
from scipy import optimize
from scipy import odr

image_path = './Test_Samples/Test_4_AC/'
data_path = image_path+'./data/'

stream = open("LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)

VRESET = 1.2

try:
    dut = LF_SFF_MIO(cnfg)
    dut.init()

    dut.boot_seq()
    dut.load_defaults(VRESET = VRESET)
    dut.set_acquire_state('RUN')
except:
    print('Firmware not flashed. This can be because a firmware was already flashed or your setup is broken')

oszi = Dut('./lab_devices/tektronix_tds_3034b.yaml')
oszi.init()

# Configure viewport of the oscilloscope
oszi['Oscilloscope'].set_vertical_scale('1.0E-1',channel=2)
oszi['Oscilloscope'].set_vertical_position('-5.0E0',channel=2)
oszi['Oscilloscope'].set_vertical_offset('0.0E0', channel=2)
oszi['Oscilloscope'].set_coupling('DC', channel=2)

trigger_lvl = 730E-3
oszi['Oscilloscope'].set_trigger_source(channel=2)


chip_version = 'AC'
if 'DC' in sys.argv[1:]:
    chip_version='DC'

def func_lin(p,x):
    a,b=p
    return a*x+b

def double_err(function, x, x_error, y, y_error, presets):
    model = odr.Model(function)
    data = odr.RealData(x, y, sx=x_error, sy=y_error)
    out = odr.ODR(data, model, beta0=presets).run()

    popt = out.beta
    perr = out.sd_beta

    return popt,perr

def take_data(RST,time,axs):
    V_out_time = np.array([])
    V_out_data = np.array([])
    meas_waveform_LF_SFF = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
    CH_LF_SFF         = meas_waveform_LF_SFF[0]
    V_out_data = np.append(V_out_data,meas_waveform_LF_SFF[1])
    CH_xscale_LF_SFF  = meas_waveform_LF_SFF[2]
    V_out_yscale  = meas_waveform_LF_SFF[3]
    V_out_time= np.append(V_out_time, np.linspace(0,CH_xscale_LF_SFF[0]*len(meas_waveform_LF_SFF[1]),len(meas_waveform_LF_SFF[1])))#np.linspace(0,len(CH_data_LF_SFF),len(CH_data_LF_SFF))#

    RST_data = np.full(len(V_out_time),RST)
    VRST_data = np.full(len(V_out_time),dut['VRESET'].get_voltage(unit='V'))
    axs[0].vlines(np.max(V_out_time)+time,-10,10, color='black', linestyle='--',alpha=0.6)
    axs[1].vlines(np.max(V_out_time)+time,-10,10, color='black', linestyle='--',alpha=0.6)
    axs[2].vlines(np.max(V_out_time)+time,-10,10, color='black', linestyle='--',alpha=0.6)
    return V_out_time+time, V_out_data, V_out_yscale, VRST_data, RST_data

#
# reset_probe() measures the V_Out for different V_RST voltages when RST is deactivated 
# after the first probe. It generates a picture like:
#
# V_out |___
#       |   |___
#       |       |__________ ...         
#       |                  
#       |________________________
#                               t
# V_RST |______
#       |      |___
#       |          |___
#       |              |___ ...
#       |________________________
#                               t
#   RST |
#     1 |___
#       |  |
#     0 |  |________________ ...
#       |________________________ 
#                               t
#

def reset_probe():
    fig, axs = plt.subplots(3, 1)
    fig.set_figheight(12)
    fig.set_figwidth(16)
    # Start with turned on RST
    dut['CONTROL']['RESET'] = 0x1
    dut['CONTROL'].write()
    time.sleep(1)
    V_out_time = np.array([])
    V_out_data = np.array([])
    VRST_data = np.array([])
    RST_data = np.array([])

    V_out_time_meas, V_out_data_meas, V_out_yscale, VRST_data_meas, RST_data_meas = take_data(RST=1,time=0,axs=axs)
    V_out_time = np.append(V_out_time,V_out_time_meas)
    V_out_data = np.append(V_out_data,V_out_data_meas)
    VRST_data = np.append(VRST_data,VRST_data_meas)
    RST_data = np.append(RST_data,RST_data_meas)


    # Turn off RST
    dut['CONTROL']['RESET'] = 0x0
    dut['CONTROL'].write()
    time.sleep(1)

    V_out_time_meas, V_out_data_meas, V_out_yscale, VRST_data_meas, RST_data_meas = take_data(RST=0, time=np.max(V_out_time),axs=axs)
    V_out_time = np.append(V_out_time,V_out_time_meas)
    V_out_data = np.append(V_out_data,V_out_data_meas)
    VRST_data = np.append(VRST_data,VRST_data_meas)
    RST_data = np.append(RST_data,RST_data_meas)
    
    time.sleep(1)

    # Change VRESET 
    VRESET=[1,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1]
    for V in VRESET:
        dut['VRESET'].set_voltage(V, unit='V')
        time.sleep(1)
        V_out_time_meas, V_out_data_meas, V_out_yscale, VRST_data_meas, RST_data_meas = take_data(RST=0, time=np.max(V_out_time),axs=axs)
        V_out_time = np.append(V_out_time,V_out_time_meas)
        V_out_data = np.append(V_out_data,V_out_data_meas)
        VRST_data = np.append(VRST_data,VRST_data_meas)
        RST_data = np.append(RST_data,RST_data_meas)
    
    fig.suptitle(chip_version)
    axs[0].scatter(V_out_time,V_out_data)
    axs[0].set_ylim(-4*V_out_yscale[0], 4*V_out_yscale[0])
    axs[0].set_xlim(np.min(V_out_time),np.max(V_out_time))
    axs[0].set_ylabel('rel. $V_{Out}$ / V')
    axs[0].grid()
    axs[1].plot(V_out_time, VRST_data)
    axs[1].set_ylabel('$V_{RST}$ / V')
    axs[1].set_xlim(np.min(V_out_time),np.max(V_out_time))
    axs[1].grid()
    axs[1].set_ylim(0,1.3)
    axs[2].plot(V_out_time, RST_data)
    axs[2].set_ylabel('RST')
    axs[2].set_xlabel('nicht zusammenhaengende Zeitabschnitte $t$ / s')
    axs[2].set_xlim(np.min(V_out_time),np.max(V_out_time))
    axs[2].grid(axis='x')
    axs[2].set_ylim(-0.1,1.1)
    axs[2].locator_params(axis='y',integer=True,tight=True)

    fig.tight_layout()
    plt.savefig('Test_Samples/Reset_Probe/results_'+chip_version+'.png')
    plt.show()

#
# Function that scans VReset with different IBN, IBP settings.
# Therefore one can see an saturated area and measure the gain for IBN/IBP while one is fixed
# to its default value
#

def ScanVRESET():
    IBN = [80,82,85,87,90,92,95,97,100]
    IBP = np.linspace(-5,-10,6)
    I_unit = 'uA'
    VRESET = np.linspace(0.1,1.2,12)

    IBN_meas = [[] for i in range(0, len(IBN))]
    IBN_VOUT = [[] for i in range(0, len(IBN))]
    IBN_VOUT_err = [[] for i in range(0, len(IBN))]
    IBN_VRESET = [[] for i in range(0, len(IBN))]
   
    IBP_meas = [[] for i in range(0, len(IBP))]
    IBP_VOUT = [[] for i in range(0, len(IBP))]
    IBP_VOUT_err = [[] for i in range(0, len(IBP))]
    IBP_VRESET = [[] for i in range(0, len(IBP))]

    dut['CONTROL']['RESET'] = 0x0
    dut['CONTROL'].write()
    time.sleep(2)
    baseline_meas = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)[1]
    baseline = np.average(baseline_meas)
    baseline_err = np.std(baseline_meas)
    
    # Scan VRESET by constant IBP/IBN -> defaults IBN=100, IBP=-10
    dut['CONTROL']['RESET'] = 0x1
    dut['CONTROL'].write()

    for V in VRESET:
        dut['VRESET'].set_voltage(V,unit='V')
        time.sleep(0.2)
        for I in IBN:
            pos = IBN.index(I)
            dut['IBN'].set_current(I,unit=I_unit)
            time.sleep(0.5)
            IBN_meas[pos].append(dut['IBN'].get_current(unit=I_unit))
            waveform = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)[1]
            IBN_VOUT[pos].append(1000*(np.average(waveform)-baseline))
            IBN_VOUT_err[pos].append(1000*np.std(waveform))
            IBN_VRESET[pos].append(dut['VRESET'].get_voltage(unit='V')) 
        dut['IBN'].set_current(IBN[-1],unit=I_unit)
        for I in IBP:
            pos = np.where(IBP==I)[0][0]
            dut['IBP'].set_current(I,unit=I_unit)
            time.sleep(0.5)
            IBP_meas[pos].append(dut['IBP'].get_current(unit=I_unit))
            waveform = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)[1]
            IBP_VOUT[pos].append(1000*(np.average(waveform)-baseline))
            IBP_VOUT_err[pos].append(1000*np.std(waveform))
            IBP_VRESET[pos].append(dut['VRESET'].get_voltage(unit='V')) 
    
    IBN_meas_err = [1 for i in range(0, len(IBN_meas))]
    IBP_meas_err = [0.1 for i in range(0, len(IBP_meas))]
    IBN_VRESET_err = [0.1 for i in range(0, len(IBN_meas))]
    IBP_VRESET_err = [0.1 for i in range(0, len(IBP_meas))]
    
    # Plotting IBN
    plt.figure(figsize=(16,9))
    for i in range(0, len(IBN_meas)):
        plt.errorbar(x=IBN_VRESET[i],y=IBN_VOUT[i], xerr=IBN_VRESET_err[i],yerr=IBN_VOUT_err[i], label='IBN = %.1f uA'%(IBN[i]), linestyle='None')
        #plt.scatter(IBN_VRESET[i], IBN_VOUT[i], label ='IBN = %.1f uA'%(IBN[i]))
    plt.grid()
    plt.xlabel('$V_{RESRT}$ / V')
    plt.ylabel('$\\Delta V$ / mV')
    plt.legend()
    plt.title( '$V_{RESRT}$ vs. $V_{Out}$ for different IBN - '+chip_version)
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBN_VRESET_VOUT.png')
    plt.show()

    IBN_meas_avrg = [np.average(IBN_meas[i]) for i in range(0, len(IBN_meas))]
    IBN_meas_avrg_err = np.sqrt(np.sum([IBN_meas_err[i]**2/len(IBN_meas_err) for i in range(0, len(IBN_meas))]))
    IBN_VOUT_avrg = [np.average(IBN_VOUT[i]) for i in range(0, len(IBN_VOUT))]
    IBN_VOUT_avrg_err = np.sqrt(np.sum([IBP_meas_err[i]**2/len(IBP_meas_err) for i in range(0, len(IBP_meas))]))
    IBN_VRESET = np.array(IBN_VRESET)
    IBN_VRESET_err = np.array(IBN_VOUT_err)
    IBN_VRESET_avrg = [np.average(IBN_VRESET[i]) for i in range(0, len(IBN_VRESET))]
    IBN_VRESET_avg_err = np.sqrt(np.sum([IBN_VRESET[i]**2/len(IBN_VRESET) for i in range(0, len(IBN_VRESET))]))

    IBN_Gain = np.array(IBN_VOUT_avrg)/np.array(IBN_VRESET_avrg)/1000
    IBN_Gain_err = np.sqrt((1/np.array(IBN_VRESET_avrg)/1000**2*np.array(IBN_VOUT_avrg_err))**2+(np.array(IBN_VOUT_avrg)/1000/np.array(IBN_VRESET_avrg)**2*IBN_VRESET_avg_err)**2)/1000
    popt_IBN_Gain, perr_IBN_Gain = double_err(function=func_lin, x=IBN_meas_avrg, x_error=IBN_meas_avrg_err, y=IBN_Gain, y_error=IBN_Gain_err, presets=[1,1])

    popt_IBN, perr_IBN =  double_err(function=func_lin, x=IBN_meas_avrg, x_error=IBN_meas_avrg_err, y=IBN_VOUT_avrg, y_error=IBN_VOUT_avrg_err, presets=[1,1])

    # Plot VOUT vs IBN 
    plt.figure(figsize=(16,9))
    plt.errorbar(x=IBN_meas_avrg,y=IBN_VOUT_avrg,xerr=IBN_meas_avrg_err,yerr=IBN_VOUT_avrg_err, linestyle="None")
    x_fit = np.linspace(np.min(IBN_meas_avrg)*0.95, np.max(IBN_meas_avrg)*1.05,100)
    plt.plot(x_fit, func_lin(popt_IBN,x_fit), label='$V_{Out}(I_{BP})=(%.3f\\pm%.3f) mV/uA\\cdot I_{BP}+(%.3f\\pm%.3f)$ mV'%(popt_IBN[0],perr_IBN[0],popt_IBN[1],perr_IBN[1]))
    plt.grid()
    plt.xlabel('$IBN$ / uA')
    plt.ylabel('$V_{Out}$ / mV')
    plt.legend()
    plt.title('$V_{Out}$ in dependency of IBN - '+chip_version)
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBN_VOUT.png')
    plt.close()

    # Plot IBN Gain vs IGN
    plt.figure(figsize=(16,9))
    plt.errorbar(x=IBN_meas_avrg,y=IBN_Gain,xerr=IBN_meas_avrg_err,yerr=IBN_Gain_err, linestyle="None")
    x_fit = np.linspace(np.min(IBN_meas_avrg)*0.95, np.max(IBN_meas_avrg)*1.05,100)
    plt.plot(x_fit, func_lin(popt_IBN_Gain,x_fit), label='$G(I_{BP})=(%.4f\\pm%.4f) 1/uA\\cdot I_{BP}+(%.4f\\pm%.4f)$ mV'%(popt_IBN_Gain[0],perr_IBN_Gain[0],popt_IBN_Gain[1],perr_IBN_Gain[1]))
    plt.grid()
    plt.xlabel('$IBN$ / uA')
    plt.ylabel('Gain $G$')
    plt.legend()
    plt.title('Gain $G$ in dependency of IBN - '+chip_version)
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBN_Gain.png')
    plt.close()
    np.savetxt('./Test_Samples/Reset_Probe/IBN_Gain.csv', (popt_IBN_Gain, perr_IBN_Gain), delimiter=',')

    # Plotting IBP
    plt.figure(figsize=(16,9))
    for i in range(0, len(IBP_meas)):
        plt.errorbar(x=IBP_VRESET[i],y=IBP_VOUT[i], xerr=IBP_VRESET_err[i],yerr=IBP_VOUT_err[i], label='IBN = %.1f uA'%(IBP[i]), linestyle='None')
    plt.grid()
    plt.xlabel('$V_{RESRT}$ / V')
    plt.ylabel('$\\Delta V$ / mV')
    plt.legend()
    plt.title( '$V_{RESRT}$ vs. $\\Delta V$ for different IBP - '+chip_version)
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBP_VRESET_VOUT.png')
    plt.close()

    IBP_meas_avrg = [np.average(IBP_meas[i]) for i in range(0, len(IBP_meas))]
    IBP_meas_avrg_err = np.sqrt(np.sum([IBP_meas_err[i]**2/len(IBP_meas_err) for i in range(0, len(IBP_meas_err))]))
    IBP_VOUT_avrg = [np.average(IBP_VOUT[i]) for i in range(0, len(IBP_VOUT))]
    IBP_VOUT_avrg_err = np.sqrt(np.sum([IBP_meas_err[i]**2/len(IBP_meas_err) for i in range(0, len(IBP_meas_err))]))
    IBP_VRESET = np.array(IBP_VRESET)
    IBP_VRESET_err = np.array(IBP_VOUT_err)
    IBP_VRESET_avrg = [np.average(IBP_VRESET[i]) for i in range(0, len(IBP_VRESET))]
    IBP_VRESET_avg_err = np.sqrt(np.sum([IBP_VRESET[i]**2/len(IBP_VRESET) for i in range(0, len(IBP_VRESET))]))

    IBP_Gain = np.array(IBP_VOUT_avrg)/np.array(IBP_VRESET_avrg)/1000
    IBP_Gain_err = np.sqrt((1/np.array(IBP_VRESET_avrg)/1000**2*np.array(IBP_VOUT_avrg_err))**2+(np.array(IBP_VOUT_avrg)/1000/np.array(IBP_VRESET_avrg)**2*np.array(IBP_VRESET_avg_err))**2)/1000
    popt_IBP_Gain, perr_IBP_Gain = double_err(function=func_lin, x=IBP_meas_avrg, x_error=IBP_meas_avrg_err, y=IBP_Gain, y_error=IBP_Gain_err, presets=[1,1])

    popt_IBP, perr_IBP = double_err(function=func_lin, x=IBP_meas_avrg, x_error=IBP_meas_avrg_err, y=IBP_VOUT_avrg, y_error=IBP_VOUT_avrg_err, presets=[1,1])

    print(popt_IBP, perr_IBP)
    plt.figure(figsize=(16,9))
    plt.errorbar(x=IBP_meas_avrg,y=IBP_VOUT_avrg,xerr=IBP_meas_avrg_err,yerr=IBP_VOUT_avrg_err, linestyle="None")
    x_fit = np.linspace(np.min(IBP_meas_avrg), np.max(IBP_meas_avrg),100)
    plt.plot(x_fit, func_lin(popt_IBP,x_fit), label='$V_{Out}(I_{BP})=(%.3f\\pm%.3f) mV/uA\\cdot I_{BP}+(%.3f\\pm%.3f)$ mV'%(popt_IBP[0], perr_IBP[0],popt_IBP[1], perr_IBP[1]))
    plt.grid()
    plt.xlabel('$IBP$ / uA')
    plt.ylabel('$V_{Out}$ / mV')
    plt.title('$V_{Out}$ in dependency of IBP - '+chip_version)
    plt.legend()
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBP_VOUT.png')
    plt.close()

    plt.figure(figsize=(16,9))
    plt.errorbar(x=IBP_meas_avrg,y=IBP_Gain,xerr=IBP_meas_avrg_err,yerr=IBP_Gain_err, linestyle="None")
    x_fit = np.linspace(np.min(IBP_meas_avrg), np.max(IBP_meas_avrg),100)
    plt.plot(x_fit, func_lin(popt_IBP_Gain,x_fit), label='$G(I_{BP})=(%.4f\\pm%.4f) 1/uA\\cdot I_{BP}+(%.4f\\pm%.4f)$'%(popt_IBP_Gain[0],perr_IBP_Gain[0],popt_IBP_Gain[1],perr_IBP_Gain[1]))
    plt.grid()
    plt.xlabel('$IBP$ / uA')
    plt.ylabel('Gain $G$')
    plt.legend()
    plt.title('Gain $G$ in dependency of IBP - '+chip_version)
    plt.savefig('Test_Samples/Reset_Probe/'+chip_version+'_IBP_Gain.png')
    plt.close()

    np.savetxt('./Test_Samples/Reset_Probe/IBP_Gain.csv', (popt_IBP_Gain, perr_IBP_Gain), delimiter=',')
    

if 'resetProbe' in sys.argv[1:]:
    reset_probe()

if 'ScanVRESET' in sys.argv[1:]:
    ScanVRESET()