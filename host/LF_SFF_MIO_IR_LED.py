# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                                 Function Generator________
#      VSRC2 __ DIODE_HV                    |               |
#           |   | PW_BIAS_________SMU_____  | RS232         |
# -----------------------                  ||               |
# | MIO | GPIO | LF_SFF |       MIO------Computer           |
# -----------------------            USB    |               |
#        Pixel  X  |                        | RJ45          |
#        Matrix Y  |                        |               |
#                  |______________________Oszi______________|__________IR-LED
#                            CH2                   CH1
#
# DO NOT USE PIXEL 10 OF PIXEL MATRIX 1! PIX_IN WILL MESS UP YOUR RESULTS!
# 
# The oscilloscope is only used for verification. Data is taken via the ADCs of 
# the GPAC
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
# The function generator is also completely controlled by this script. 
# Please verify that the IR-LED is connected with the right polarity:
#
#       ###
#      #   #
#      #   #
#      #####
#       # #
#       # #
#       # #
#       # #
#       # # GND
#       #
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
load_data, chip_version, image_path, data_path = init_meas('IR_LED')
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


    func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    func_gen.init()
    pulse_width = 100*1e-9 
    func_gen.load_IR_LED_ext_config(3.0, pulse_width, 10**6)

    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()


def triggered_offlines_analysis(n_events, PW_BIAS, fit=False, control_pics=False, adc='fadc0_rx', nSamples = 4096, delta_trigger=500, threshold_y = 150,  calibrate_data=False):
    overhead = nSamples
    ####
    # Take/Load data
    ####
    if not load_data:
        sm.pixel_depletion(PW_BIAS=PW_BIAS)
        data_baseline = []
        data_event = []
        data_event_time = []

        for i in range(n_events):
            while True:
                print('event data: %i/%i - ADC: %s, PW_BIAS: %.2f'%(i+1,n_events, adc, PW_BIAS))
                dut.reset(sleep=1e-1)
                time.sleep(2e-1)
                data, err = dut.read_triggered_adc(adc_ch=adc,SEQ_config=dut.single_signal_SEQ, nSamples=nSamples, delta_trigger=delta_trigger, overhead=overhead, calibrate_data=calibrate_data)
                if fit:
                    baseline, event, event_time = pa.fit_exp(data=data, title=chip_version+': IR LED Pulse of %.2fns,'%(pulse_width*1e9)+' PW_BIAS='+str(PW_BIAS)+'V', threshold_y=threshold_y, control_plots=control_pics, image_path=image_path+'control_pics/online_analysis_demo_'+str(PW_BIAS)+'_'+str(i)+'.pdf', smooth_data=False, calibrate_data=calibrate_data)
                else:
                    baseline, event, event_time = pa.fast_triggered_signal(data=data, baseline_end=delta_trigger, skip_region=0, signal_duration=30, title=chip_version+': IR LED Pulse of %.2fns,'%(pulse_width*1e9)+' PW_BIAS='+str(PW_BIAS)+'V', image_path=image_path+'control_pics/online_analysis_demo_'+str(PW_BIAS)+'_'+str(i)+'.pdf', control_pics=control_pics)
                if baseline and event:
                    data_event_time.append(event_time)
                    data_baseline.append(baseline)
                    data_event.append(event)
                    break
                else:
                    pass
        data_handler.save_data(data=[data_baseline, data_event, data_event_time], output_path=data_path+'demo_fast_offline_event_analyse_'+str(PW_BIAS)+'.csv',header='baseline, events, time tau')
    else:
        data = np.round(np.genfromtxt(data_path+'demo_fast_offline_event_analyse_'+str(PW_BIAS)+'.csv', delimiter=',')[1:],0)
        data_baseline = np.round(data,0)[:,0]
        data_event = np.round(data,0)[:,1]
        data_event_time = data[:,2]

    ####
    # Analyse data
    ####
    binwidth = 1
    pltfit.beauty_plot(xlabel='ADC register entry', ylabel='# of hits', title=chip_version+ ': '+str(n_events)+' IR LED Pulses')
    
    baseline_n, baseline_bins, baseline_patches = plt.hist(data_baseline,edgecolor='black', label='baseline', bins=range(int(min(data_baseline)), int(max(data_baseline)) + binwidth, binwidth), alpha=0.8)
    baseline_bins = [(baseline_bins[i+1]+baseline_bins[i])/2 for i in range(0, len(baseline_bins)-1)]
    baseline_popt, baseline_perr = pltfit.no_err(function=pltfit.func_gauss_no_offset, x=baseline_bins, y=baseline_n, presets=[np.max(baseline_n),np.mean(baseline_bins),1])
    x_base_gauss = np.linspace(np.min(baseline_bins)-10, np.max(baseline_bins)+10,1000)
    
    event_n, event_bins, event_patches = plt.hist(data_event,edgecolor='black', label='events', bins=range(int(min(data_event)), int(max(data_event)) + binwidth, binwidth), alpha=0.8)
    event_bins = [(event_bins[i+1]+event_bins[i])/2 for i in range(0, len(event_bins)-1)]
    event_popt, event_perr = pltfit.no_err(function=pltfit.func_gauss_no_offset, x=event_bins, y=event_n, presets=[np.max(event_n),np.mean(event_bins),1])
    x_event_gauss = np.linspace(np.min(event_bins)-10, np.max(event_bins)+10,1000)
    
    plt.plot(x_base_gauss, pltfit.func_gauss_no_offset(p=baseline_popt, x=x_base_gauss), color='black', linestyle='dashed', label='$\#_{baseline}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(baseline_popt[0], baseline_perr[0],baseline_popt[1], baseline_perr[1],baseline_popt[2], baseline_perr[2]))
    plt.plot(x_event_gauss, pltfit.func_gauss_no_offset(p=event_popt, x=x_event_gauss), color='black', linestyle='-.', label='$\#_{event}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(event_popt[0], event_perr[0],event_popt[1], event_perr[1],event_popt[2], event_perr[2]))
    plt.legend()
    plt.savefig(image_path+'triggered_offlines_analysis'+str(PW_BIAS)+'.pdf',bbox_inches='tight')
    plt.show()
    #plt.close()
    data_handler.save_data(data=[baseline_popt[1], event_popt[1], event_popt[2]], header='baseline_pos, event_pos, event_tau', output_path=data_path+'triggered_offlines_analysis'+str(PW_BIAS)+'.csv')
    return baseline_popt[1], event_popt[1], np.average(data_event_time)

def triggered_offline_analysis_range(PWELL_range, n_events, fit=True, control_pics=True, adc='fadc0_rx'):
    base_pos = []
    event_pos = []
    event_time_const = []
    if not load_data:
        for PW_BIAS in PWELL_range:
            base, event, event_time = triggered_offlines_analysis(n_events, PW_BIAS, fit=fit, control_pics=control_pics)
            base_pos.append(base)
            event_pos.append(event)
            event_time_const.append(event_time)
    else:
        for PW_BIAS in PWELL_range:
            data = np.genfromtxt(data_path+'triggered_offlines_analysis'+str(PW_BIAS)+'.csv', delimiter=',')
            base_pos.append(data[1][0])
            event_pos.append(data[1][1])
            event_time_const.append(data[1][2])
    pltfit.beauty_plot(figsize=[10,10],fontsize=20, xlabel='PWELL_BIAS / V', ylabel='$x_{base}-x_{event}$')
    plt.scatter(PWELL_range, y = np.array(base_pos)-np.array(event_pos))
    plt.savefig(image_path+'compare_different_PWELL_BIAS.pdf')
    plt.show()
    pltfit.beauty_plot(figsize=[10,10],fontsize=20, xlabel='PWELL_BIAS / V', ylabel='$\\tau$ / ADC units')
    plt.scatter(PWELL_range, y = event_time_const)
    plt.savefig(image_path+'compare_different_PWELL_BIAS_event_time.pdf')
    plt.show()  
 
####
# Brute force method to read a signal by periodically reading the ADC and searching for a signal
####
def untriggered_offline_analysis(n_events, adc_ch='fadc0_rx', fit = False, PW_BIAS=-2, control_plots=False, test_SEQ=False, nSamples = 4096, threshold_y = 150):
    ####
    # Take/Load data
    ####
    n_captured = 0
    n_tried_captures = 0
    if not load_data:
        sm.pixel_depletion(PW_BIAS=PW_BIAS)
        dut['sram'].reset()
        dut[adc_ch].reset()
        if test_SEQ : dut.pseudo_random_test_SEQ(overhead=100, delta_trigger=0)
        dut[adc_ch].set_delay(10)
        dut[adc_ch].set_data_count(nSamples)
        dut[adc_ch].set_single_data(True)
        dut[adc_ch].set_en_trigger(False)
        dut[adc_ch].start()
        print('RESETTED ADC')
        print('Starting Measurement')
        captured_base = []
        captured_event = []
        while n_captured != n_events:
            n_tried_captures += 1
            while dut['sram'].get_FIFO_INT_SIZE()<=nSamples-1:
                pass
            data = dut['sram'].get_data() 
            data = data & 0x3fff
            if fit:
                base, event, tau = pa.fit_exp(data=data, title=chip_version+': IR LED Pulse of %.2fns,'%(pulse_width*1e9)+' PW_BIAS='+str(PW_BIAS)+'V', threshold_y=150, control_plots=control_plots, image_path=image_path+'control_pics/online_analysis_demo_'+str(PW_BIAS)+'_'+str(n_tried_captures)+'.pdf', smooth_data=False)
            else:
                base, event = pa.online_analyser(data=data,threshold_x=10, threshold_y=40)
            if base and event:
                captured_base.append(base)
                captured_event.append(event)
                if event <=0:
                    time.sleep(2)
                n_captured += 1
                dut['sram'].reset()
                print(n_captured, '/', n_events)
            
            #dut.reset(1e-9)
            #time.sleep(1e-6)
            dut[adc_ch].start()
        print('captured ', n_events, ' events in ', n_tried_captures, ' tries -> ', n_events/n_tried_captures*100,'%')
        data_handler.save_data([captured_base, captured_event], data_path+'online_analysis.csv', 'base, events')
    else:
        data = np.round(np.genfromtxt(data_path+'online_analysis.csv', delimiter=',')[1:],0)
        captured_base = np.round(data,0)[:,0]
        captured_event = np.round(data,0)[:,1]
  
    ####
    # Analyse data
    ####  
    pltfit.beauty_plot(xlabel='ADC register entry', ylabel='# of hits', title=chip_version+ ': '+str(len(data))+' IR LED Pulses online detected without trigger (pulse width=200ns, PW_BIAS='+str(PW_BIAS)+'V)')
    binwidth = 1
    try:
        baseline_n, baseline_bins, baseline_patches = plt.hist(captured_base,edgecolor='black', label='baseline', bins=range(int(min(captured_base)), int(max(captured_base)) + binwidth, binwidth), alpha=0.8)        # data analysis
        baseline_bins = [(baseline_bins[i+1]+baseline_bins[i])/2 for i in range(0, len(baseline_bins)-1)]
        baseline_popt, baseline_perr = pltfit.double_err(function=pltfit.func_gauss, x=baseline_bins, x_error=[0.01 for i in range(len(baseline_bins))], y=baseline_n, y_error=[0.01 for i in range(len(baseline_n))], presets=[np.max(baseline_n), baseline_bins[np.argmax(baseline_n)], 2,0])
        plt.plot(np.linspace(np.min(baseline_bins), np.max(baseline_bins),10000), pltfit.func_gauss(p=baseline_popt, x=np.linspace(np.min(baseline_bins), np.max(baseline_bins),10000)), color='black', linestyle='dashed', label='$\#_{baseline}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(baseline_popt[0], baseline_perr[0],baseline_popt[1], baseline_perr[1],baseline_popt[2], baseline_perr[2]))
        
    except: pass
    event_n, event_bins, event_patches = plt.hist(captured_event,edgecolor='black', label='IR PULSE', bins=range(int(min(captured_event)), int(max(captured_event)) + binwidth, binwidth), alpha=0.8)        # data analysis
    
    try:
        event_bins = [(event_bins[i+1]+event_bins[i])/2 for i in range(0, len(event_bins)-1)]
        event_popt, event_perr = pltfit.double_err(function=pltfit.func_gauss, x=event_bins, x_error=[0.01 for i in range(len(event_bins))], y=event_n, y_error=[0.01 for i in range(len(event_n))], presets=[np.max(event_n),event_bins[np.argmax(event_n)],4,0])
        plt.plot(np.linspace(np.min(event_bins), np.max(event_bins),10000), pltfit.func_gauss(p=event_popt, x=np.linspace(np.min(event_bins), np.max(event_bins),10000)), color='black', linestyle='-.', label='$\#_{event}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(event_popt[0], event_perr[0],event_popt[1], event_perr[1],event_popt[2], event_perr[2]))
    except: pass
    plt.legend()
    plt.savefig(image_path+'online_analysis_demo.pdf', bbox_inches='tight')
    dut.close()
    plt.show()


triggered_offlines_analysis(n_events=10, fit=True, control_pics=True, PW_BIAS=-3, adc = 'fadc0_rx', delta_trigger=2024, threshold_y=150)
#untriggered_offline_analysis(n_events=1000, adc_ch='fadc0_rx', fit = True, PW_BIAS=-3, control_plots=True, test_SEQ=True)

