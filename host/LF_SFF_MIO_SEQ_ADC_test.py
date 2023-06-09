# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#
# This script contains some test routines to check, if the Sequencer
# as well as the ADC is working properly, as well as some examples for 
# real data acquisition
#

import time
import numpy as np

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

from bitarray import bitarray
from lab_devices.sourcemeter import sourcemeter
import utils.pulse_analyzer as pa 
from scipy.stats import norm
import matplotlib.mlab as mlab
import random as ran

load_data, chip_version, image_path, data_path = init_meas('IR_LED')
if not load_data:
    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.boot_seq()
    if chip_version == 'AC':
        dut.load_defaults(VRESET=dut.get_DC_offset(chip_version=chip_version), DIODE_HV=0)
    else:
        dut.load_defaults(VRESET=0, DIODE_HV=dut.get_DC_offset(chip_version=chip_version))

    func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
    func_gen.init()

    #sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    #sm.init()
    #sm.pixel_depletion(PW_BIAS=-3)

def test_SEQ(dut, overhead, delta_trigger):
    dut['SEQ'].reset()
    dut['SEQ'].set_clk_divide(1)
    reset       = bitarray('0'+'0'*delta_trigger+'0'*overhead)
    trigger     = bitarray('0'*delta_trigger+'1'+'0'*overhead)
    adc_trigger = bitarray('1'+'0'*delta_trigger+'0'*overhead)

    seq_size  = len(trigger)
    dut['SEQ'].set_repeat_start(0) 
    dut['SEQ'].set_repeat(1)  # else records many events
    dut['SEQ'].set_size(len(adc_trigger))
    dut['SEQ']['RESET'][0:len(trigger)] =  reset
    dut['SEQ']['Trigger'][0:len(trigger)] =  trigger
    dut['SEQ']['ADC_Trigger'][0:len(trigger)] = adc_trigger
    dut['SEQ'].write()
    dut['SEQ'].start()

def read_adc(nSamples, adc_ch):
    data = dut.read_adc(nSamples, adc_ch)
    plt.plot(data, label=adc_ch, alpha=0.5)

def adc_test_offset(adc_ch='fadc0_rx'):
    freq = 1e3
    nSamples = 15000
    offset_list = [0.2,0.4,0.6,0.8,1.0, 1.2]
    colors = ['red', 'orange', 'purple', 'green', 'blue', 'navy']
    i = 0
    pltfit.beauty_plot(xlim=[0, nSamples])
    for offset in offset_list:
        dut['ADC_REF'].set_voltage(offset)
        func_gen.adc_test_config(0.2,dut['ADC_REF'].get_voltage(),1e3)
        data = dut.read_raw_adc(nSamples, adc_ch)
        data_max = np.max(data[100:-100])
        data_min = np.min(data[100:-100])
        data_avrg = (data_max-data_min)/2+data_min
        plt.plot(data, alpha= 0.7, label='ADC_REF='+str(offset)+'V, meas: '+str(np.round(dut['ADC_REF'].get_voltage(),3))+'V, funcgen offset='+str(np.round(float(func_gen['Pulser'].get_voltage_offset()),3))+'V, measured offset= '+str(round(data_avrg,0)) +', $V_{pp}$='+str(data_max-data_min),color=colors[i])
        plt.hlines(8000,-1e10,+1e10, colors='black')
        plt.hlines(data_avrg, -1e6, 1e6, alpha=0.5, color=colors[i], linestyles='--')
        i+=1
        print('Calibration:', 0.1/(data_max-data_min), 'V/Unit')
    plt.legend()
    plt.savefig('ADC_offset_test.pdf')
    plt.show()

def test_read_pulse():
    pulse_width = 0.3*1e-6
    test_SEQ(pulse_width)
    func_gen.load_IR_LED_ext_config(1.8, pulse_width, int(1/pulse_width*0.1))
    time.sleep(1)
    pltfit.beauty_plot(tight=False)
    for adc_ch in ['fadc0_rx','fadc1_rx','fadc2_rx','fadc3_rx']:
        data, data_err = dut.read_adc(adc_ch=adc_ch, nSamples=10000)
        plt.plot(data, label=adc_ch)
    plt.legend()
    plt.show()
    dut_config = update_config('./lab_devices/conifg/LF_SFF_SEQ_ADC_test.csv')

    while True:
        dut_config.check_config(dut)

