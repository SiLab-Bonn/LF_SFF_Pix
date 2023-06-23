import numpy as np
import utils.plot_fit as pltfit
import matplotlib.pyplot as plt

def fast_online_analysis(data, baseline):
    #return np.max(np.greater(data-baseline,threshold), initial=-1)
    return np.min(data)

def fast_triggered_signal(data, baseline_end, skip_region, signal_duration, title, image_path, control_pics=False):
    baseline = np.average(data[:baseline_end])
    event = np.min(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])#np.average(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])
    if control_pics:
        pltfit.beauty_plot(figsize=[10,10], xlabel='ADC data points', ylabel='ADC units', title=title, fontsize=20)
        plt.plot(data)
        plt.hlines(baseline, 0, len(data), color='black')
        plt.hlines(event, 0, len(data), color='black')
        plt.savefig(image_path,bbox_inches='tight')
        #plt.show()
        plt.close()
    return baseline, event, 0

def fit_landau(x, y, yerr, p, bounds):
    # p = mpv, eta, sigma, A
    # mpv max
    # eta offset
    # sigma std 
    # A amplitude
    popt, perr = pltfit.fit_landau_yerr(x,y,yerr,p,bounds)  
    return popt, perr

def fit_first_order(data, threshold_x,threshold_y, control_plots = False):
    #data = np.genfromtxt('./output/IR_LED/AC/data/demo_fit_offline_event_analyse.csv', delimiter=',')
    #y = data[1:,0]
    skip_after_peak = 1
    y_max = np.argmax(data)



    data_min_pos = np.argmin(data)
    data_max_pos = np.argmax(data)
    if data_min_pos-data_max_pos <= threshold_x and data_min_pos-data_max_pos>0 and data[data_max_pos]-data[data_min_pos]>threshold_y:
        #### 
        # First order approximation
        ####
        y_base = data[:y_max]
        y_event = data[y_max+skip_after_peak:]
        x_event = np.linspace(y_max+skip_after_peak, len(data), len(data)-y_max-skip_after_peak)
        x_base = np.linspace(0, y_max, y_max)
        popt_base, perr_base = pltfit.no_err(pltfit.func_lin, x=x_base, y=y_base, presets=[0,0])
        popt_event, perr_event = pltfit.no_err(pltfit.func_lin, x=x_event, y=y_event, presets=[0,0])
        event_point = np.array([pltfit.func_lin(x = x_base[-1] , p=popt_base),pltfit.func_lin(x = x_event[0] , p=popt_event)])

        if control_plots:
            plt.close()
            plt.plot(data)     
            plt.plot(np.array([x_base[-1], x_event[0]]), event_point, color='black')
            plt.plot(x_base, pltfit.func_lin(p=popt_base, x=x_base), color='black')
            plt.plot(x_event, pltfit.func_lin(x=x_event, p=popt_event), color='black')
            plt.show()
        return event_point[0], event_point[1]
    else:
        return None, None

def smooth_data(y, box_pts=10):
    return np.convolve(y, np.ones(box_pts)/box_pts, mode='same')[int(box_pts/2):-int(box_pts/2)]

def fit_exp(data, title, threshold_y, control_plots=False, area=None, image_path=None, smooth_data=False, calibrate_data=False):
    if calibrate_data:
        pltfit.beauty_plot(xlabel='ADC data points', ylabel='Voltage U / V', title=title, fontsize=20)
    else:
        pltfit.beauty_plot(xlabel='ADC data points', ylabel='ADC units', title=title, fontsize=20)
    plt.plot(data, label='measured data')
    
    if smooth_data: data = smooth_data(data)
    data_min = np.min(data)
    data_min_pos = np.argmin(data)
   
    baseline_avoid_fitting_event = 10
    x_baseline = np.linspace(0, len(data[:data_min_pos-baseline_avoid_fitting_event]), len(data[:data_min_pos-baseline_avoid_fitting_event]))
    y_baseline = data[:data_min_pos-baseline_avoid_fitting_event]
    popt_base, perr_base = pltfit.no_err(pltfit.func_const, x=x_baseline, y=y_baseline, presets=[np.average(y_baseline)])

    x_event = np.linspace(data_min_pos, len(data),len(data)-data_min_pos)    
    y_event = data[data_min_pos:]
    popt_event, perr_event = pltfit.no_err(pltfit.func_exp, x=x_event, y=y_event, presets=[-(np.average(y_baseline)-data_min),-4.82084142e-03,2.73505430e+00, popt_base[0]])
    if np.abs(pltfit.func_exp(p=popt_event, x=data_min_pos))>=popt_base[0]-threshold_y:
        plt.close()
        return None, None, None
    if control_plots:
        if smooth_data: plt.plot(data, label='smoothed data')
        plt.plot(x_baseline, pltfit.func_const(p=popt_base, x=x_baseline),color='black')
        plt.plot(x_event, pltfit.func_exp(p=popt_event, x=x_event), color='black', label = '$(%.3f\\pm %.3f)\\cdot\\exp(\\frac{-(x-(%.3f\\pm %.3f))}{(%.3f\\pm %.3f)})+(%.3f\\pm %.3f)$'%(popt_event[0], perr_event[0],popt_event[1], perr_event[1],popt_event[2], perr_event[2], popt_event[3], perr_event[3]))
        plt.plot([data_min_pos-baseline_avoid_fitting_event,data_min_pos], [pltfit.func_const(p=popt_base, x=data_min_pos-baseline_avoid_fitting_event),pltfit.func_exp(p=popt_event, x=(data_min_pos))], color='black')
        plt.legend()
        plt.show()
        if image_path:
            plt.savefig(image_path,bbox_inches='tight')    
    plt.close()

    return popt_base[0], pltfit.func_exp(p=popt_event, x=data_min_pos), popt_event[2]




def online_analyser(data, threshold_x, threshold_y):
    data_min_pos = np.argmin(data)
    data_max_pos = np.argmax(data)
    if data_min_pos-data_max_pos <= threshold_x and data_min_pos-data_max_pos>0 and data[data_max_pos]-data[data_min_pos]>threshold_y:
        return np.average(data[:data_max_pos]),data[data_min_pos]
    else:
        return None, None
    
