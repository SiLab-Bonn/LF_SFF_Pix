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


sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
sm.init()
sm.settings(voltage=0, current_limit=400*1e-6)


def scan_ESD_Diode(V_SEL=[]):
    current = []
    if not load_data:
        for V in V_SEL:
            print(V)
            sm['sourcemeter'].set_voltage(V)
            time.sleep(0.5)
            current.append(float(sm['sourcemeter'].get_current())*1e6)
        dh.save_data(data=[V_SEL, current], header='V, I', output_path='./output/miscellaneous/data/DIODE_HV_PIX_IN_scan_%s.csv'%(chip_version))
    else:
        data = np.genfromtxt('./output/miscellaneous/data/DIODE_HV_PIX_IN_scan_%s.csv'%(chip_version), delimiter=',')
        V_SEL = data[1:,0]
        current = data[1:,1]
    sm['sourcemeter'].off()

    fig, ax = plt.subplots(1, 2, squeeze=True)
    fig.suptitle('%s chip (LOGIC_DNWELL=NWELL_RING=PWELL=BACK_BIAS=VDD=floating'%(chip_version))
    fig.set_figheight(9)
    fig.set_figwidth(16)
    ax = ax.ravel()
    ax[0].plot(V_SEL, current, marker='x')
    ax[0].grid()
    ax[0].set_xlabel('voltage $V_\mathrm{DIODE\_HV-PIX\_IN}$ / V')
    ax[0].set_ylabel('current I / $\\mu$A')
    ax[1].set_yscale('log')
    ax[1].plot(V_SEL, current, marker='x')
    ax[1].grid()
    ax[1].set_xlabel('voltage $V_\mathrm{DIODE\_HV-PIX\_IN}$ / V')
    ax[1].set_ylabel('current I / $\\mu$A')
    #plt.gca().set_prop_cycle(None)
    plt.savefig('./output/miscellaneous/DIODE_HV_PIX_IN_scan_%s.pdf'%(chip_version), bbox_inches='tight')
    plt.show()
    

scan_ESD_Diode(V_SEL=np.arange(0, 2.05, 0.05))