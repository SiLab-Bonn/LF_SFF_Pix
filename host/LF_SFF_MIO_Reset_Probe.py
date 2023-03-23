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

#reset_probe()
