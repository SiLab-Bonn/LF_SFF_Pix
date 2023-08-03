# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# --------------------------------------------------- ---------
#
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


sm_VDD = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm_VDD.init()
sm_VDD.settings(voltage=0, current_limit=2*1e-3)

sm_GND = sourcemeter(yaml.load(open("./lab_devices/keithley_2410_2.yaml", 'r'), Loader=yaml.Loader))
sm_GND.init()
sm_GND.settings(voltage=0, current_limit=2*1e-3)

def VDD_scan(VDD_SEL=np.arange(0,4, 0.1)):
    VDD_current = []
    GND_current = []

    for VDD in VDD_SEL:
        sm_VDD['sourcemeter'].set_voltage(VDD)
        time.sleep(2)
        VDD_current.append(float(sm_VDD['sourcemeter'].get_current())*1e6)
        GND_current.append(float(sm_GND['sourcemeter'].get_current())*1e6)
    
    sm_VDD['sourcemeter'].off()
    sm_GND['sourcemeter'].off()

    pltfit.beauty_plot(title='%s chip:VDD IV-curve (PW_BIAS=BACK_BIAS=DIODE_HV=NWELL_RING=LOGIC_DNWELL=floating)'%(chip_version), xlabel='VDD / V', ylabel='current I / $\\mu$A')
    plt.plot(VDD_SEL, VDD_current, label='VDD', marker='x')
    plt.plot(VDD_SEL, GND_current, label='GND', marker='x')
    plt.plot(VDD_SEL, np.array(GND_current)+np.array(VDD_current), label='Sum', color='black', marker='x')
    plt.legend()
    plt.savefig('./output/miscellaneous/VDD_IV_curve_%s.pdf'%(chip_version), bbox_inches='tight')
    plt.show()


def VDD_current_over_time(VDD=3, control_pics=True):
    sm_VDD['sourcemeter'].on()
    sm_GND['sourcemeter'].on()
    sm_VDD['sourcemeter'].set_voltage(VDD)
    VDD_current = []
    GND_current = []
    for i in range(30):
        time.sleep(2)
        VDD_current.append(float(sm_VDD['sourcemeter'].get_current())*1e6)
        GND_current.append(float(sm_GND['sourcemeter'].get_current())*1e6)
    sm_VDD['sourcemeter'].set_voltage(0)
    time.sleep(1)
    sm_VDD['sourcemeter'].off()
    sm_GND['sourcemeter'].off()
    if control_pics:
        pltfit.beauty_plot(title='%s chip: VDD IV-curve (PW_BIAS=BACK_BIAS=DIODE_HV=NWELL_RING=LOGIC_DNWELL=floating, VDD=%.1fV)'%(chip_version, VDD), xlabel='measurements', ylabel='current I / $\\mu$A')
        plt.plot(VDD_current, label='VDD', marker='x')
        plt.plot(GND_current, label='GND', marker='x')
        plt.plot(np.array(GND_current)+np.array(VDD_current), label='Sum', color='black', marker='x')
        plt.legend()
        plt.savefig('./output/miscellaneous/VDD_%.1f_current_over_time_%s.pdf'%(VDD, chip_version), bbox_inches='tight')
        plt.show()
    return VDD_current, GND_current

def VDD_current_over_time_scan(VDD_SEL=[]):
    fig, ax = plt.subplots(int(len(VDD_SEL)/2+1), 2, squeeze=True)
    fig.suptitle('%s chip (PW_BIAS=BACK_BIAS=DIODE_HV=NWELL_RING=LOGIC_DNWELL=floating)'%(chip_version))
    fig.set_figheight(30)
    fig.set_figwidth(30)
    ax = ax.ravel()
    
    for VDD in VDD_SEL:
        i = np.where(np.array(VDD_SEL)==VDD)[0][0]

        if not load_data:
            sm_VDD['sourcemeter'].set_voltage(0)
            time.sleep(1)
            VDD_current, GND_current = VDD_current_over_time(VDD=VDD, control_pics=False)
        else:
            for VDD in VDD_SEL:
                data = np.genfromtxt('./output/miscellaneous/data/VDD_SEL_%.1f.csv'%(VDD), delimiter=',')
                VDD_current = data[1:,0]
                GND_current = data[1:,1]
        ax[i].plot(VDD_current, label='VDD', marker='x')
        ax[i].plot(GND_current, label='GND', marker='x')
        ax[i].plot(np.array(GND_current)+np.array(VDD_current), label='Sum', color='black', marker='x')
        ax[i].set_title('VDD=%.1fV'%(VDD))
        ax[i].grid()
        ax[i].set_xlabel('measurement point')
        ax[i].set_ylabel('current I / $\\mu$A')
        ax[i].legend()
        plt.gca().set_prop_cycle(None)
        if not load_data: dh.save_data(data=[VDD_current, GND_current], header='VDD_current, GND_current', output_path='./output/miscellaneous/data/VDD_SEL_%.1f.csv'%(VDD))

    for i in range(len(ax)-len(VDD_SEL)):
        fig.delaxes(ax[-1-i])
    plt.savefig('./output/miscellaneous/VDD_SEL_current_over_time_%s.pdf'%(chip_version), bbox_inches='tight')

    plt.show()

#VDD_scan()
#VDD_current_over_time()
VDD_current_over_time_scan(VDD_SEL=[1.8, 2.5, 3, 3.2, 3.5, 3.7])

