# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#
# This script tests if one can deplete the AC coupled chip just by applying a positive 
# voltage to DIODE_HV while PW_BIAS and BACK_BIAS are at GND
#
# CHECK BEFORE YOU START THIS SCRIPT, IF THE SMU IS CONNECTED TO THE CORRECT PORTS!!!!
#
# DEACTIVATE AUTO CURRENT RANGE MANUALLY IN THE SMU!!! 
#

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import matplotlib.pyplot as plt
from lab_devices.sourcemeter import sourcemeter
from lab_devices.multimeter import multimeter
import time
import utils.plot_fit as pltfit
import numpy as np
from utils.initialize_measurement import initialize_measurement as init_meas
import utils.data_handler as dh

load_data, chip_version, image_path, data_path = init_meas('miscellaneous')
color=['red','orange', 'pink', 'green', 'purple', 'blue', 'gray']

if not load_data:
    try:
        dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
        dut.init()
        dut.boot_seq()
        dut.load_defaults(DIODE_HV=0, VRESET=0)
    except: pass 
    sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
    sm.init()
    sm.settings(voltage=0, current_limit=350*1e-6)

    sm_back_bias = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
    sm_back_bias.init()
    sm_back_bias.settings(voltage=0, current_limit=350*1e-6, voltage_limit=-12)
    
    smu_HV = False
    smu_GND = False
    try:
        sm_x = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_3.yaml", 'r'), Loader=yaml.Loader))
        sm_x.init()
        sm_x.settings(voltage=0, current_limit=350*1e-6, voltage_limit=3)
        smu_HV = True
    except: pass
    try:
        sm_GND = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_4.yaml", 'r'), Loader=yaml.Loader))
        sm_GND.init()
        sm_GND.settings(voltage=0, current_limit=350*1e-6, voltage_limit=3)
        smu_GND = True
    except: pass
    try:
        sm_5 = sourcemeter(yaml.load(open("./lab_devices/keithley_2400.yaml", 'r'), Loader=yaml.Loader))
        sm_5.init()
        sm_5.settings(voltage=0, current_limit=350*1e-6, voltage_limit=3)
    except: pass
    #try:
     #   mm = multimeter(yaml.load(open("./lab_devices/keithley_2001.yaml", 'r'), Loader=yaml.Loader))
     #   mm.init()
    #except: pass

    
    sm['sourcemeter'].set_current_autorange() # Turn off AUTO range manually!
    sm_back_bias['sourcemeter'].set_current_autorange() # Turn off AUTO range manually!
    sm_x['sourcemeter'].set_current_autorange() # Turn off AUTO range manually!