# Wire up LED as well as trigger -> function generator
def read_test_input(adc_ch = 'fadc0_rx'):
    dut[adc_ch].reset()
    dut['sram'].reset()
    dut[adc_ch].set_data_count(100)
    dut[adc_ch].set_en_trigger(True)
    test_SEQ()
    dut[adc_ch].set_delay(10)
    dut[adc_ch].start()
    while not dut[adc_ch].is_done():
        pass
    data = dut['sram'].get_data() 
    data = data & 0x3fff
    plt.plot(data)
    plt.show()

# Wire up LED as well as trigger -> function generator
def demo_capture_one_event():
    nSamples=4096
    delta_trigger = 500
    overhead = nSamples*100
    pltfit.beauty_plot(figsize=[10,10],tight=False, xlabel='ADC data points', ylabel='Voltage / V', title='IR LED Pulse of 100ns', label_size=22)
    data, data_err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead)
    baseline, signal = pa.fast_triggered_signal(data=data, baseline_end=delta_trigger, skip_region=0, signal_duration=30)
    plt.plot(data)

    plt.savefig(image_path+'ADC_Test_Pulse.pdf',bbox_inches='tight')
    plt.hlines(baseline, 0, len(data), color='black')
    plt.hlines(signal, 0, len(data), color='black')
    plt.show()

# Wire up LED as well as trigger -> function generator
def demo_capture_multiple_events(n_events):
    nSamples=4096
    delta_trigger = 100
    overhead = nSamples
    pltfit.beauty_plot(figsize=[10,10],tight=False, xlabel='ADC data points', ylabel='Voltage / V', title='IR LED Pulse of 100ns', label_size=22)
    for i in range(n_events):
        time.sleep(1)
        data, data_err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead)
        plt.plot(data)
    plt.show()

# Wire up LED as well as trigger -> function generator
def demo_avrg_multiple_events(n_events):
    nSamples=4096
    delta_trigger = 100
    overhead = nSamples
    pltfit.beauty_plot(figsize=[10,10],tight=False, xlabel='ADC data points', ylabel='Voltage / V', title='IR LED Pulse of 100ns', label_size=22)
    data = np.zeros(nSamples)
    for i in range(n_events):
        time.sleep(1)
        data_meas, data_err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead)
        plt.plot(data_meas, alpha=0.5)
        if i != 0:
            data=(data+data_meas)/2
        else:
            data=data_meas    
    plt.plot(data, color='black')
    plt.show()

