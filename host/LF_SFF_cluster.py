# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
#
# 
#
# PIXEL LAYOUT:
# 3 7 11 15
# 2 6 10 14
# 1 5  9 13
# 0 4  8 12
#
# Choose a corner pixel in the center like 6 to trigger on -> 6,5,9
# 
# Set oszi time window to 40mus 

 
from os import walk
import numpy as np
from utils.initialize_measurement import initialize_measurement as init_meas
import matplotlib.pyplot as plt
import utils.pulse_analyzer as pa
import utils.data_handler as data_handler
from lab_devices.tektronix_MSO54 import oscilloscope
import yaml
import utils.plot_fit as pltfit

def analyize_pixel_combination(CH1_pixel, CH2_pixel, CH3_pixel, CH4_pixel, amplitude_CH1, amplitude_CH2, amplitude_CH3, amplitude_CH4):
    # Pixel configurations
    # 0: No data taken
    # 1: single pixel
    # 2: neighboring pixel 
    # 3: two diagonal neighboring pixels
    # 4: All three pixels
    # 5: veto from outside pixel

    if not amplitude_CH1:
        return 0
    if not amplitude_CH4:
        if amplitude_CH1 and not amplitude_CH2 and not amplitude_CH3:
            return 1
        if amplitude_CH2 and not amplitude_CH3:
            return 2
        if not amplitude_CH2 and amplitude_CH3:
            return 3
        if amplitude_CH2 and amplitude_CH3:
            return 4
    else:
        return 5

