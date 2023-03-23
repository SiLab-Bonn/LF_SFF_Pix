# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# Hardware Setup DC/AC:
#                   ______
#        VSRC0 (DC)|      |                        
#                  |      | PIX_INPUT (DC)             
#        -----------------------                   
#  ----- | MIO | GPIO | LF_SFF |       
#  |     -----------------------            
#  |               |______|
#  |        VSRC3 (AC/DC)  Pixel 10              
#  PC                      Matrix 1               
#                  
#                                 
#

import time
import numpy as np

from lab_devices.LF_SFF_MIO import LF_SFF_MIO
from lab_devices.oscilloscope import oscilloscope
from lab_devices.function_generator import function_generator
import utils.plot_fit as pltfit
import utils.data_handler as data_handler

import matplotlib.pyplot as plt
import yaml
import sys

#######################################################################
# The main function that can also be called from DAQ and other scripts
#######################################################################


def DC_sweep(DC=False, use_pix_in=False, load_data=False, use_oszi = False):
    #Define IBN, IBP, VRESET scan range
    IBN = [80,82,85,87,90,92,95,97,100]
    IBP = [-5,-6,-7,-8,-9,-10]
    I_unit = 'uA'
    VRESET = np.array([0.05*i for i in range(0,10)])
    VRESET = np.append(VRESET, np.linspace(0.5,1.2,8))
    VRESET_start = 1.2

    colors = ['steelblue', 'blue', 'indigo', 'cyan', 'magenta', 'green', 'darkgreen', 'orange', 'red', 'crimson', 'deeppink', 'lightseagreen', 'darkslategray', 'teal', 'darkgoldenrod', 'goldenrod', 'indianred',
              'maroon', 'coral', 'sandybrown', 'peachpuff', 'peru']

    image_path = './output/DC_sweeps/AC/'
    data_path = image_path+'data/'
    threshold = 0.3
    
    chip_version = 'AC'
    if 'DC' in sys.argv[1:] or DC==True:
        chip_version='DC'
        image_path = './output/DC_sweeps/DC/'
        data_path = image_path+'data/'
        use_pix_in = True  
    #################################
    # Setup lab devices and DUT
    #################################
    if 'load_data' in sys.argv[1:]:
        load_data = True
    if not load_data:
        try:
            dut = LF_SFF_MIO(yaml.load(open("./lab_devices/LF_SFF_MIO.yaml", 'r'), Loader=yaml.Loader))
            dut.init()
            dut.boot_seq()
            dut.load_defaults(VRESET = VRESET_start)
        except:
            print('Firmware not flashed. This can be because a firmware was already flashed or your setup is broken')
        if use_oszi:
            oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_tds_3034b.yaml", 'r'), Loader=yaml.Loader))
            oszi.init()
            
            oszi.load_dc_sweep_config()

        #################################
        # Begin Measurement 
        #################################

        print(chip_version)
        IBN_In = [[] for i in range(0, len(IBN))]
        IBN_In_err = [[] for i in range(0, len(IBN))]
        IBN_meas = [[] for i in range(0, len(IBN))]
        IBN_VOUT = [[] for i in range(0, len(IBN))]
        IBN_VOUT_err = [[] for i in range(0, len(IBN))]
    
        IBP_In = [[] for i in range(0, len(IBP))]
        IBP_In_err = [[] for i in range(0, len(IBP))]
        IBP_meas = [[] for i in range(0, len(IBP))]
        IBP_VOUT = [[] for i in range(0, len(IBP))]
        IBP_VOUT_err = [[] for i in range(0, len(IBP))]
        if use_pix_in:
            dut['CONTROL']['RESET'] = 0x0
            dut['CONTROL'].write()
            time.sleep(2)
            if use_oszi:
                vertical_pos = float(oszi['Oscilloscope'].get_vertical_position(channel=2).split(' ')[1])
                vertical_scale = float(oszi['Oscilloscope'].get_vertical_scale(channel=2).split(' ')[1])
                baseline = vertical_pos*vertical_scale
            time.sleep(1)

        else:
            if use_oszi:
                vertical_pos = float(oszi['Oscilloscope'].get_vertical_position(channel=2).split(' ')[1])
                vertical_scale = float(oszi['Oscilloscope'].get_vertical_scale(channel=2).split(' ')[1])
                baseline = vertical_pos*vertical_scale
            dut['CONTROL']['RESET'] = 0x1
            dut['CONTROL'].write()
            dut['VRESET'].set_voltage(1.2, unit='V')

        for V in VRESET:
            
            dut['VRESET'].set_voltage(V,unit='V')
            time.sleep(0.2)
            print('----------------------\nV_in =',V,'V')
            for I in IBN:
                pos = IBN.index(I)
                dut['IBN'].set_current(I,unit=I_unit)
                time.sleep(0.5)
                IBN_meas[pos].append(dut['IBN'].get_current(unit=I_unit))
                if use_oszi:
                    waveform = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)[1]
                    IBN_VOUT[pos].append(((np.average(waveform))-baseline)*1000)
                    IBN_VOUT_err[pos].append(np.std(waveform)*1000)
                else:
                    IBN_VOUT[pos].append((dut['AUX_ADC'].get_voltage(unit='mV')))
                    IBN_VOUT_err[pos].append(10)
                IBN_In[pos].append(dut['VRESET'].get_voltage(unit='V')) 
                IBN_In_err[pos].append(0.002) 
                print('IBN =', I,'uA', '| V_IN =', np.round(IBN_In[pos][-1],3),'V', '| V_OUT =', np.round(IBN_VOUT[pos][-1]/1000,3),'V')
            dut['IBN'].set_current(IBN[-1],unit=I_unit)
            for I in IBP:
                pos = IBP.index(I)
                dut['IBP'].set_current(I,unit=I_unit)
                time.sleep(0.5)
                IBP_meas[pos].append(dut['IBP'].get_current(unit=I_unit))
                if use_oszi:
                    waveform = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=True)[1]
                    IBP_VOUT[pos].append(((np.average(waveform))-baseline)*1000)
                    IBP_VOUT_err[pos].append(np.std(waveform)*1000)
                else:
                    IBP_VOUT[pos].append((dut['AUX_ADC'].get_voltage(unit='mV')))
                    IBP_VOUT_err[pos].append(10)
                IBP_In[pos].append(dut['VRESET'].get_voltage(unit='V'))
                IBP_In_err[pos].append(0.02) 
                print('IBP =', I,'uA', '| V_IN =', np.round(IBP_In[pos][-1],3),'V', '| V_OUT =', np.round(IBP_VOUT[pos][-1]/1000,3),'V')

        IBN_meas_err = [1 for i in range(0, len(IBN_meas))]
        IBP_meas_err = [0.1 for i in range(0, len(IBP_meas))]

        IBN_In = np.array(IBN_In)
        IBN_In_err = np.array(IBN_In_err)
        IBN_meas = np.array(IBN_meas)
        IBN_meas_err = np.array(IBN_meas_err)
        IBN_VOUT = np.array(IBN_VOUT)
        IBN_VOUT_err = np.array(IBN_VOUT_err)

        IBP_In = np.array(IBP_In)
        IBP_In_err = np.array(IBP_In_err)
        IBP_meas = np.array(IBP_meas)
        IBP_meas_err = np.array(IBP_meas_err)
        IBP_VOUT = np.array(IBP_VOUT)
        IBP_VOUT_err = np.array(IBP_VOUT_err)

        data_handler.save_sweep(IBX=IBN, IBX_name='IBN', output_path=data_path, iterator=np.array(VRESET), iterator_err=np.array(VRESET)*0, IBX_VIN = IBN_In, IBX_VIN_err= IBN_In_err, IBX_VOUT=IBN_VOUT,IBX_VOUT_err=IBN_VOUT_err)
        data_handler.save_sweep(IBX=IBP, IBX_name='IBP', output_path=data_path, iterator=np.array(VRESET), iterator_err=np.array(VRESET)*0, IBX_VIN = IBP_In, IBX_VIN_err= IBP_In_err, IBX_VOUT=IBP_VOUT,IBX_VOUT_err=IBP_VOUT_err)
        
        data_handler.success_message_data_taking()

    else:
        try:
            IBN_In, IBN_In_err, IBN_VOUT, IBN_VOUT_err = data_handler.load_sweep(data_path=data_path, IBX=IBN, IBX_name='IBN')
            IBP_In, IBP_In_err, IBP_VOUT, IBP_VOUT_err = data_handler.load_sweep(data_path=data_path, IBX=IBP, IBX_name='IBP')
        except:
            print('Some (at least one dataset) data is missing. Please start a new measurement')
    
    #################################
    # Plot the results
    #
    # I. IBN Results
    #################################

    pltfit.beauty_plot(xlabel='$V_{IN}$ / V', ylabel='Gain $G$', title='Gain $G$ vs. $V_{in}$ for different IBN')
    IBN_Gain = []
    IBN_Gain_err = []
    IBN_Gain_IN = []
    IBN_Gain_IN_err = []
    for i in range(0, len(IBN)):
        IBN_Gain.append([])
        IBN_Gain_err.append([])
        for j in range(0, len(IBN_In[i])-1):
                IBN_Gain[i].append((IBN_VOUT[i][j+1]-IBN_VOUT[i][j])/(IBN_In[i][j+1]-IBN_In[i][j])/1000)
                IBN_Gain_err[i].append(np.sqrt((1/(IBN_In[i][j+1]-IBN_In[i][j])/1000*IBN_In_err[i][j+1])**2+(1/(IBN_In[i][j+1]-IBN_In[i][j])/1000*IBN_In_err[i][j])**2+((IBN_VOUT[i][j+1]-IBN_VOUT[i][j])/(IBN_In[i][j+1]-IBN_In[i][j])**2*IBN_In_err[i][j]/1000)**2+((IBN_VOUT[i][j+1]-IBN_VOUT[i][j])/(IBN_In[i][j+1]-IBN_In[i][j])**2*IBN_In_err[i][j+1]/1000)**2))
        IBN_Gain_IN.append([IBN_In[i][j]+(IBN_In[i][j+1]-IBN_In[i][j])/2 for j in range(0, len(IBN_In[i])-1)])
        IBN_Gain_IN_err.append([(IBN_In[i][j+1]-IBN_In[i][j])/2 for j in range(0, len(IBN_In[i])-1)])
        plt.errorbar(x = IBN_Gain_IN[i],xerr=IBN_Gain_IN_err[i], y=IBN_Gain[i], yerr=IBN_Gain_err[i], linestyle='None', marker='.', color=colors[i], label='IBN='+str(IBN[i])+'uA')

    plt.legend()
    plt.savefig(image_path+chip_version+'_IBN_Gain_V_In.png')
    plt.show()

    for i in range(0, len(IBN)):
        data_handler.save_data([IBN_Gain_IN[i],IBN_Gain_IN_err[i], IBN_Gain[i], IBN_Gain_err[i]], data_path+'IBN_'+str(IBN[i])+'_Gain.csv', 'IBN_In, IBN_In_err, Gain, Gain_err')

    # Output vs. V_In  with variable IBN
    # find end of dynamic area:
    end_of_dynamic_area_pos_default = 5
    end_of_dynamic_area = []
    end_of_dynamic_area_pos = []
    for i in range(0, len(IBN)):
        initial_popt = []
        initial_perr = []
        found = False
        for j in range(0, len(IBN_In[i][end_of_dynamic_area_pos_default:])):
            popt, perr = pltfit.double_err(function=pltfit.func_lin, x=IBN_In[i][:end_of_dynamic_area_pos_default+j], y=IBN_VOUT[i][:end_of_dynamic_area_pos_default+j]/1000,x_error=IBN_In_err[i][:end_of_dynamic_area_pos_default+j],y_error=IBN_VOUT_err[i][:end_of_dynamic_area_pos_default+j]/1000, presets=[1,1])
            if j == 0:
                initial_popt = popt
                initial_perr = perr
            else:
                if popt[0]/initial_popt[0]<=1-threshold and found==False:
                    end_of_dynamic_area.append(IBN_In[i][j])
                    end_of_dynamic_area_pos.append(j)
                    found=True

    end_of_dynamic_area = np.average(end_of_dynamic_area)
    end_of_dynamic_area_pos = np.argmin(np.abs(IBP_In[0] - end_of_dynamic_area))
    
    data_handler.save_data([end_of_dynamic_area, end_of_dynamic_area/2], data_path+'IBN_end_of_dynamic_area.csv', 'end_of_dyn_area, end_of_dyn_area/2')

    pltfit.beauty_plot(xlim=[np.min(VRESET), np.max(VRESET)+0.1],ylim=[np.min(IBN_VOUT)-30, np.max(IBN_VOUT)+30],xlabel='$V_{IN}$ / V', ylabel='$V$ / mV', title=chip_version+': VOUT vs. VIN for different IBN')
    for i in range(0, len(IBN_In)):
        IBN_In_slope = IBN_In[i][0:end_of_dynamic_area_pos]
        IBN_In_slope_err = IBN_In_err[i][0:end_of_dynamic_area_pos]
        IBN_VOUT_slope = IBN_VOUT[i][0:end_of_dynamic_area_pos]
        IBN_VOUT_slope_err = IBN_VOUT_err[i][0:end_of_dynamic_area_pos]
        slope_popt, slope_perr = pltfit.double_err(function=pltfit.func_lin, x=IBN_In_slope, y=IBN_VOUT_slope,x_error=IBN_In_slope_err,y_error=IBN_VOUT_slope_err, presets=[1,1])
        plt.errorbar(x=IBN_In[i],y=IBN_VOUT[i], xerr=IBN_In_err[i],yerr=IBN_VOUT_err[i], marker='.', label='IBN = %.1f uA: $V_{Out}=(%.3f\\pm%.3f)\\cdot V_{In}+(%.3f\\pm%.3f)V$'%(IBN[i], slope_popt[0]/1000, slope_perr[0]/1000, slope_popt[1]/1000,slope_perr[1]/1000), linestyle='None', color=colors[i])
        plt.plot(np.linspace(np.min(IBN_In_slope)-0.1, np.max(IBN_In_slope)+0.1,100), pltfit.func_lin(slope_popt,np.linspace(np.min(IBN_In_slope)-0.1, np.max(IBN_In_slope)+0.1,100)), color=colors[i])
    plt.fill_between([-10, end_of_dynamic_area], -1000,1000,alpha=0.2, color='gray')   
    plt.vlines(end_of_dynamic_area,-1000,1000, color='black', linestyle='--')
    plt.text(end_of_dynamic_area+0.01, np.min(IBN_VOUT[0]), 'end of dynamic area: '+str(np.round(end_of_dynamic_area*1000,1))+'mV',rotation = 90)
    plt.vlines(end_of_dynamic_area/2,-1000,1000, color='black', linestyle='--') 
    plt.text(end_of_dynamic_area/2+0.01, np.min(IBN_VOUT[0]), 'ideal DC offset: '+str(np.round(end_of_dynamic_area/2*1000,1))+'mV',rotation = 90)
    plt.legend(loc='right')
    plt.savefig(image_path+chip_version+'_IBN_V_In_VOUT.png')
    plt.show()
    

    #################################
    # Plot the results
    #
    # II. IBP Results
    #################################
    
    pltfit.beauty_plot(xlabel='$V_{IN}$ / V', ylabel='Gain $G$', title='Gain $G$ vs. $V_{in}$ for different IBP')
    IBP_Gain = []
    IBP_Gain_err = []
    IBP_Gain_IN = []
    IBP_Gain_IN_err = []
    for i in range(0, len(IBP)):
        IBP_Gain.append([])
        IBP_Gain_err.append([])
        for j in range(0, len(IBP_In[i])-1):
                IBP_Gain[i].append((IBP_VOUT[i][j+1]-IBP_VOUT[i][j])/(IBP_In[i][j+1]-IBP_In[i][j])/1000)
                IBP_Gain_err[i].append(np.sqrt((1/(IBP_In[i][j+1]-IBP_In[i][j])/1000*IBP_In_err[i][j+1])**2+(1/(IBP_In[i][j+1]-IBP_In[i][j])/1000*IBP_In_err[i][j])**2+((IBP_VOUT[i][j+1]-IBP_VOUT[i][j])/(IBP_In[i][j+1]-IBP_In[i][j])**2*IBP_In_err[i][j]/1000)**2+((IBP_VOUT[i][j+1]-IBP_VOUT[i][j])/(IBP_In[i][j+1]-IBP_In[i][j])**2*IBP_In_err[i][j+1]/1000)**2))
        IBP_Gain_IN.append([IBP_In[i][j]+(IBP_In[i][j+1]-IBP_In[i][j])/2 for j in range(0, len(IBP_In[i])-1)])
        IBP_Gain_IN_err.append([(IBP_In[i][j+1]-IBP_In[i][j])/2 for j in range(0, len(IBP_In[i])-1)])
        plt.errorbar(x = IBP_Gain_IN[i],xerr=IBP_Gain_IN_err[i], y=IBP_Gain[i], yerr=IBP_Gain_err[i], linestyle='None', marker='.', color=colors[i], label='IBP='+str(IBP[i])+'uA')

    plt.legend()
    plt.savefig(image_path+chip_version+'_IBP_Gain_V_In.png')
    plt.show()

    for i in range(0, len(IBP)):
        data_handler.save_data([IBP_Gain_IN[i],IBP_Gain_IN_err[i], IBP_Gain[i], IBP_Gain_err[i]], data_path+'IBP_'+str(IBP[i])+'_Gain.csv', 'IBP_In, IBP_In_err, Gain, Gain_err')

    # Output vs. V_In  with variable IBP
    # find end of dynamic area:
    end_of_dynamic_area_pos_default = 5
    end_of_dynamic_area = []
    end_of_dynamic_area_pos = []
    for i in range(0, len(IBP)):
        initial_popt = []
        initial_perr = []
        found = False
        for j in range(0, len(IBP_In[i][end_of_dynamic_area_pos_default:])):
            popt, perr = pltfit.double_err(function=pltfit.func_lin, x=IBP_In[i][:end_of_dynamic_area_pos_default+j], y=IBP_VOUT[i][:end_of_dynamic_area_pos_default+j]/1000,x_error=IBP_In_err[i][:end_of_dynamic_area_pos_default+j],y_error=IBP_VOUT_err[i][:end_of_dynamic_area_pos_default+j]/1000, presets=[1,1])
            if j == 0:
                initial_popt = popt
                initial_perr = perr
            else:
                if popt[0]/initial_popt[0]<=1-threshold and found==False:
                    end_of_dynamic_area.append(IBP_In[i][j])
                    end_of_dynamic_area_pos.append(j)
                    found=True

    end_of_dynamic_area = np.average(end_of_dynamic_area)
    end_of_dynamic_area_pos = np.argmin(np.abs(IBP_In[0] - end_of_dynamic_area))
    # Save position of dynamic area
    data_handler.save_data([end_of_dynamic_area, end_of_dynamic_area/2], data_path+'IBP_end_of_dynamic_area.csv', 'end_of_dyn_area, end_of_dyn_area/2')


    pltfit.beauty_plot(xlim=[np.min(VRESET), np.max(VRESET)+0.1],ylim=[np.min(IBP_VOUT)-30, np.max(IBP_VOUT)+30],xlabel='$V_{IN}$ / V', ylabel='$V$ / mV', title=chip_version+': VOUT vs. VIN for different IBP')
    for i in range(0, len(IBP_In)):
        IBP_In_slope = IBP_In[i][0:end_of_dynamic_area_pos]
        IBP_In_slope_err = IBP_In_err[i][0:end_of_dynamic_area_pos]
        IBP_VOUT_slope = IBP_VOUT[i][0:end_of_dynamic_area_pos]
        IBP_VOUT_slope_err = IBP_VOUT_err[i][0:end_of_dynamic_area_pos]
        slope_popt, slope_perr = pltfit.double_err(function=pltfit.func_lin, x=IBP_In_slope, y=IBP_VOUT_slope,x_error=IBP_In_slope_err,y_error=IBP_VOUT_slope_err, presets=[1,1])
        plt.errorbar(x=IBP_In[i],y=IBP_VOUT[i], xerr=IBP_In_err[i],yerr=IBP_VOUT_err[i], marker='.', label='IBP = %.1f uA: $V_{Out}=(%.3f\\pm%.3f)\\cdot V_{In}+(%.3f\\pm%.3f)V$'%(IBP[i], slope_popt[0]/1000, slope_perr[0]/1000, slope_popt[1]/1000, slope_perr[1]/1000), linestyle='None', color=colors[i])
        plt.plot(np.linspace(np.min(IBP_In_slope)-0.1, np.max(IBP_In_slope)+0.1,100), pltfit.func_lin(slope_popt,np.linspace(np.min(IBP_In_slope)-0.1, np.max(IBP_In_slope)+0.1,100)), color=colors[i])
    plt.fill_between([-10, end_of_dynamic_area], -1000,1000,alpha=0.2, color='gray')   
    plt.vlines(end_of_dynamic_area,-1000,1000, color='black', linestyle='--')
    plt.text(end_of_dynamic_area+0.01, np.min(IBP_VOUT[0]), 'end of dynamic area: '+str(np.round(end_of_dynamic_area*1000,1))+'mV',rotation = 90)
    plt.vlines(end_of_dynamic_area/2,-1000,1000, color='black', linestyle='--') 
    plt.text(end_of_dynamic_area/2+0.01, np.min(IBP_VOUT[0]), 'ideal DC offset: '+str(np.round(end_of_dynamic_area/2*1000,1))+'mV',rotation = 90)
    plt.legend(loc='right')
    plt.savefig(image_path+chip_version+'_IBP_V_In_VOUT.png')
    plt.show()    

    #####
    # Exit message
    #####
    data_handler.success_message(data_path, image_path)

DC_sweep()