def PW_BACK_IV(PW_BIAS_SEL=[], delta_max_bias = 7, DIODE_HV=0):
    if smu_HV:sm_x.settings(voltage=DIODE_HV, current_limit=350*1e-6, voltage_limit=3)
    else: dut.load_defaults(DIODE_HV=DIODE_HV)
    time.sleep(1)
    back_voltage_list = []
    back_current_list = []
    pw_current_list = []
    DIODE_HV_current_list = []

    back_voltage = []
    back_current = []
    pw_current = []
    DIODE_HV_current = []

    floating = np.genfromtxt('./output/miscellaneous/data/back_floating.csv', delimiter=',', skip_header=1)
    PW_floating_in = floating[0:,0]
    BACK_floating = floating[0:,1]


    for PW in PW_BIAS_SEL:
        back_voltage = []
        back_current = []
        pw_current = []
        BACK_BIAS = []
        DIODE_HV_current = []
        sm['sourcemeter'].set_voltage(PW)
        if PW >= -2:
            BACK_BIAS = [PW-i for i in range(0,delta_max_bias)]
        else:
            BACK_BIAS = [PW-i for i in range(0,delta_max_bias)]
        BACK_BIAS.append(BACK_floating[np.where(PW_floating_in==PW)[0][0]])
        BACK_BIAS = -np.sort(-np.array(BACK_BIAS))
        #BACK_BIAS = np.sort(np.array(BACK_BIAS))

        for V in BACK_BIAS:
            sm_back_bias['sourcemeter'].set_voltage(V)
            time.sleep(1.5)
            back_voltage.append(float(sm_back_bias['sourcemeter'].get_voltage()))
            for i in range(0,2): bk_current =float(sm_back_bias['sourcemeter'].get_current())*1e6 
            back_current.append(bk_current)
            pw_current.append(float(sm['sourcemeter'].get_current())*1e6)
            if smu_HV: DIODE_HV_current.append(float(sm_x['sourcemeter'].get_current())*1e6)
            print('BACK Voltage=%.2f, BACK current=%.2f, PW current=%.2f, DIODE_HV current=%.2f'%(back_voltage[-1], back_current[-1], pw_current[-1], DIODE_HV_current[-1]))

        #pltfit.beauty_plot(xlabel='BACK_BIAS / V', ylabel='Current I / uA', title='PW_BIAS=%iV'%(PW))
        #plt.plot(back_voltage, back_current, marker='x', label='BACK_BIAS')
        #plt.plot(back_voltage, pw_current, marker='x', label='PW_BIAS')
        #plt.legend()
        #plt.savefig('./output/miscellaneous/BACK_BIAS_IV_curve_DIODE_HV_%i.pdf'%(PW), bbox_inches='tight')
        #plt.show()
        #plt.close()
        back_voltage_list.append(back_voltage)
        back_current_list.append(back_current)
        pw_current_list.append(pw_current)
        DIODE_HV_current_list.append(DIODE_HV_current)

    pltfit.beauty_plot(xlabel='BACK_BIAS / V', ylabel='Current I / uA', title='%s chip (DIODE_HV=%.2fV)'%(chip_version, DIODE_HV))
    for i in range(len(back_voltage_list)):
        plt.plot(back_voltage_list[i], back_current_list[i], marker='x', linestyle='-', label='PW_BIAS=%iV'%(PW_BIAS_SEL[i]), color=color[i])
        plt.plot(back_voltage_list[i], pw_current_list[i], marker='x', linestyle='--', color=color[i])
        if smu_HV: plt.plot(back_voltage_list[i], DIODE_HV_current_list[i], marker='x', linestyle='-.', color=color[i])
    plt.legend()
    plt.savefig('./output/miscellaneous/BACK_BIAS_IV_curve_different_PW_DIODE_HV_%.2f.pdf'%(DIODE_HV), bbox_inches='tight')
    plt.show()
    plt.close()

    
def current_sum(PW_BIAS_SEL = [0, -1, -2, -3, -4, -5, -6], DIODE_HV = 1.8, x=1.8, x_name='DIODE_HV', VRESET=None):

    # Disconnect dut from GPAC 
    # Connect all 4 SMUs (1xPW, 1xBACK, 1x(NWELL,LOGIC_DNWELL,NRING), 1xGND)
 
    floating = np.genfromtxt('./output/miscellaneous/data/back_floating.csv', delimiter=',', skip_header=1)
    PW_floating_in = floating[0:,0]
    BACK_floating = floating[0:,1]
    sm_x['sourcemeter'].set_voltage(x)

    back_voltage = []
    back_current = []
    pw_current = []
    x_current = []
    GND_current = []

    for PW in PW_BIAS_SEL:
        DIODE_HV_current = []
        sm['sourcemeter'].set_voltage(PW)
        sm_back_bias['sourcemeter'].set_voltage(PW)
        
        time.sleep(1)
        pw_current.append(float(sm['sourcemeter'].get_current())*1e6)
        back_voltage.append(float(sm_back_bias['sourcemeter'].get_voltage()))
        back_current.append(float(sm_back_bias['sourcemeter'].get_current())*1e6)
        x_current.append(float(sm_x['sourcemeter'].get_current())*1e6)
        GND_current.append(float(sm_GND['sourcemeter'].get_current())*1e6)
    xname_and = x_name.replace('+',"=")
    pltfit.beauty_plot(xlabel='PW_BIAS = BACK_BIAS / V', ylabel='current I / uA', title='%s chip (%s=%.2fV)'%(chip_version, xname_and, x))
    plt.plot(PW_BIAS_SEL, pw_current, label='PW_BIAS', marker='x')
    plt.plot(PW_BIAS_SEL, back_current, label='BACK_BIAS', marker='x')
    plt.plot(PW_BIAS_SEL, x_current, label=x_name, marker='x')
    plt.plot(PW_BIAS_SEL, GND_current, label='GND', marker='x')
    plt.plot(PW_BIAS_SEL, np.array(back_current)+np.array(x_current)+np.array(pw_current)+np.array(GND_current), label='Sum', marker='x', color='black', linestyle='--')
    plt.legend()
    plt.savefig('./output/miscellaneous/PW_BACK_%s__DIODE_HV_%.2f_VRESET_%s_IV_curve_%s.pdf'%(x_name, DIODE_HV, str(VRESET), chip_version), bbox_inches='tight')
    plt.show()