# Wire up LED as well as trigger -> function generator
def demo_fast_offline_event_analyse(n_events):
    nSamples=4096
    delta_trigger = 500
    overhead = nSamples
    if not load_data:
        data_baseline = []
        data_event = []
        for i in range(n_events):
            dut.reset(sleep=1e-1)
            print('event data: %i/%i'%(i+1,n_events))
            time.sleep(1e-1)
            data, err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead, calibrate_data=False)
            print(data)
            baseline, event = pa.fast_triggered_signal(data=data, baseline_end=delta_trigger, skip_region=0, signal_duration=30)
            data_baseline.append(baseline)
            data_event.append(event)
            data_handler.save_data([data,err], data_path+'demo.csv', 'data, err')
            plt.plot(data)
            plt.hlines(baseline, 0, len(data), color='black')
            plt.hlines(event, 0, len(data), color='black') 
            plt.savefig(image_path+'control_pics/'+str(i)+'.png',bbox_inches='tight')
            plt.show()
            plt.close()

        data_handler.save_data(data=[data_baseline, data_event], output_path=data_path+'demo_fast_offline_event_analyse.csv',header='baseline, events')
    else:
        data = np.round(np.genfromtxt(data_path+'demo_fast_offline_event_analyse.csv', delimiter=',')[1:],0)
        data_baseline = np.round(data,0)[:,0]
        data_event = np.round(data,0)[:,1]
    pltfit.beauty_plot(xlabel='ADC register entry', ylabel='# of hits', title=chip_version+ ': '+str(n_events)+' IR LED Pulses')
    binwidth = 1
    baseline_n, baseline_bins, baseline_patches = plt.hist(data_baseline,edgecolor='black', label='baseline', bins=range(int(min(data_baseline)), int(max(data_baseline)) + binwidth, binwidth), alpha=0.8)
    baseline_bins = [(baseline_bins[i+1]+baseline_bins[i])/2 for i in range(0, len(baseline_bins)-1)]
    baseline_popt, baseline_perr = pltfit.double_err(function=pltfit.func_gauss, x=baseline_bins, x_error=[0.01 for i in range(len(baseline_bins))], y=baseline_n, y_error=[0.01 for i in range(len(baseline_n))], presets=[np.mean(baseline_n),np.mean(baseline_bins),1,0])
    plt.plot(np.linspace(np.min(baseline_bins), np.max(baseline_bins),100), pltfit.func_gauss(p=baseline_popt, x=np.linspace(np.min(baseline_bins), np.max(baseline_bins),100)), color='black', linestyle='dashed', label='$\#_{baseline}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(baseline_popt[0], baseline_perr[0],baseline_popt[1], baseline_perr[1],baseline_popt[2], baseline_perr[2]))
    event_n, event_bins, event_patches = plt.hist(data_event,edgecolor='black', label='events', bins=range(int(min(data_event)), int(max(data_event)) + binwidth, binwidth), alpha=0.8)
    event_bins = [(event_bins[i+1]+event_bins[i])/2 for i in range(0, len(event_bins)-1)]
    event_popt, event_perr = pltfit.double_err(function=pltfit.func_gauss, x=event_bins, x_error=[0.01 for i in range(len(event_bins))], y=event_n, y_error=[0.01 for i in range(len(event_n))], presets=[np.mean(event_n),np.mean(event_bins),1,0])
    plt.plot(np.linspace(np.min(event_bins), np.max(event_bins),100), pltfit.func_gauss(p=event_popt, x=np.linspace(np.min(event_bins), np.max(event_bins),100)), color='black', linestyle='-.', label='$\#_{event}(x)=(%.2f\\pm%.2f)\\cdot\\exp{(\\frac{-(x-(%.2f\\pm%.2f))^2}{(%.2f\\pm%.2f)^2})}$'%(event_popt[0], event_perr[0],event_popt[1], event_perr[1],event_popt[2], event_perr[2]))
    plt.legend()
    plt.savefig(image_path+'demo_fast_offline_event_analysis.pdf',bbox_inches='tight')
    plt.show()

def demo_threshold_trigger(adc_ch='fadc0_rx', nSamples = 4096):
    dut.reset()
    dut[adc_ch].reset()
    dut['sram'].reset()
    
    dut[adc_ch].set_data_count(nSamples)
    dut[adc_ch].set_single_data(True)
    dut[adc_ch].set_threshold_trigger_value(30)
    dut[adc_ch].set_threshold_trigger(3)
    print('THRESHOLD MODE: ', dut[adc_ch].get_threshold_trigger_mode())
    print(dut[adc_ch].get_threshold_trigger_value())
    time.sleep(5)
    dut['sram'].reset()
    
    while not dut[adc_ch].is_done():
        pass
    i = 1
    delta_trigger=100
    overhead=nSamples
    while dut['sram'].get_FIFO_INT_SIZE()<=nSamples-1:
        print(dut['sram'].get_FIFO_INT_SIZE())
    lost = dut[adc_ch].get_count_lost()
    data = dut['sram'].get_data() 
    data = data & 0x3fff
    plt.plot(data)
    plt.show()

def demo_fit_offline_analysis(n_events):
    nSamples=4096
    delta_trigger = 500
    overhead = nSamples
    if not load_data:
        data_baseline = []
        data_event = []
        for i in range(n_events):
            dut.reset(sleep=1)
            print('event data: %i/%i'%(i+1,n_events))
            time.sleep(1)
            data, err = dut.read_triggered_adc(adc_ch='fadc0_rx',SEQ_config=test_SEQ, nSamples=nSamples, delta_trigger = delta_trigger, overhead=overhead, calibrate_data=False)
        data_handler.save_data(data=[data, err], output_path=data_path+'demo_fit_offline_event_analyse.csv',header='baseline, err')
    else:
        data_in = np.round(np.genfromtxt(data_path+'demo_fit_offline_event_analyse.csv', delimiter=',')[1:],0)
        data = np.round(data_in,0)[:,0]
        err = np.round(data_in,0)[:,1]

    x = np.linspace(0, len(data), len(data))
    print(len(x), len(data))
    plt.plot(data)
    err = [0.1 for i in range(len(x))]
    print(np.argmin(data))
    print(np.min(data)-np.average(data))
    preset = [500,1,1,12]
    popt, perr = pa.fit_landau(x=x, y=data, yerr=err, bounds=[0, len(x)],p=preset)
    print(popt)
    plt.plot(x, pltfit.func_landau(popt,np.array(x)), color='black')
    plt.show()

def online_SEQ():
    delta_trigger = 500
    overhead = 4096*ran.randrange(10,20)
    dut['SEQ'].reset()
    dut['SEQ'].set_clk_divide(1)
    np.random.rand()
    trigger     = bitarray('0'*delta_trigger+'1'+'0'*overhead)
    seq_size  = len(trigger)
    dut['SEQ'].set_repeat_start(0) 
    dut['SEQ'].set_repeat(0)  # else records many events
    dut['SEQ'].set_size(len(trigger))
    dut['SEQ']['Trigger'][0:len(trigger)] =  trigger
    dut['SEQ'].write()
    dut['SEQ'].start()


def online_analysis(n_events, adc_ch='fadc0_rx', fit = False, PW_BIAS=-2, control_plots=False):

    nSamples = 4096
    n_captured = 0
    n_tried_captures = 0
    if not load_data:
        sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
        sm.init()
        sm.pixel_depletion(PW_BIAS=PW_BIAS)
        dut['sram'].reset()
        dut[adc_ch].reset()
        online_SEQ()
        dut[adc_ch].set_delay(10)
        dut[adc_ch].set_data_count(nSamples)
        dut[adc_ch].set_single_data(True)
        dut[adc_ch].set_en_trigger(False)
        dut[adc_ch].start()

        captured_base = []
        captured_event = []
        while n_captured != n_events:
            n_tried_captures += 1
            while dut['sram'].get_FIFO_INT_SIZE()<=nSamples-1:
                pass
            data = dut['sram'].get_data() 
            data = data & 0x3fff
            if fit:
                base, event = pa.fit_exp(data=data,threshold_x=10, title=chip_version+': IR LED Pulse of 200ns, PW_BIAS='+str(PW_BIAS)+'V', threshold_y=10, control_plots=control_plots, image_path=image_path+'control_pics/online_analysis_demo_'+str(n_captured)+'.pdf', area = [4925,5025])
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
            
            dut.reset(1e-9)
            time.sleep(1e-6)
            dut[adc_ch].start()
        print('captured ', n_events, ' events in ', n_tried_captures, ' tries -> ', n_events/n_tried_captures*100,'%')
        data_handler.save_data([captured_base, captured_event], data_path+'online_analysis.csv', 'base, events')
    else:
        data = np.round(np.genfromtxt(data_path+'online_analysis.csv', delimiter=',')[1:],0)
        captured_base = np.round(data,0)[:,0]
        captured_event = np.round(data,0)[:,1]
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
    plt.show()

#demo_capture_one_event()
#demo_capture_multiple_events(n_events=10)
#demo_avrg_multiple_events(n_events=10)
#demo_fast_offline_event_analyse(n_events=2)
#demo_fit_offline_analysis(n_events=1)
online_analysis(100000, fit=True, control_plots=True, PW_BIAS=-2)
dut.close()
