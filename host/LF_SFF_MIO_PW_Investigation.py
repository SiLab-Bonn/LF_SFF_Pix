
import time
import numpy as np

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
import utils.plot_fit as pltfit
from host.bode_plot_analyzer import analyse_bode_plot
import utils.data_handler as data_handler

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import yaml
import sys

try:
    dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
    dut.init()
    dut.boot_seq()
    dut.load_defaults(VRESET = 0)
except:
    print('Firmware not flashed. This can be because a firmware was already flashed or your setup is broken')


image_format = '.pdf'

def AC_sweep(DC_off,load_data=False,DC=False):
    IBN = [100]
    IBP = [-10]
    #IBN = [80,82,85,87,90,92,95,97,100]
    #IBP = [-5,-6,-7,-8,-9,-10]
    I_unit = 'uA'

    frequency_oszi = [1e0, 1e1,1e2,1e3,1e4,1e5,1e6]
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
    
    if 'DC' in sys.argv[1:] or DC==True:
        print('WARNING: This test shall only be used for the AC chip version!!!')
        time.sleep(10)
        chip_version='DC'
        image_path = './output/AC_sweeps/PW_investigation/'
        data_path = image_path+'data/'

    else:
        chip_version = 'AC'
        image_path = './output/AC_sweeps/PW_investigation/'
        data_path = image_path+'data/'
   
    if 'load_data' in sys.argv[1:]:
        load_data = True  
    try:
        IBP_end_of_dynamic_area = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBP_end_of_dynamic_area.csv', delimiter=',')
        end_of_dynamic_area = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBN_end_of_dynamic_area.csv', delimiter=',')
        DC_offset = np.average([IBP_end_of_dynamic_area[1][1],end_of_dynamic_area[1][1]])
        print('\nSuccessfully loaded DC sweep results\n')

        if DC_offset <= 0.05:
            DC_offset = 0.05
            print('But it was smaller than 50mV. Therefore the DC offset was set to 50mV')
    except:
        DC_offset = 0.3
        print('\nSet DC_offset to fallback, because DC sweep results could not be loaded\n')
            

    DC_offset = DC_off
    dut.load_defaults(VRESET = DC_offset)
    if not load_data:


        dut['CONTROL']['RESET'] = 0x0
        dut['CONTROL'].write()
        
        oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_tds_3034b.yaml", 'r'), Loader=yaml.Loader))
        oszi.init()

        func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
        func_gen.init()
        if chip_version == 'DC':
            func_gen.load_ac_sweep_config(offset=DC_offset, amplitude=0.1, frequency=100)
        else:
            func_gen.load_ac_sweep_config(offset=0, amplitude=0.1, frequency=100)

        oszi.load_ac_sweep_config()

        VIN = []
        VIN_err = []
        meas = []
        VOUT = []
        VOUT_err = []
        for f in frequencies:
            if f in frequency_oszi:
                set_oszi_freq = f
            else:
                for i in range(1,6):
                    if (f-i*len(str(f)[1:]) in frequency_oszi):
                        set_oszi_freq = i*len(str(f)[1:])
                        break
            print('-----------------\n',f,' Hz')
            func_gen['Pulser'].set_pulse_period(1/f)
            oszi['Oscilloscope'].set_horizontal_scale(1/set_oszi_freq)


            if f <=10:
                time.sleep(10)
            if f <= 100:
                time.sleep(1)
            else:
                time.sleep(0.5)
            meas.append(dut['IBN'].get_current(unit=I_unit))
            waveform_in = oszi['Oscilloscope'].get_waveform(channel=1, continue_meas=False)
            waveform_in_x = oszi.gen_waveform_x(waveform_in)
            p_in_guess = pltfit.guess_cos_params(f=f,y=waveform_in[1])
            popt_in, perr_in = pltfit.fit_no_err(pltfit.func_cos, waveform_in_x, waveform_in[1],p_in_guess)        
            waveform_out = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
            waveform_out_x = oszi.gen_waveform_x(waveform_out)
            p_out_guess = pltfit.guess_cos_params(f=f,y=waveform_out[1])
            popt_out, perr_out = pltfit.fit_no_err(pltfit.func_cos, waveform_out_x, waveform_out[1],p_out_guess)
            pltfit.beauty_plot(xlabel='time t / s',ylabel='Voltage / V',ylim=[-4*waveform_in[3][0], 4*waveform_in[3][0]])
            plt.scatter(waveform_in_x, waveform_in[1], label='Input')
            plt.scatter(waveform_out_x, waveform_out[1], label='Output')
            plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_in[0], popt_in[1], popt_in[2], popt_in[3]), color='black')
            plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_out[0], popt_out[1], popt_out[2], popt_out[3]), color='black')
            plt.legend()
            plt.savefig(image_path+'DC_'+str(DC_offset)+'.png')
            plt.close()
            print('IN: ', np.abs(popt_in[0])*2,'| OUT: ', np.abs(popt_out[0])*2, ' | Ratio: ', np.abs(popt_out[0])/np.abs(popt_in[0]))
            VOUT.append(popt_out[0])
            VOUT_err.append(perr_out[0])
            VIN.append(popt_in[0])
            VIN_err.append(perr_in[0])

        # Save data
        file_name = 'DC_'+str(DC_offset)+'.csv'
        with open(data_path+file_name, 'w') as f:
                f.write('frequency, frequency_error, VIN, VIN_err, VOUT, VOUT_err\n')
                for i in range(0, len(frequencies)):
                    f.write(str(frequencies[i])+', '+str(frequencies[i]*0.05)+', '+str(np.abs(VIN[i]))+', '+str(np.abs(VIN_err[i]))+', '+str(np.abs(VOUT[i]))+', '+str(np.abs(VOUT_err[i])))
                    f.write('\n')

    else: # load data
  
 
        data = np.genfromtxt(data_path+'DC_'+str(DC_offset)+'.csv', delimiter=',')
        VIN = data[1:,2]
        VIN_err = data[1:,3]
        VOUT = data[1:,4]
        VOUT_err = data[1:,5]


    y = np.abs(VOUT)/np.abs(VIN)
    yerr = np.sqrt((1/np.abs(VIN)*VOUT_err)**2+(np.abs(VOUT)/np.abs(VIN)**2*VIN_err)**2)
    yerr = (np.abs(10/(y*np.log10(10)))*yerr)

    '''pltfit.beauty_plot(xlabel='f / Hz', ylabel='V_IN', log_x=True)
    for I in range(0,len(IBN)):
        plt.scatter(frequencies,np.abs(VIN[I]), linestyle="None", label="V_IN")
        plt.scatter(frequencies,np.abs(VOUT[I]), linestyle="None", label="V_OUT")
        plt.savefig(image_path+"00_VIN_VOUT_RAW.png")

    plt.legend()
    plt.show()

    pltfit.beauty_plot(xlabel='f / Hz', ylabel='V_IN/V_OUT', log_x=True)
    for I in range(0,len(IBN)):
        dc_gain = 0.8
        dc_gain_err = 0.01
        plt.scatter(frequencies, y, linestyle="None")
        plt.savefig(image_path+"00_not_db.png")

    plt.show()


    pltfit.beauty_plot(xlabel='f / Hz', ylabel='V_IN/V_OUT in dB', log_x=True)
    for I in range(0,len(IBN)):
        y = np.abs(VOUT[I]/VIN[I])
        yerr = y*0.05
        dc_gain = 0.8
        dc_gain_err = 0.01
        plt.errorbar(x=frequencies,y=10*np.log10(np.abs(VOUT[I]/VIN[I])),yerr=np.sqrt((np.abs(10/(y*np.log10(10)))*yerr)**2+(10/(dc_gain*np.log(10))*dc_gain_err)**2), marker='.' , linestyle="None")
        plt.savefig(image_path+"00_Bode.png")
    plt.show()
    '''
    return [frequencies,np.array(frequencies)*0.05, y,yerr]
results = []
counter= 0
pltfit.beauty_plot(log_x=True, xlabel='f / Hz', ylabel='$V_{out}$ / $V_{in}$ / dB')
for DC_offset in [0,0.1,0.2,0.5,0.8,1.2]:
    results.append(AC_sweep(DC_offset))
    plt.errorbar(x=results[counter][0],xerr=results[counter][1],y=10*np.log10(results[counter][2]),yerr=results[counter][3], label = 'VRESET = '+str(DC_offset)+'V', linestyle='None')
    counter +=1
plt.legend()
plt.savefig('./output/AC_sweeps/PW_investigation//00_DC_OFFSET_COMPARISON'+image_format)
plt.show()