def plot_subfigure(x, y, baseline, y_min, y_min_pos, amplitude, x_window, pixel, matrix, ax):
    x_lower_lim = int((x[0]+x_window[0])//abs(x[1]-x[0]))
    x_upper_lim = int((x[0]+x_window[1])//abs(x[1]-x[0]))
    ax.plot(x,y, label='data')
    x_smooth, y_smooth = pa.smooth_data(y, x_lims=[np.min(x), np.max(x)], box_pts=30)
    ax.plot(x_smooth, y_smooth, label='smoothed_data')
    if amplitude:
        ax.hlines(baseline, x_window[0], 0, color='black', label='baseline')
        ax.plot(x[y_min_pos], y_min, marker='x', color='black', label='minimum')
    ax.set_title('Matrix %i: Pixel %i'%(matrix, pixel))
    ax.set_ylim(np.min(y)-0.01, np.max(y)+0.01)
    ax.vlines(x[x_lower_lim], -10000, 10000, colors='black', linestyle='--', label='selection')
    ax.vlines(x[x_upper_lim], -10000, 10000, colors='black', linestyle='--')
    ax.set_xlabel('s')
    ax.set_ylabel('Voltage V')
    ax.grid()
    ax.legend(loc='lower left')

def plot_subfigures_oszi(x, y, baseline, y_min, y_min_pos, amplitude, x_window, pixel, matrix, ax):
    ax.plot(x,y)
    if amplitude:
        ax.hlines(baseline, np.min(x), np.max(x), linestyle='--', label='baseline', color='black')
        ax.hlines(y_min, np.min(x), np.max(x), label='minimum', color='black')
        ax.set_xlabel('s')
    ax.set_title('Matrix %i: Pixel %i'%(matrix, pixel))
    ax.set_ylim(np.min(y)-0.01, np.max(y)+0.01)

    ax.set_ylabel('Voltage V')
    ax.grid()
    ax.legend(loc='lower left')


def cluster_analysis(data_path, y_threshold, source, PWELL, DIODE_HV, matrix=1, pixel=[3,7,2,6], x_window=[-0.005, 0.005], control_pics=False, capture=True, n_events=100):
    data_path = image_path+'/%s_%.1f_%i/'%(source, DIODE_HV, PWELL)
    filenames = next(walk(data_path), (None, None, []))[2]
    failed = 0
    analyzed = 0
    n_captured = 0
    amplitude_CH = [[],[],[],[]]
    if not load_data:
        if capture:
            print('Measuring using Oscilloscope')
            oszi = oscilloscope(yaml.load(open("./lab_devices/tektronix_MSO54.yaml", 'r'), Loader=yaml.Loader))
            oszi.init() 
            previous_trigger_state = 'READY'
            while n_captured!=n_events:
                amplitude_CH_meas = []
                baseline_CH = []
                y_min_CH = []
                y_min_pos_CH = []
                trigger_state = oszi['Oscilloscope'].get_trigger_state()
                fig, ax = plt.subplots(4)
                fig.tight_layout()
                fig.set_figheight(12)
                fig.set_figwidth(16)
                if 'TRIGGER' in trigger_state and previous_trigger_state!=trigger_state:
                    CH1 = oszi['Oscilloscope'].get_waveform(channel=1, continue_meas=False)
                    CH2 = oszi['Oscilloscope'].get_waveform(channel=2, continue_meas=False)
                    CH3 = oszi['Oscilloscope'].get_waveform(channel=3, continue_meas=False)
                    CH4 = oszi['Oscilloscope'].get_waveform(channel=4, continue_meas=True)
                    time = oszi.gen_waveform_x(CH1)
                    time = np.array(time)-np.max(time)/2
                    CH_combined = [CH1[1], CH2[1], CH3[1], CH4[1]]
                    for i in range(1, 5):
                        CH = CH_combined[i-1]
                        baseline_CH_measurement, amplitude_CH_measurement, y_min_CH_measurement, y_min_pos_CH_measurement = pa.fast_amplitude(x=time, y=CH, center=0, x_window=x_window, channel='CH'+str(i), pixel=pixel[i-1], y_threshold=y_threshold, smooth=True)
                        amplitude_CH[i-1].append(amplitude_CH_measurement)
                        amplitude_CH_meas.append(amplitude_CH_measurement)
                        baseline_CH.append(baseline_CH_measurement)
                        y_min_CH.append(y_min_CH_measurement)
                        y_min_pos_CH.append(y_min_pos_CH_measurement)
                        if control_pics: plot_subfigures_oszi(time, CH, baseline_CH_measurement, y_min_CH_measurement, y_min_pos_CH_measurement, amplitude_CH_measurement, x_window, pixel[i-1], matrix, ax[i-1])                    
                    if control_pics: plt.savefig(data_path+'/figs/capture_'+str(n_captured)+'.png')
                    if amplitude_CH_meas[0]:
                        data_handler.save_data([time, CH1[1], CH2[1], CH3[1], CH4[1]], data_path+'data/waveforms/waveform_'+str(n_captured)+'.csv', header='time, CH1[1], CH2[1], CH3[1], CH4[1]')
                        n_captured += 1
                        print('Captured %i/%i events'%(n_captured, n_events))
                        data_handler.save_data([pixel[0], baseline_CH[0], amplitude_CH_meas[0], y_min_CH[0], y_min_pos_CH[0],
                            pixel[1], baseline_CH[1], amplitude_CH_meas[1], y_min_CH[1], y_min_pos_CH[1],
                            pixel[2], baseline_CH[2], amplitude_CH_meas[2], y_min_CH[2], y_min_pos_CH[2],
                            pixel[3], baseline_CH[3], amplitude_CH_meas[3], y_min_CH[3], y_min_pos_CH[3]], data_path+'data/results_'+str(n_captured),
                            'pixel, baseline_CH1, amplitude_CH1, y_min_CH1, y_min_pos_CH1,pixel, baseline_CH2, amplitude_CH2, y_min_CH2, y_min_pos_CH2,pixel, baseline_CH3, amplitude_CH3, y_min_CH3, y_min_pos_CH3,pixel, baseline_CH4, amplitude_CH4, y_min_CH4, y_min_pos_CH4')              
                    else:
                        print('No amplitude measured')
                plt.close()
                previous_trigger_state = trigger_state
        else:
            CH1_pixel = pixel[0]
            CH2_pixel = pixel[1]
            CH3_pixel = pixel[2]
            CH4_pixel = pixel[3]
            #amplitude_CH1 = data[2]
            #amplitude_CH2 = data[7]
            #amplitude_CH3 = data[12]
            #amplitude_CH4 = data[17]
            for file in filenames:
                    try:
                        print(file)
                        analyzed+=1
                        fig, ax = plt.subplots(4)
                        fig.tight_layout()
                        fig.set_figheight(12)
                        fig.set_figwidth(16)
                        data = np.genfromtxt(data_path+file, delimiter=',', skip_header=12)
                        time = data[0:,0]

                        for i in range(1, 5):
                            CH = data[0:,i]
                            baseline_CH, amplitude_CH_measurement, y_min_CH, y_min_pos_CH = pa.fast_windowed_amplitude(x=time, y=CH, center=0, x_window=x_window, channel='CH'+str(i), pixel=pixel[i], y_threshold=y_threshold, smooth=True)
                            amplitude_CH[i].append(amplitude_CH_measurement)
                            amplitude_CH_meas.append(amplitude_CH_measurement)
                            baseline_CH.append(baseline_CH)
                            y_min_CH.append(y_min_CH)
                            y_min_pos_CH.append(y_min_pos_CH)
                            if control_pics: plot_subfigure(time, CH, baseline_CH, y_min_CH, y_min_pos_CH, amplitude_CH, x_window, pixel[i], matrix, ax[i])
                        '''
                        CH1 = data[0:,1]
                        baseline_CH1, amplitude_CH1_meas, y_min_CH1, y_min_pos_CH1 = pa.fast_windowed_amplitude(x=time, y=CH1, center=0, x_window=x_window, channel='CH1', pixel=pixel[0], y_threshold=y_threshold, smooth=True)
                        amplitude_CH1.append(amplitude_CH1_meas)
                        if control_pics: plot_subfigure(time, CH1, baseline_CH1, y_min_CH1, y_min_pos_CH1, amplitude_CH1, x_window, pixel[0], matrix, ax[0])
                        CH2 = data[0:,2]
                        baseline_CH2, amplitude_CH2_meas, y_min_CH2, y_min_pos_CH2 = pa.fast_windowed_amplitude(x=time, y=CH2, center=0, x_window=x_window, channel='CH2', pixel=pixel[0], y_threshold=y_threshold)
                        amplitude_CH2.append(amplitude_CH2_meas)
                        if control_pics: plot_subfigure(time, CH2, baseline_CH2, y_min_CH2, y_min_pos_CH2, amplitude_CH2, x_window, pixel[1], matrix, ax[1])

                        CH3 = data[0:,3]
                        baseline_CH3, amplitude_CH3_meas, y_min_CH3, y_min_pos_CH3 = pa.fast_windowed_amplitude(x=time, y=CH3, center=0, x_window=x_window, channel='CH3', pixel=pixel[0], y_threshold=y_threshold)
                        amplitude_CH3.append(amplitude_CH3_meas)
                        if control_pics: plot_subfigure(time, CH3, baseline_CH3, y_min_CH3, y_min_pos_CH3, amplitude_CH3, x_window, pixel[2], matrix, ax[2])

                        CH4 = data[0:,4]
                        baseline_CH4, amplitude_CH4_meas, y_min_CH4, y_min_pos_CH4 = pa.fast_windowed_amplitude(x=time, y=CH4, center=0, x_window=x_window, channel='CH4', pixel=pixel[0], y_threshold=y_threshold)
                        amplitude_CH4.append(amplitude_CH4_meas)
                        if control_pics: plot_subfigure(time, CH4, baseline_CH4, y_min_CH4, y_min_pos_CH4, amplitude_CH4, x_window, pixel[3], matrix, ax[3])

                        if control_pics:
                            plt.legend()
                            plt.savefig(data_path+'figs/'+file[:-4]+'.png')
                        data_handler.save_data([pixel[0], baseline_CH1, amplitude_CH1_meas, y_min_CH1, y_min_pos_CH1,
                                                pixel[1], baseline_CH2, amplitude_CH2_meas, y_min_CH2, y_min_pos_CH2,
                                                pixel[2], baseline_CH3, amplitude_CH3_meas, y_min_CH3, y_min_pos_CH3,
                                                pixel[3], baseline_CH4, amplitude_CH4_meas, y_min_CH4, y_min_pos_CH4], data_path+'data/results_'+file,
                                                'pixel, baseline_CH1, amplitude_CH1, y_min_CH1, y_min_pos_CH1,pixel, baseline_CH2, amplitude_CH2, y_min_CH2, y_min_pos_CH2,pixel, baseline_CH3, amplitude_CH3, y_min_CH3, y_min_pos_CH3,pixel, baseline_CH4, amplitude_CH4, y_min_CH4, y_min_pos_CH4')
                        '''
                        if control_pics:
                            plt.legend()
                            plt.savefig(data_path+'figs/'+file[:-4]+'.png')
                        data_handler.save_data([pixel[0], baseline_CH[0], amplitude_CH_meas[0], y_min_CH[0], y_min_pos_CH[0],
                                                pixel[1], baseline_CH[1], amplitude_CH_meas[1], y_min_CH[1], y_min_pos_CH[1],
                                                pixel[2], baseline_CH[2], amplitude_CH_meas[2], y_min_CH[2], y_min_pos_CH[2],
                                                pixel[3], baseline_CH[3], amplitude_CH_meas[3], y_min_CH[3], y_min_pos_CH[3]], data_path+'data/results_'+file,
                                                'pixel, baseline_CH1, amplitude_CH1, y_min_CH1, y_min_pos_CH1,pixel, baseline_CH2, amplitude_CH2, y_min_CH2, y_min_pos_CH2,pixel, baseline_CH3, amplitude_CH3, y_min_CH3, y_min_pos_CH3,pixel, baseline_CH4, amplitude_CH4, y_min_CH4, y_min_pos_CH4')
                    except:
                        failed+=1
                        print('failed to analyze (%i/%i):'%(failed, analyzed), file)

    filenames = next(walk(data_path+'data/'), (None, None, []))[2]
    CH1_pixel = []
    CH2_pixel = []
    CH3_pixel = []
    CH4_pixel = []
    amplitude_CH1 = []
    amplitude_CH2 = []
    amplitude_CH3 = []
    amplitude_CH4 = []
    cluster = []
    for file in filenames:
        data = np.nan_to_num(np.genfromtxt(data_path+'data/'+file, skip_header=1, delimiter=','), 0)
        CH1_pixel.append(data[0])
        CH2_pixel.append(data[5])
        CH3_pixel.append(data[10])
        CH4_pixel.append(data[15])
        amplitude_CH1.append(data[2])
        amplitude_CH2.append(data[7])
        amplitude_CH3.append(data[12])
        amplitude_CH4.append(data[17])
    for i in range(len(CH1_pixel)):
        cluster.append(analyize_pixel_combination(CH1_pixel[i], CH2_pixel[i], CH3_pixel[i], CH4_pixel[i], amplitude_CH1[i], amplitude_CH2[i], amplitude_CH3[i], amplitude_CH4[i]))

    data_handler.save_data(data=[cluster], header='cluster', output_path=data_path+'/data/cluster/cluster.csv')
    pltfit.beauty_plot(xlabel='cluster', ylabel='counts', title='%s (Pixel Matrix=%i, Pixel=[%i,%i,%i], PWELL=%.2fV, DIODE_HV=%.2fV, %i events)'%(source, matrix, pixel[0],pixel[1],pixel[2], PWELL, DIODE_HV, len(filenames)))
    #plt.hist(cluster, label='Pixel configurations\n 1: single pixel\n 2: neighboring pixel\n 3: two diagonal neighboring pixels\n 4: L shape\n 5: veto from outside pixel')
    labels, counts = np.unique(cluster, return_counts=True)
    plt.bar(labels, counts, align='center',label='Pixel configurations\n 1: single pixel\n 2: neighboring pixel\n 3: two diagonal neighboring pixels\n 4: L shape\n 5: signal in surrounding pixels', edgecolor='black')
    plt.legend()
    plt.savefig(data_path+'cluster_histo.pdf', bbox_inches='tight')
    plt.show()
    
    pltfit.beauty_plot(xlabel='Amplitude / V', ylabel='counts', title='%s (Pixel Matrix=%i, Pixel=[%i,%i,%i], PWELL=%.2fV, DIODE_HV=%.2fV, %i events)'%(source, matrix, pixel[0],pixel[1],pixel[2], PWELL, DIODE_HV, len(filenames)))
    bins= np.arange(0, np.max(amplitude_CH1), 1/1000)
    plt.hist(amplitude_CH1, bins=bins, label='Pixel %i'%(pixel[0]),alpha=0.7, edgecolor='black')
    plt.hist(amplitude_CH2, bins=bins, label='Pixel %i'%(pixel[1]),alpha=0.7, edgecolor='black')
    plt.hist(amplitude_CH3, bins=bins, label='Pixel %i'%(pixel[2]),alpha=0.7, edgecolor='black')
    plt.hist(amplitude_CH4, bins=bins, label='Sum of other pixels',alpha=0.7, edgecolor='black')
    plt.hist(np.array(amplitude_CH1)+np.array(amplitude_CH2)+np.array(amplitude_CH3)+np.array(amplitude_CH4), bins=bins, label='Sum of all pixels',alpha=0.8, edgecolor='black')
    plt.legend()
    plt.savefig(data_path+'spectrum.pdf', bbox_inches='tight')
    plt.show()
            
        

load_data, chip_version, image_path, data_path = init_meas('cluster')


cluster_analysis(data_path, y_threshold=0.003, matrix=2, pixel=[6,5,9,42], control_pics=True, capture=True, x_window=[-5*1e-6,5*1e-6], source='Cd109', PWELL=-6, DIODE_HV=0.4, n_events=1000)