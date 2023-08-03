# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# --------------------------------------------------- ---------
#
# This script tests if one can deplete the AC coupled chip just by applying a positive 
# voltage to DIODE_HV while PW_BIAS and BACK_BIAS are at GND
#
# CHECK BEFORE YOU START THIS SCRIPT, IF THE SMU IS CONNECTED TO DIODE_HV!!!!
#

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import matplotlib.pyplot as plt
from lab_devices.sourcemeter import sourcemeter
import time
import utils.plot_fit as pltfit
import utils.data_handler as data_handler
import numpy as np
from utils.initialize_measurement import initialize_measurement as init_meas
import utils.data_handler as dh

load_data, chip_version, image_path, data_path = init_meas('miscellaneous')

time.sleep(3)
def record_IV_curve(voltage_max = 4.5):
    if not load_data:
        dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
        dut.init()
        dut.boot_seq()
        dut.load_defaults(VRESET = dut.get_DC_offset(chip_version='AC'))

        sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
        sm.init()
        sm.settings(voltage=0, current_limit=400*1e-6)

        sm_nwell_ring = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
        sm_nwell_ring.init()
        sm_nwell_ring.settings(voltage=0, current_limit=400*1e-6)

        voltage = np.arange(0, voltage_max+0.1, 0.1)
        current = []
        current_n_guard_ring = []
        for V in voltage:
            sm['sourcemeter'].set_voltage(V)
            sm_nwell_ring['sourcemeter'].set_voltage(V)
            time.sleep(0.1)
            current.append(float(sm['sourcemeter'].get_current())*1e6)
            current_n_guard_ring.append(float(sm_nwell_ring['sourcemeter'].get_current())*1e6)

        pltfit.beauty_plot(xlabel='Voltage / V', ylabel='Current I / uA')
        plt.plot(voltage, current, marker='x', label='DIODE_HV')
        plt.plot(voltage, current_n_guard_ring, marker='x', label='NWELL_RING')
        plt.legend()
        plt.savefig('./output/miscellaneous/DIODE_HV_IV_curve.pdf', bbox_inches='tight')
        plt.show()

        pltfit.beauty_plot(xlabel='Voltage / V', ylabel='Current I / uA', log_y=True)
        plt.plot(voltage, current, marker='x', label='DIODE_HV')
        plt.plot(voltage, current_n_guard_ring, marker='x', label='NWELL_RING')
        plt.legend()
        plt.savefig('./output/miscellaneous/DIODE_HV_IV_curve_log.pdf', bbox_inches='tight')
        plt.show()

        data_handler.save_data(data=[voltage, current], header='DIODE_HV, current', output_path='./output/miscellaneous/data/DIODE_HV_IV.csv')

def advanced_IV_curve_analysis(VDD_SEL=[1.8, 2, 2.5, 3, 3.5, 4], DIODE_HV_SEL = np.arange(3, 4.5, 0.1)):
    # PW_BIAS=BACK_BIAS=NWELL_RING=DNWELL_LOGIC=GND
    # remove DUT from GPAC
    if not load_data:
        sm_DIODE_HV = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
        sm_DIODE_HV.init()
        sm_DIODE_HV.settings(voltage=0, current_limit=400*1e-6)

        sm_VDD = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
        sm_VDD.init()
        sm_VDD.settings(voltage=0, current_limit=2*1e-3)

        sm_GND = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_3.yaml", 'r'), Loader=yaml.Loader))
        sm_GND.init()
        sm_GND.settings(voltage=0, current_limit=2*1e-3)

        current_DIODE_HV = []
        current_VDD = []
        current_GND = []

        for VDD in VDD_SEL:
            sm_VDD['sourcemeter'].set_voltage(VDD)
            current_DIODE_HV_meas = []
            current_VDD_meas = []
            current_GND_meas = []
            for DIODE_HV in DIODE_HV_SEL:
                sm_DIODE_HV['sourcemeter'].set_voltage(DIODE_HV)
                time.sleep(1)
                current_DIODE_HV_meas.append(float(sm_DIODE_HV['sourcemeter'].get_current())*1e6)
                current_VDD_meas.append(float(sm_VDD['sourcemeter'].get_current())*1e6)
                current_GND_meas.append(float(sm_GND['sourcemeter'].get_current())*1e6)
            current_DIODE_HV.append(current_DIODE_HV_meas)
            current_VDD.append(current_GND_meas)
            current_GND.append(current_GND_meas)

    sm_DIODE_HV['sourcemeter'].off()
    sm_GND['sourcemeter'].off()
    sm_VDD['sourcemeter'].off()

    fig, ax = plt.subplots(int(len(VDD_SEL)/2+1), 2, squeeze=True)
    fig.suptitle('%s chip (LOGIC_DNWELL=NWELL_RING=PWELL_BIAS=BACK_BIAS=GND)'%(chip_version))
    fig.set_figheight(30)
    fig.set_figwidth(25)
    ax = ax.ravel()
    for i in range(len(VDD_SEL)):
        ax[i].plot(DIODE_HV_SEL, current_DIODE_HV[i],marker='x', label='DIODE_HV', alpha=0.5)
        ax[i].plot(DIODE_HV_SEL, current_VDD[i], marker='x', label='VDD', alpha=0.5)
        ax[i].plot(DIODE_HV_SEL, current_GND[i],marker='x', label='GND', alpha=0.5)
        ax[i].plot(DIODE_HV_SEL, np.array(current_DIODE_HV[i])+np.array(current_GND[i])+np.array(current_VDD[i]),marker='x', label='Sum', color='black', alpha=0.5)
        ax[i].set_title('VDD=%.1fV'%(VDD_SEL[i]))
        ax[i].grid()
        ax[i].set_xlabel('DIODE_HV / V')
        ax[i].set_ylabel('current I / $\\mu$A')
        ax[i].legend()
        plt.gca().set_prop_cycle(None)
    for i in range(len(ax)-len(VDD_SEL)):
        fig.delaxes(ax[-1-i])

    plt.savefig('./output/miscellaneous/DIODE_HV_VDD_Scan.pdf', bbox_inches='tight')
    plt.show()

#record_IV_curve()

advanced_IV_curve_analysis()