def simplify_chip_potential(DIODE_HV_SEL=np.arange(0,1.9,0.1), BACK_BIAS_SEL = np.linspace(0, -3, 11), n_title='floating'):

    # Try to enforce simplified model by setting PW=VDD=GND
    # DIODE_HV = 0V-1.8V
    # Varying BACK in small negative voltages

    PW_current = []
    BACK_BIAS_current = []
    DIODE_HV_current = []
    GND_current = []
    if not load_data:     
        sm['sourcemeter'].set_voltage(0)
        sm_back_bias['sourcemeter'].set_voltage(0)

        for DIODE_HV in DIODE_HV_SEL:
            sm_x['sourcemeter'].set_voltage(DIODE_HV)
            PW_current_meas = []
            BACK_BIAS_current_meas = []
            DIODE_HV_current_meas = []
            GND_current_meas = []
            for BACK_BIAS in BACK_BIAS_SEL:
                sm_back_bias['sourcemeter'].set_voltage(BACK_BIAS)
                time.sleep(1)
                PW_current_meas.append(float(sm['sourcemeter'].get_current())*1e6)
                BACK_BIAS_current_meas.append(float(sm_back_bias['sourcemeter'].get_current())*1e6)
                DIODE_HV_current_meas.append(float(sm_x['sourcemeter'].get_current())*1e6)
                GND_current_meas.append(float(sm_GND['sourcemeter'].get_current())*1e6)
            PW_current.append(PW_current_meas)
            BACK_BIAS_current.append(BACK_BIAS_current_meas)
            DIODE_HV_current.append(DIODE_HV_current_meas)
            GND_current.append(GND_current_meas)

        for i in range(len(DIODE_HV_SEL)):
            dh.save_data(data=[BACK_BIAS_SEL, PW_current[i], BACK_BIAS_current[i], DIODE_HV_current[i], GND_current[i]], header='BACK_BIAS_SEL, PW_current, BACK_BIAS_current, DIODE_HV_current, GND_current', output_path='./output/miscellaneous/data/simplify_chip_potential/simplify_chip_n_potential_%s_DIODE_HV_%.1f_%s.pdf'%(n_title,DIODE_HV_SEL[i], chip_version))
    else:
        for i in range(len(DIODE_HV_SEL)):
            data = np.genfromtxt('./output/miscellaneous/data/simplify_chip_n_potential_%s_DIODE_HV_%.1f_%s.pdf'%(n_title,DIODE_HV_SEL[i], chip_version), delimiter=',')
            PW_current.append(data[1:,1])
            BACK_BIAS_current.append(data[1:,2])
            DIODE_HV_current.append(data[1:,3])
            GND_current.append(data[1:,4])
    fig, ax = plt.subplots(int(len(DIODE_HV_SEL)/2+1), 2, squeeze=True)
    fig.suptitle('%s chip (LOGIC_DNWELL=NWELL_RING=%s, VDD=PWELL=GND)'%(chip_version, n_title))
    fig.set_figheight(30)
    fig.set_figwidth(25)
    ax = ax.ravel()
    for i in range(len(DIODE_HV_SEL)):
        ax[i].plot(BACK_BIAS_SEL, PW_current[i], marker='x', label='PWELL_BIAS')
        ax[i].plot(BACK_BIAS_SEL, BACK_BIAS_current[i],marker='x', label='BACK_BIAS', linestyle='--')
        ax[i].plot(BACK_BIAS_SEL, DIODE_HV_current[i], marker='x', label='DIODE_HV', linestyle='-.')
        ax[i].plot(BACK_BIAS_SEL, GND_current[i], marker='x', label='GND', linestyle=':')    
        ax[i].plot(BACK_BIAS_SEL, np.array(PW_current[i])+np.array(BACK_BIAS_current[i])+np.array(DIODE_HV_current[i])+np.array(GND_current[i]),marker='x', color='black', alpha=0.6, label='Sum')
        ax[i].set_title('DIODE_HV=%.1fV'%(DIODE_HV_SEL[i]))
        ax[i].grid()
        ax[i].set_xlabel('BACK_BIAS / V')
        ax[i].set_ylabel('current I / $\\mu$A')
        ax[i].legend()
        plt.gca().set_prop_cycle(None)

    for i in range(len(ax)-len(DIODE_HV_SEL)):
        fig.delaxes(ax[-1-i])
   
    plt.savefig('./output/miscellaneous/simplify_chip_n_potential_%s_%s.pdf'%(n_title, chip_version), bbox_inches='tight')
    
    plt.show()

