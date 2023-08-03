# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup:
#                   _____________ Function Generator________
#                  |                        |               |
#                  | PIX_INPUT              | RS232         |
# -----------------------                   |               |
# | MIO | GPIO | LF_SFF |       MIO------Computer           |
# -----------------------            USB    |               |
#        Pixel 10  |                        | RJ45          |
#        Matrix 1  |                        |               |
#                  |______________________Oszi______________|
#                            CH2                   CH1
#
# You don"t have to adjust the trigger/Channel levels/offsets. Everything is handled automatically.
# If you can't see a trigger at 100Hz like in the picture below, restart the script, until it triggers correctly
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
# The function generator is also completely controlled by this script except the function form. Set it to SINE. 
# Please verify BEFORE plugging it into the PIX_INPUT of the LFSFF Board that the Ampl and Offset are not larger 
# than Vpp=100mV and Voff=650mV.
#

####
# Measure IBN/IBP and frequency
####

import time
import numpy as np

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
from lab_devices.conifg.config_handler import update_config
from lab_devices.sourcemeter import sourcemeter

import utils.plot_fit as pltfit
from host.bode_plot_analyzer import analyse_bode_plot
import utils.data_handler as data_handler
import matplotlib.pyplot as plt
import yaml
import sys
from utils.initialize_measurement import initialize_measurement as init_meas

image_format = '.pdf'

load_data, chip_version, image_path, data_path = init_meas('AC_sweeps')

