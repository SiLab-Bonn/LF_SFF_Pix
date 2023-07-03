# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                                
#      VSRC2 __ DIODE_HV                    
#           |   | PW_BIAS_________SMU______ 
# -----------------------                  |
# | MIO | GPIO | LF_SFF |       MIO------Computer
# -----------------------            USB    |    
#        Pixel  10 |                        | RJ45
#        Matrix 1  |                        |     
#                  |______________________Oszi
#
# This script analyses the DC output voltage for different VRESETs and PWELL_BIAS 
# combinations
#

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
from lab_devices.conifg.config_handler import update_config

import utils.plot_fit as pltfit
from host.bode_plot_analyzer import analyse_bode_plot
import utils.data_handler as data_handler
from utils.initialize_measurement import initialize_measurement as init_meas
import matplotlib.pyplot as plt
import yaml
import sys
import time
    
import logging
from lab_devices.conifg.config_handler import update_config

from lab_devices.sourcemeter import sourcemeter
import utils.pulse_analyzer as pa 
from scipy.stats import norm
import matplotlib.mlab as mlab
import random as ran
import numpy as np


#####
# Configure experiment
#####
load_data, chip_version, image_path, data_path = init_meas('PWELL_VRESET_Investigation')
if not load_data:
    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.boot_seq()
    if chip_version == 'AC':
        dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=1.8)
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage())
        print('ADC_REF:' , dut['ADC_REF'].get_voltage())
    else:
        dut.load_defaults(VRESET=0, DIODE_HV=dut.get_DC_offset(chip_version=chip_version))
        print('DIODE_HV: ', dut['DIODE_HV'].get_voltage(),'V')


    oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_tds_3034b.yaml", 'r'), Loader=yaml.Loader))
    oszi.init()
    oszi.load_PWELL_VRESET_conifg()
    
    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()

#####
# This test iterates through different PWELL_SELECTION with a fixed VRESET
#####
def PWELL_VRESET_influence(VRESET, PWELL_SELECTION):
    if not load_data:
        dut['VRESET'].set_voltage(VRESET)
        VOUT = []
        VOUT_err = []
        I_smu = []
        for PW_BIAS in PWELL_SELECTION:
            sm.pixel_depletion(PW_BIAS=PW_BIAS)
            time.sleep(2)
            waveform = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
            waveform_x = oszi.gen_waveform_x(waveform)
            waveform = np.array(waveform[1])
            VOUT.append(np.average(waveform))
            VOUT_err.append(np.std(waveform))
            I_smu.append(sm['sourcemeter'].get_current())
            print('\n---------------\nVRESET, PW_BIAS, VOUT, I_SMU')
            print(VRESET, PW_BIAS, VOUT[-1],I_smu[-1],'\n---------------')
            plt.plot(waveform_x, waveform)
            plt.plot(waveform_x, [VOUT[-1] for i in range(len(waveform))])
            plt.savefig(image_path+'control_pics/VRESET_'+str(VRESET)+'_'+str(PW_BIAS)+'.pdf',bbox_inches='tight')
            plt.close()
        data_handler.save_data(data=[PWELL_SELECTION, VOUT, VOUT_err, I_smu], output_path=data_path+'VRESET_'+str(VRESET)+'.csv', header='PWELL_SELECTION, VOUT, VOUT_err, I_smu')
    else:
        data = np.genfromtxt(data_path+'VRESET_'+str(VRESET)+'.csv', delimiter=',')
        PWELL_SELECTION = data[1:,0]
        VOUT = data[1:,1]
        VOUT_err = data[1:,2]
        I_smu = data[1:,3]
    
    pltfit.beauty_plot(xlabel='PW_BIAS / V', ylabel='$V_{Out}$', title='$V_{out}$ in dependence of PWELL_BIAS, no PIX_IN, VRESET=%.2fV'%(VRESET))
    plt.errorbar(x=PWELL_SELECTION, y=VOUT, yerr=VOUT_err, linestyle='None', marker='x')
    plt.savefig(image_path+'PWELL_VRESET_influence_VRESET_'+str(VRESET)+'.pdf',bbox_inches='tight')
    plt.close()
    pltfit.beauty_plot(xlabel='PW_BIAS / V', ylabel='$I_{SMU}$ / A', title='$I_{SMU}$ in dependence of PWELL_BIAS, no PIX_IN, VRESET=%.2fV'%(VRESET))
    plt.errorbar(x=PWELL_SELECTION, y=I_smu, linestyle='None', marker='x')
    plt.savefig(image_path+'PWELL_I_SMU_influence_VRESET_'+str(VRESET)+'.pdf',bbox_inches='tight')
    plt.close()
    return PWELL_SELECTION, VOUT, VOUT_err, I_smu

#####
# This test repeats the iteration throguh different PWELL for a selection of VRESET
#####
def compare_for_different_VRESET(VRESET_SEL=[0.1,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.8], PWELL_SELECTION=[0, -0.5, -1, -1.5, -2, -2.5, -3, -3.5, -4, -4.5, -5]):
    PWELL_SELECTION_meas, VOUT_meas, VOUT_err_meas, I_smu_meas = [],[],[],[]
    for VRESET in VRESET_SEL:
        PWELL_SELECTION, VOUT, VOUT_err, I_smu = PWELL_VRESET_influence(VRESET=VRESET, PWELL_SELECTION=PWELL_SELECTION)
        PWELL_SELECTION_meas.append(PWELL_SELECTION)
        VOUT_meas.append(VOUT)
        VOUT_err_meas.append(VOUT_err)
        I_smu_meas.append(I_smu)
    pltfit.beauty_plot(xlabel='PW_BIAS / V', ylabel='$V_{Out}$ / V', title='$V_{out}$ in dependency of PWELL_BIAS for different VRESET')
    for i in range(len(VRESET_SEL)):
        plt.errorbar(x=PWELL_SELECTION_meas[i], y=VOUT_meas[i], yerr=VOUT_err_meas[i], linestyle='None', marker='x', label='VRESET=%.2fV'%(VRESET_SEL[i]))
    plt.legend()
    plt.savefig(image_path+'PWELL_VRESET_influence_for_different_VRESETs.pdf',bbox_inches='tight')
    plt.show()
    
    pltfit.beauty_plot(xlabel='PW_BIAS / V', ylabel='$I_{SMU}$ / A', title='$I_{SMU}$ in dependency of PWELL_BIAS for different VRESET')
    for i in range(len(VRESET_SEL)):
        plt.errorbar(x=PWELL_SELECTION_meas[i], y=np.array(I_smu_meas[i]).astype(float), linestyle='None', marker='x', label='VRESET=%.2fV'%(VRESET_SEL[i]))
    plt.legend()
    plt.savefig(image_path+'PWELL_I_SMU_influence_for_different_VRESETs.pdf',bbox_inches='tight')
    plt.show()

compare_for_different_VRESET()