def simplify_chip_potential_GND_PWELL_COMBINED_SMU(DIODE_HV_SEL=np.arange(0,1.9,0.1), BACK_BIAS_SEL = np.linspace(0, -3, 11), n_title='floating', VDD=3.7):

    # Try to enforce simplified model by setting PW=VDD=GND
    # DIODE_HV = 0V-1.8V
    # Varying BACK in small negative voltages
    # Use here the sm for VDD exclusively 

    
    VDD_current = []
    BACK_BIAS_current = []
    DIODE_HV_current = []
    GND_current = []
    #PW_current = []
    if not load_data:     
        sm.settings(voltage=VDD, current_limit=2*1e-3)
        sm_back_bias['sourcemeter'].set_voltage(0)
        sm_GND.settings(voltage=0, current_limit=2*1e-3, voltage_limit=3)
        #sm_PW_current = sm_5
        #sm_PW_current.settings(voltage=0, current_limit=2*1e-3, voltage_limit=3)

        for DIODE_HV in DIODE_HV_SEL:
            sm_x['sourcemeter'].set_voltage(DIODE_HV)
            VDD_current_meas = []
            BACK_BIAS_current_meas = []
            DIODE_HV_current_meas = []
            GND_current_meas = []
            #BACK_BIAS = np.sort(BACK_BIAS_SEL)
            #PW_current_meas = []
            for BACK_BIAS in BACK_BIAS_SEL:
                sm_back_bias['sourcemeter'].set_voltage(BACK_BIAS)
                time.sleep(1)
                VDD_current_meas.append(float(sm['sourcemeter'].get_current())*1e6)
                BACK_BIAS_current_meas.append(float(sm_back_bias['sourcemeter'].get_current())*1e6)
                DIODE_HV_current_meas.append(float(sm_x['sourcemeter'].get_current())*1e6)
                GND_current_meas.append(float(sm_GND['sourcemeter'].get_current())*1e6)
                #PW_current_meas.append(float(sm_5['sourcemeter'].get_current().split(',')[1])*1e6)

            VDD_current.append(VDD_current_meas)
            BACK_BIAS_current.append(BACK_BIAS_current_meas)
            DIODE_HV_current.append(DIODE_HV_current_meas)
            GND_current.append(GND_current_meas)
            #PW_current.append(PW_current_meas)
        
        sm['sourcemeter'].off()
        sm_x['sourcemeter'].off()
        sm_back_bias['sourcemeter'].off()
        sm_GND['sourcemeter'].off()
        #sm_PW_current['sourcemeter'].off()

        for i in range(len(DIODE_HV_SEL)):
            #dh.save_data(data=[BACK_BIAS_SEL, VDD_current[i], BACK_BIAS_current[i], DIODE_HV_current[i], GND_current[i], PW_current[i]], header='BACK_BIAS_SEL, VDD_current, VDD_current, DIODE_HV_current, GND_current, PW_current', output_path='./output/miscellaneous/data/simplify_chip_potential/simplify_chip_n_potential_%s_DIODE_HV_%.1f_VDD_%.2f_%s.csv'%(n_title,DIODE_HV_SEL[i],VDD, chip_version))
            dh.save_data(data=[BACK_BIAS_SEL, VDD_current[i], BACK_BIAS_current[i], DIODE_HV_current[i], GND_current[i]], header='BACK_BIAS_SEL, VDD_current, VDD_current, DIODE_HV_current, GND_current', output_path='./output/miscellaneous/data/simplify_chip_potential/simplify_chip_n_potential_%s_DIODE_HV_%.1f_VDD_%.2f_%s.csv'%(n_title,DIODE_HV_SEL[i],VDD, chip_version))
    else:
        for i in range(len(DIODE_HV_SEL)):
            data = np.genfromtxt('./output/miscellaneous/data/simplify_chip_potential/simplify_chip_n_potential_%s_DIODE_HV_%.1f_VDD_%.2f_%s.csv'%(n_title,DIODE_HV_SEL[i],VDD, chip_version), delimiter=',')
            VDD_current.append(data[1:,1])
            BACK_BIAS_current.append(data[1:,2])
            DIODE_HV_current.append(data[1:,3])
            GND_current.append(data[1:,4])
            #PW_current.append(data[1:,5])
    fig, ax = plt.subplots(int(len(DIODE_HV_SEL)/2+1), 2, squeeze=True)
    fig.suptitle('%s chip (LOGIC_DNWELL=NWELL_RING=%s, PWELL=GND, VDD=%.2fV)'%(chip_version, n_title, VDD))
    fig.set_figheight(30)
    fig.set_figwidth(25)
    ax = ax.ravel()
    for i in range(len(DIODE_HV_SEL)):
        ax[i].plot(BACK_BIAS_SEL, VDD_current[i], marker='x', label='VDD')
        ax[i].plot(BACK_BIAS_SEL, BACK_BIAS_current[i],marker='x', label='BACK_BIAS', linestyle='--')
        ax[i].plot(BACK_BIAS_SEL, DIODE_HV_current[i], marker='x', label='DIODE_HV', linestyle='-.')
        ax[i].plot(BACK_BIAS_SEL, GND_current[i], marker='x', label='GND', linestyle=':')    
        #ax[i].plot(BACK_BIAS_SEL, PW_current[i], marker='x', label='PW', linestyle=':')    
        ax[i].plot(BACK_BIAS_SEL, np.array(VDD_current[i])+np.array(BACK_BIAS_current[i])+np.array(DIODE_HV_current[i])+np.array(GND_current[i]),marker='x', color='black', alpha=0.6, label='Sum')
        ax[i].set_title('DIODE_HV=%.1fV'%(DIODE_HV_SEL[i]))
        ax[i].grid()
        ax[i].set_xlabel('BACK_BIAS / V')
        ax[i].set_ylabel('current I / $\\mu$A')
        ax[i].legend()
        plt.gca().set_prop_cycle(None)

    for i in range(len(ax)-len(DIODE_HV_SEL)):
        fig.delaxes(ax[-1-i])
   
    plt.savefig('./output/miscellaneous/simplify_chip_n_potential_%s_VDD_%.2f_%s.pdf'%(n_title,VDD, chip_version), bbox_inches='tight')
    
    plt.show()