def AC_sweep(load_data=False, DC=False, PWELL_BIAS_SELECTION = [0], IBN = [100], IBP = []):
    dut_config = update_config('./lab_devices/conifg/LF_SFF_AC_Sweep.csv')
    #IBN = [80,82,85,87,90,92,95,97,100]
    #IBP = [-5,-6,-7,-8,-9,-10]
    
    I_unit = 'uA'

    frequency_oszi = [1e0,1e1, 1e2, 1e3,1e4,1e5,1e6] #[1e0,1e1,1e2,1e3,1e4,1e5,1e6] we can skip f<1e3 since noise is dominating
    #frequency_oszi = [1e3,1e4,1e5,1e6] #[1e0,1e1,1e2,1e3,1e4,1e5,1e6] we can skip f<1e3 since noise is dominating
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
    
    # Determins if user has applied an external resistor in VRESET
    R_ext = False
    R_ext_err = False

    if 'DC' in sys.argv[1:] or DC==True:
        chip_version='DC'
        image_path = './output/AC_sweeps/DC/'
        data_path = image_path+'data/'

    else:
        chip_version = 'AC'
        image_path = './output/AC_sweeps/AC/'
        data_path = image_path+'data/'
   
    if 'R_ext' in sys.argv[1:]:
        chip_version = 'AC'
        image_path = './output/AC_sweeps/AC_R_ext/'
        data_path = image_path+'data/'
        R_ext = 1e6
        R_ext_err = R_ext*0.02
   
    if 'load_data' in sys.argv[1:]:
        load_data = True  

    if '--name' in sys.argv[1:]:
        image_path = './output/AC_sweeps/'+sys.argv[sys.argv[1:].index('--name')+2]+'/'
        data_path = image_path+'data/'
        print('Custom path: ', image_path)
    DIODE_HV = 0
    

    if load_data: 
        DC_offset = np.genfromtxt(data_path+'DC_offset.txt')
        print(DC_offset)

        IBN_VIN = [[] for i in range(0, len(IBN))]
        IBN_VIN_err = [[] for i in range(0, len(IBN))]
        IBN_meas = [[] for i in range(0, len(IBN))]
        IBN_VOUT = [[] for i in range(0, len(IBN))]
        IBN_VOUT_err = [[] for i in range(0, len(IBN))]
    
        IBP_VIN = [[] for i in range(0, len(IBN))]
        IBP_VIN_err = [[] for i in range(0, len(IBN))]
        IBP_meas = [[] for i in range(0, len(IBP))]
        IBP_VOUT = [[] for i in range(0, len(IBP))]
        IBP_VOUT_err = [[] for i in range(0, len(IBP))]

        for i in range(0, len(IBN)):
            data = np.genfromtxt(data_path+'IBN_'+str(IBN[i])+'_'+str(PWELL_BIAS)+'.csv', delimiter=',')
            IBN_VIN[i] = data[1:,2]
            IBN_VIN_err [i] = data[1:,3]
            IBN_VOUT[i] = data[1:,4]
            IBN_VOUT_err[i] = data[1:,5]
        for i in range(0, len(IBP)):
            data = np.genfromtxt(data_path+'IBP_'+str(IBP[i])+'_'+str(PWELL_BIAS)+'.csv', delimiter=',')
            IBP_VIN[i] = data[1:,2]
            IBP_VIN_err [i] = data[1:,3]
            IBP_VOUT[i] = data[1:,4]
            IBP_VOUT_err[i] = data[1:,5]
    else:
        try:
            dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
            dut.init()
            dut.boot_seq()
            DC_offset = dut.get_DC_offset(chip_version=chip_version)    
            #DC_offset = 0.1 
            dut.load_defaults(VRESET = DC_offset, DIODE_HV=DIODE_HV)
            print('DIODE_HV set to: ', dut['DIODE_HV'].get_voltage())
            data_handler.save_data([DC_offset], data_path+'DC_offset.txt')
        except:
            print('Firmware not flashed. This can be because a firmware was already flashed or your setup is broken')
        print('Resetting')
        dut.reset(sleep=1)
        time.sleep(3)
        if not R_ext:
            dut['CONTROL']['RESET'] = 0x0
            dut['CONTROL'].write()
        else:
            dut['CONTROL']['RESET'] = 0x1
            dut['CONTROL'].write()
            
        oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_tds_3034b.yaml", 'r'), Loader=yaml.Loader))
        oszi.init()

        sm = sourcemeter(yaml.load(open("./lab_devices/keithley_2410.yaml", 'r'), Loader=yaml.Loader))
        sm.init()

        func_gen = function_generator(yaml.load(open("./lab_devices/agilent33250a_pyserial.yaml", 'r'), Loader=yaml.Loader))
        func_gen.init()
        if chip_version == 'DC':
            func_gen.load_ac_sweep_config(offset=DC_offset, amplitude=0.1, frequency=100)
        else:
            func_gen.load_ac_sweep_config(offset=DIODE_HV, amplitude=0.1, frequency=100)

        oszi.load_ac_sweep_config()
        IBN_Gain_meas, IBN_Gain_err_meas, IBN_f_hp_meas, IBN_f_hp_err_meas, IBN_R_off_meas, IBN_R_off_err_meas, IBN_C_in_meas, IBN_C_in_err_meas = [],[],[],[],[],[],[],[]

        for PWELL_BIAS in PWELL_BIAS_SELECTION:
            IBN_VIN = [[] for i in range(0, len(IBN))]
            IBN_VIN_err = [[] for i in range(0, len(IBN))]
            IBN_meas = [[] for i in range(0, len(IBN))]
            IBN_VOUT = [[] for i in range(0, len(IBN))]
            IBN_VOUT_err = [[] for i in range(0, len(IBN))]
        
            IBP_VIN = [[] for i in range(0, len(IBN))]
            IBP_VIN_err = [[] for i in range(0, len(IBN))]
            IBP_meas = [[] for i in range(0, len(IBP))]
            IBP_VOUT = [[] for i in range(0, len(IBP))]
            IBP_VOUT_err = [[] for i in range(0, len(IBP))]
        
            sm.pixel_depletion(PW_BIAS=PWELL_BIAS)
            for f in frequencies:
                dut_config.check_config(dut)
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
                #dut.reset(sleep=1)
                #time.sleep(3)

                for I in IBN:
                    while True:
                        print('IBN =', I,'uA', '(DC_offset=%.2fV, PW_BIAS=%.2fV)'%(DC_offset, PWELL_BIAS))
                        pos = IBN.index(I)
                        dut['IBN'].set_current(I,unit=I_unit)

                        if f<=3:
                            time.sleep(10.1)
                        if f <=10:
                            time.sleep(5)
                        elif f <= 100:
                            time.sleep(3)
                        else:
                            time.sleep(0.5)
                        IBN_meas[pos].append(dut['IBN'].get_current(unit=I_unit))
                        waveform_in = oszi['Oscilloscope'].get_waveform(channel=1, continue_meas=False)
                        waveform_in_x = oszi.gen_waveform_x(waveform_in)
                        p_in_guess = pltfit.guess_cos_params(f=f,y=waveform_in[1])
                        popt_in, perr_in = pltfit.fit_no_err(pltfit.func_cos, waveform_in_x, waveform_in[1],p_in_guess)        
                        waveform_out = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
                        waveform_out_x = oszi.gen_waveform_x(waveform_out)
                        p_out_guess = pltfit.guess_cos_params(f=f,y=waveform_out[1])
                        popt_out, perr_out = pltfit.fit_no_err(pltfit.func_cos, waveform_out_x, waveform_out[1],p_out_guess)
                        pltfit.beauty_plot(xlabel='time t / s',ylabel='Voltage / V',ylim=[-4*waveform_in[3][0], 4*waveform_in[3][0]])
                        plt.scatter(waveform_in_x, waveform_in[1], label='Input: %f *f + %f'%(popt_in[0], popt_in[1]))
                        plt.scatter(waveform_out_x, waveform_out[1], label='Output %f *f + %f'%(popt_out[0], popt_out[1]))
                        plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_in[0], popt_in[1], popt_in[2], popt_in[3]), color='black')
                        plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_out[0], popt_out[1], popt_out[2], popt_out[3]), color='black')
                        plt.legend()
                        plt.savefig(image_path+'fits/'+'IBN_'+str(f)+'_'+str(I)+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
                        plt.close()
                        IBN_VOUT[pos].append(popt_out[0])
                        IBN_VOUT_err[pos].append(perr_out[0])
                        IBN_VIN[pos].append(popt_in[0])
                        IBN_VIN_err[pos].append(perr_in[0])
                        print(popt_in[0],popt_out[0])
                        if popt_out[0] != 0 and popt_in[0]!=0:
                            break

                dut['IBN'].set_current(IBN[-1],unit=I_unit)
                for I in IBP:
                    while True:
                        print('IBP =', I,'uA', '(DC_offset=%.2fV, PW_BIAS=%.2fV)'%(DC_offset, PWELL_BIAS))
                        pos = IBP.index(I)
                        dut['IBP'].set_current(I,unit=I_unit)
                        if f<=5:
                            time.sleep(10.1)
                        if f <=10:
                            time.sleep(5)
                        elif f <= 100:
                            time.sleep(3)
                        else:
                            time.sleep(0.5)
                        IBP_meas[pos].append(dut['IBP'].get_current(unit=I_unit))
                        waveform_in = oszi['Oscilloscope'].get_waveform(channel=1, continue_meas=False)
                        waveform_in_x = oszi.gen_waveform_x(waveform_in)
                        p_in_guess = pltfit.guess_cos_params(f=f,y=waveform_in[1])
                        popt_in, perr_in = pltfit.fit_no_err(pltfit.func_cos, waveform_in_x, waveform_in[1],p_in_guess)        
                        waveform_out = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)
                        waveform_out_x = oszi.gen_waveform_x(waveform_out)
                        p_out_guess = pltfit.guess_cos_params(f=f,y=waveform_out[1])
                        popt_out, perr_out = pltfit.fit_no_err(pltfit.func_cos, waveform_out_x, waveform_out[1],p_out_guess)
                        pltfit.beauty_plot(xlabel='time t / s',ylabel='Voltage / V',ylim=[-4*waveform_in[3][0], 4*waveform_in[3][0]])
                        plt.scatter(waveform_in_x, waveform_in[1], label='Input: %f *f + %f'%(popt_in[0], popt_in[1]))
                        plt.scatter(waveform_out_x, waveform_out[1], label='Output %f *f + %f'%(popt_out[0], popt_out[1]))
                        plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_in[0], popt_in[1], popt_in[2], popt_in[3]), color='black')
                        plt.plot(waveform_in_x, pltfit.func_cos(waveform_in_x, popt_out[0], popt_out[1], popt_out[2], popt_out[3]), color='black')
                        plt.legend()
                        plt.savefig(image_path+'fits/'+'IBP_'+str(f)+'_'+str(I)+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
                        plt.close()
                        IBP_VOUT[pos].append(popt_out[0])
                        IBP_VOUT_err[pos].append(perr_out[0])
                        IBP_VIN[pos].append(popt_in[0])
                        IBP_VIN_err[pos].append(perr_in[0])
                        print(popt_in[0],popt_out[0])
                        if popt_out[0] != 0 and popt_in[0]!=0:
                            break


            # Save data
            for j in range(0, len(IBN)):
                file_name = 'IBN_'+str(IBN[j])+'_'+str(PWELL_BIAS)+'.csv'
                with open(data_path+file_name, 'w') as f:
                        f.write('frequency, frequency_error, IBN_VIN, IBN_VIN_err, IBN_VOUT, IBN_VOUT_err\n')
                        for i in range(0, len(frequencies)):
                            f.write(str(frequencies[i])+', '+str(frequencies[i]*0.05)+', '+str(np.abs(IBN_VIN[j][i]))+', '+str(np.abs(IBN_VIN_err[j][i]))+', '+str(np.abs(IBN_VOUT[j][i]))+', '+str(np.abs(IBN_VOUT_err[j][i])))
                            f.write('\n')
            for j in range(0, len(IBP)):
                file_name = 'IBP_'+str(IBP[j])+'_'+str(PWELL_BIAS)+'.csv'
                with open(data_path+file_name, 'w') as f:
                        f.write('frequency, frequency_error, IBP_VIN, IBP_VIN_err, IBP_VOUT, IBP_VOUT_err\n')
                        for i in range(0, len(frequencies)):
                            f.write(str(frequencies[i])+', '+str(frequencies[i]*0.05)+', '+str(np.abs(IBP_VIN[j][i]))+', '+str(np.abs(IBP_VIN_err[j][i]))+', '+str(np.abs(IBP_VOUT[j][i]))+', '+str(np.abs(IBP_VOUT_err[j][i])))
                            f.write('\n')
            data_handler.success_message_data_taking()
        

            #################################
            # Plot the results
            #
            # I. IBN Results
            #################################      

            #################################
            # Create IBN Bode Plots
            #################################   
            IBN_Gain, IBN_Gain_err, IBN_f_tp, IBN_f_tp_err, IBN_f_hp, IBN_f_hp_err, IBN_C_in, IBN_C_in_err, IBN_R_off, IBN_R_off_err = [[0 for i in range(0, len(IBN))] for j in range(0,10)]
            for i in range(0, len(IBN)):
                print(IBN[i])

                x = np.array(frequencies)
                xerr = np.array(frequencies)*0.05
                y = np.abs(IBN_VOUT[i])/np.abs(IBN_VIN[i])
                yerr = np.sqrt((1/np.abs(IBN_VIN[i])*IBN_VOUT_err[i])**2+(np.abs(IBN_VOUT[i])/np.abs(IBN_VIN[i])**2*IBN_VIN_err[i])**2)
                IBN_Gain[i], IBN_Gain_err[i], IBN_f_tp[i], IBN_f_tp_err[i], IBN_f_hp[i], IBN_f_hp_err[i],IBN_C_in[i], IBN_C_in_err[i], IBN_R_off[i], IBN_R_off_err[i]= analyse_bode_plot(x=x, y=y, xerr=xerr, yerr=yerr, chip_version=chip_version, DC_offset=DC_offset, output_path=image_path+'IBN_'+str(IBN[i])+'_'+str(PWELL_BIAS)+'_bode'+image_format, title=chip_version+' coupled chip\nBodeplot: $I_{BN}=$%.2f$\\mu$A, $I_{BP}=$%.2f$\\mu$A, DIODE_HV=%.2fV, PWELL_BIAS=%.2fV, DC_offset=%.2fV'%(IBN[i], -10, DIODE_HV, PWELL_BIAS, DC_offset), show_plot = False, IBN=IBN[i], R_ext=R_ext, R_ext_err=R_ext_err)

            
            pltfit.beauty_plot(log_x=True, xlabel='Frequency $f$ / Hz', ylabel='$V_{pp}(LF SFF)/V_{pp}(IN)$ in dB')
            for i in range(0, len(IBN)):
                try:
                    plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBN_VOUT[i])/np.abs(IBN_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBN=%.1fuA, $f_{tp}=(%.3f\\pm  %.3f)MHz$, $f_{hp} =(%.3f\\pm %.3f)$'%(IBN[i], IBN_f_tp[i]*1e-6, IBN_f_tp_err[i]*1e-6,IBN_f_hp[i], IBN_f_hp_err[i]))
                except:
                    try:
                        plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBN_VOUT[i])/np.abs(IBN_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBN=%.1fuA, $f_{tp}=(%.3f\\pm  %.3f)MHz$, $f_{hp}=$Not found'%(IBN[i],IBN_f_tp[i]*1e-6, IBN_f_tp_err[i]*1e-6))
                    except:
                        plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBN_VOUT[i])/np.abs(IBN_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBN=%.1fuA, $f_{tp}=$Not found, $f_{hp}=$Not found'%(IBN[i]))

            plt.legend()
            #plt.savefig(image_path+'IBN_data'+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
            plt.close()

                        
            #################################
            # Plot the results
            #
            # II. IBP Results
            #################################      
            #################################
            # Create IBP Bode Plots
            #################################   
            IBP_Gain, IBP_Gain_err, IBP_f_tp, IBP_f_tp_err, IBP_f_hp, IBP_f_hp_err, IBP_C_in, IBP_C_in_err, IBP_R_off, IBP_R_off_err = [[0 for i in range(0, len(IBP))] for j in range(0,10)]
            for i in range(0, len(IBP)):
                print(IBP[i])
                x = np.array(frequencies)
                xerr = np.array(frequencies)*0.05
                y = np.abs(IBP_VOUT[i])/np.abs(IBP_VIN[i])
                yerr = np.sqrt((1/np.abs(IBP_VIN[i])*IBP_VOUT_err[i])**2+(np.abs(IBP_VOUT[i])/np.abs(IBP_VIN[i])**2*IBP_VIN_err[i])**2)
                IBP_Gain[i], IBP_Gain_err[i], IBP_f_tp[i], IBP_f_tp_err[i], IBP_f_hp[i], IBP_f_hp_err[i],IBP_C_in[i], IBP_C_in_err[i], IBP_R_off[i], IBP_R_off_err[i]= analyse_bode_plot(x=x, y=y, xerr=xerr, yerr=yerr, chip_version=chip_version, DC_offset=DC_offset, output_path=image_path+'IBP_'+str(IBP[i])+'_bode'+image_format, title='Bodeplot at IBP:'+str(IBP[i])+'uA', show_plot = False, IBP=IBP[i], R_ext=R_ext, R_ext_err=R_ext_err)
            
            pltfit.beauty_plot(log_x=True, xlabel='Frequency $f$ / Hz', ylabel='$V_{pp}(LF SFF)/V_{pp}(IN)$ in dB')
            for i in range(0, len(IBP)):
                try:
                    plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBP_VOUT[i])/np.abs(IBP_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBP=%.1fuA, $f_{tp}=(%.3f\\pm %.3f)$, $f_{hp} =(%.3f\\pm %.3f)$'%(IBP[i], IBP_f_tp[i], IBP_f_tp_err[i],IBP_f_hp[i], IBP_f_hp_err[i]))
                except:
                    try:
                        plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBP_VOUT[i])/np.abs(IBP_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBP=%.1fuA, $f_{tp}=(%.3f\\pm %.3f)$MHz, $f_{hp}=$Not found'%(IBP[i],IBP_f_tp[i]*1e-6, IBP_f_tp_err[i]*1e-6))
                    except:
                        plt.errorbar(x=frequencies, y=10*np.log10(np.abs(IBP_VOUT[i])/np.abs(IBP_VIN[i])), xerr=np.array(frequencies)*0.05, linestyle='None', marker='.', label='IBP=%.1fuA, $f_{tp}=$Not found, $f_{hp}=$Not found'%(IBP[i]))

            plt.legend()
            #plt.savefig(image_path+'IBP_data'+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
            plt.close()


            #################################
            # Plot C_in and R_off results
            #################################   
            if chip_version != 'DC':
                pltfit.beauty_plot(tight=False, title='$C_{in}$ of '+chip_version+' chip') 
                plt.subplot(2,1,1)
                plt.errorbar(x=IBN, y=IBN_C_in, yerr=IBN_C_in_err, linestyle='None', marker='.', label='$\\langle C_{in}\\rangle =(%.1f\\pm %.1f)$fF'%(np.mean(IBN_C_in), 1/len(IBN_C_in)*np.sqrt(np.sum([np.array(IBN_C_in_err)**2]))))
                plt.legend()
                plt.xlabel('IBN / uA')
                plt.ylabel('$C_{in}$ / fF')
                plt.grid()
                plt.subplot(2,1,2)
                if IBP:
                    plt.errorbar(x=IBP, y=IBP_C_in, yerr=IBP_C_in_err, linestyle='None', marker='.', label='$\\langle C_{in}\\rangle =(%.1f\\pm %.1f)$fF'%(np.mean(IBP_C_in), 1/len(IBP_C_in)*np.sqrt(np.sum([np.array(IBP_C_in_err)**2]))))
                    plt.legend()
                    plt.xlabel('IBP / uA')
                    plt.ylabel('$C_{in}$ / fF')
                    plt.grid()
                    plt.savefig(image_path+chip_version+'_C_in'+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
                    plt.close()

                pltfit.beauty_plot(tight=False, title='$R_{off}$ of '+chip_version+' chip') 
                plt.subplot(2,1,1)
                plt.errorbar(x=IBN, y=np.array(IBN_R_off).flatten()*1e-6, yerr=np.array(IBN_R_off_err).flatten()*1e-6, linestyle='None', marker='.', label='$\\langle R_{off}\\rangle =(%.1f\\pm %.1f)$M$\Omega$'%(np.mean(IBN_R_off)*1e-6, 1/len(IBN_R_off)*np.sqrt(np.sum([np.array(IBN_R_off_err)**2])*1e-6)))
                plt.legend()
                plt.xlabel('IBN / uA')
                plt.ylabel('$R_{off} / M\Omega$')
                plt.grid()
                plt.subplot(2,1,2)
                if IBP:
                    plt.errorbar(x=IBP, y=np.array(IBP_R_off).flatten()*1e-6, yerr=np.array(IBP_R_off_err).flatten()*1e-6, linestyle='None', marker='.', label='$\\langle C_{in}\\rangle =(%.1f\\pm %.1f)$M$\Omega$'%(np.mean(IBP_R_off), 1/len(IBP_R_off)*np.sqrt(np.sum([np.array(IBP_R_off_err)**2]))))
                    plt.legend()
                    plt.xlabel('IBP / uA')
                    plt.ylabel('$R_{off} / M\Omega$')
                    plt.grid()
                    plt.savefig(image_path+chip_version+'_R_off'+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
                    plt.close()

            #################################
            # Plot AC sweep Gain results
            #################################   
            pltfit.beauty_plot(tight=False) 

            IBP_DC_Gain = []
            IBP_DC_Gain_err = []
            IBN_DC_Gain = []
            IBN_DC_Gain_err = []

            plt.subplot(2,1,1)
            plt.errorbar(x=IBN, y=IBN_Gain, yerr=IBN_Gain_err, linestyle='None', marker='.', label='AC Sweep: $\\langle G\\rangle =(%.3f\\pm %.3f)$'%(np.mean(IBN_Gain), 1/len(IBN_Gain)*np.sqrt(np.sum([np.array(IBN_Gain_err)**2]))))
            try:
                for i in range(0, len(IBN)):
                    IBN_DC_sweep_data = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBN_'+str(IBN[i])+'_'+str(PWELL_BIAS)+'_Gain.csv', delimiter=',')[1:,]
                    IBN_DC_Gain.append(IBN_DC_sweep_data[np.argmin(np.abs(IBN_DC_sweep_data[:,0] - DC_offset))][2])
                    IBN_DC_Gain_err.append(IBN_DC_sweep_data[np.argmin(np.abs(IBN_DC_sweep_data[:,0] - DC_offset))][3])
                plt.errorbar(x=IBN, y=IBN_DC_Gain, yerr=IBN_DC_Gain_err, linestyle='None', marker='.',alpha=0.5, label='DC Sweep: $\\langle G\\rangle =(%.3f\\pm %.3f)$'%(np.mean(IBN_DC_Gain), 1/len(IBN_DC_Gain)*np.sqrt(np.sum([np.array(IBN_DC_Gain_err)**2]))))
            except: pass
            plt.legend()
            plt.xlabel('IBN / uA')
            plt.ylabel('Gain $G$')
            plt.grid()
            if IBP:
                plt.subplot(2,1,2)
                plt.errorbar(x=IBP, y=IBP_Gain, yerr=IBP_Gain_err, linestyle='None', marker='.', label='AC Sweep: $\\langle G\\rangle =(%.3f\\pm %.3f)$'%(np.mean(IBP_Gain), 1/len(IBP_Gain)*np.sqrt(np.sum([np.array(IBP_Gain_err)**2]))))
            try:
                for i in range(0, len(IBP)):
                    IBP_DC_sweep_data = np.genfromtxt('./output/DC_sweeps/'+chip_version+'/data/IBP_'+str(IBP[i])+'_'+str(PWELL_BIAS)+'_Gain.csv', delimiter=',')[1:,]
                    IBP_DC_Gain.append(IBP_DC_sweep_data[np.argmin(np.abs(IBP_DC_sweep_data[:,0] - DC_offset))][2])
                    IBP_DC_Gain_err.append(IBP_DC_sweep_data[np.argmin(np.abs(IBN_DC_sweep_data[:,0] - DC_offset))][3])
                plt.errorbar(x=IBP, y=IBP_DC_Gain, yerr=IBP_DC_Gain_err, linestyle='None', marker='.',alpha=0.5, label='DC Sweep: $\\langle G\\rangle =(%.3f\\pm %.3f)$'%(np.mean(IBP_DC_Gain), 1/len(IBP_DC_Gain)*np.sqrt(np.sum([np.array(IBP_DC_Gain_err)**2]))))
            except: pass
            plt.legend()
            plt.xlabel('IBP / uA')
            plt.ylabel('Gain $G$')
            plt.grid()
            plt.savefig(image_path+chip_version+'_AC_Gain'+'_'+str(PWELL_BIAS)+image_format,bbox_inches='tight')
            plt.close()

            

            #####
            # Exit message
            #####
            data_handler.success_message(data_path, image_path)
            IBN_Gain_meas.append(IBN_Gain[0]) 
            IBN_Gain_err_meas.append(IBN_Gain_err[0]) 
            if IBN_f_hp[0]:
                IBN_f_hp_meas.append(IBN_f_hp[0])
                IBN_f_hp_err_meas.append(IBN_f_hp_err[0])
            else:
                IBN_f_hp_meas.append(0)
                IBN_f_hp_err_meas.append(0)
            if IBN_R_off[0]:
                IBN_R_off_meas.append(IBN_R_off[0])
                IBN_R_off_err_meas.append(IBN_R_off_err[0])
            else:
                IBN_R_off_meas.append(0)
                IBN_R_off_err_meas.append(0)
            if IBN_C_in[0]:
                IBN_C_in_meas.append(IBN_C_in[0])
                IBN_C_in_err_meas.append(IBN_C_in_err[0])
            else:
                IBN_C_in_meas.append(0)
                IBN_C_in_err_meas.append(0)
        plt.close()
        return IBN_Gain_meas, IBN_Gain_err_meas, IBN_f_hp_meas, IBN_f_hp_err_meas, IBN_R_off_meas, IBN_R_off_err_meas, IBN_C_in_meas, IBN_C_in_err_meas #IBP_f_tp, IBP_f_tp_err, IBP_f_hp, IBP_f_hp_err, IBP_C_in, IBP_C_in_err, IBP_R_off, IBP_R_off_err, IBN_Gain, IBN_Gain_err, IBN_f_tp, IBN_f_tp_err, IBN_f_hp, IBN_f_hp_err, IBN_C_in, IBN_C_in_err, IBN_R_off, IBN_R_off_err

def AC_sweep_PWELL_range(PWELL_SELECTION=[0, -1, -1.5, -2, -2.5, -3, -4, -5]):
    if not load_data:
        IBN_Gain, IBN_Gain_err,IBN_f_hp, IBN_f_hp_err, IBN_R_off, IBN_R_off_err, IBN_C_in, IBN_C_in_err = AC_sweep(PWELL_BIAS_SELECTION=PWELL_SELECTION)
        data_handler.save_data(data=[PWELL_SELECTION, IBN_Gain, IBN_Gain_err,IBN_f_hp, IBN_f_hp_err, IBN_R_off, IBN_R_off_err, IBN_C_in, IBN_C_in_err], header='PWELL_SELECTION, IBN_Gain, IBN_Gain_err, IBN_f_hp, IBN_f_hp_err,  IBN_R_off, IBN_R_off_err, IBN_C_in, IBN_C_in_err', output_path=data_path+'Gain_PWELL_range.csv')
    else:
        data = np.genfromtxt(data_path+'Gain_PWELL_range.csv', delimiter=',')
        PWELL_SELECTION = data[1:,0]
        IBN_Gain = data[1:,1]
        IBN_Gain_err = data[1:,2]
        IBN_f_hp = data[1:,3]
        IBN_f_hp_err  = data[1:,4]
        IBN_R_off = data[1:,5]
        IBN_R_off_err  = data[1:,6]
        IBN_C_in  = data[1:,7]
        IBN_C_in_err  = data[1:,8]
    pltfit.beauty_plot(xlabel='PWELL_BIAS / V', ylabel='AC Gain $G_{AC}$',title='IBN AC Gain in dependency of PWELL_BIAS')
    plt.errorbar(x=PWELL_SELECTION, y=IBN_Gain, yerr=IBN_Gain_err, marker='x', linestyle='None')
    plt.savefig(image_path+'AC_GAIN_PWELL_comparison.pdf',bbox_inches='tight')
    plt.show()
    plt.close()
    
    pltfit.beauty_plot(xlabel='PWELL_BIAS / V', ylabel='$R_{off}$ in $\\Omega$',title='$R_{off}$ in dependency of PWELL_BIAS', log_y=True)
    plt.errorbar(x=PWELL_SELECTION, y= IBN_R_off, yerr=IBN_R_off_err, marker='x', linestyle='None')
    plt.savefig(image_path+'R_OFF_PWELL_comparison.pdf',bbox_inches='tight')
    plt.show()
    plt.close()

    pltfit.beauty_plot(xlabel='PWELL_BIAS / V', ylabel='$f_{hp}$ / Hz',title='IBN $f_{hp}$ in dependency of PWELL_BIAS', log_y=True)
    plt.errorbar(x=PWELL_SELECTION, y=IBN_f_hp, yerr=IBN_f_hp_err, marker='x', linestyle='None')
    plt.savefig(image_path+'f_hp_PWELL_comparison.pdf',bbox_inches='tight')
    plt.show()

    pltfit.beauty_plot(xlabel='PWELL_BIAS / V', ylabel='$C_{in}$ / fF',title='Capacity $C_{in}$ in dependency of PWELL_BIAS', log_y=False)
    plt.errorbar(x=PWELL_SELECTION, y=IBN_C_in, yerr=IBN_C_in_err, marker='x', linestyle='None')
    plt.savefig(image_path+'C_in_PWELL_comparison.pdf',bbox_inches='tight')
    plt.show()

#AC_sweep()
AC_sweep_PWELL_range()