#PW_BACK_IV(PW_BIAS_SEL = [0, -1, -2, -3, -4, -5, -6], DIODE_HV=1.8)
#current_sum(PW_BIAS_SEL = np.arange(0, -6.1, -0.1), DIODE_HV=0, x=0, x_name='DIODE_HV+NWELL_RING+DNWELL_LOGIC', VRESET=0.4)
#current_sum(PW_BIAS_SEL = np.arange(0, -6.1, -0.1), DIODE_HV=1.8, x=1.8, x_name='DIODE_HV+NWELL_RING+DNWELL_LOGIC+VDD')
#current_sum(PW_BIAS_SEL = np.arange(0, -6.1, -0.1), DIODE_HV=2.8, x=2.8, x_name='DIODE_HV+NWELL_RING+DNWELL_LOGIC+VDD', VRESET=0.0)
#simplify_chip_potential(DIODE_HV_SEL=np.arange(0, 1.9, 0.2), n_title='floating')
#simplify_chip_potential_GND_PWELL_COMBINED_SMU(DIODE_HV_SEL=np.arange(1.8, 4.7, 0.2), n_title='floating', VDD=3.7)
#simplify_chip_potential_GND_PWELL_COMBINED_SMU(DIODE_HV_SEL=[3.7, 4.0, 4, 4.5, 5], n_title='GND', VDD=3.7)
simplify_chip_potential_GND_PWELL_COMBINED_SMU(DIODE_HV_SEL=[4, 4], n_title='GND', VDD=3.5)