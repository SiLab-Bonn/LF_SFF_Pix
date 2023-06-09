import numpy as np
import utils.plot_fit as pltfit
import matplotlib.pyplot as plt

def fast_online_analysis(data, baseline):
    #return np.max(np.greater(data-baseline,threshold), initial=-1)
    return np.min(data)

def fast_triggered_signal(data, baseline_end, skip_region, signal_duration):
    baseline = np.average(data[:baseline_end])
    event = np.min(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])#np.average(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])
    return baseline, event

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

def fit_exp(data,title, threshold_x,threshold_y, control_plots=False, area=None, image_path=None):
    skip_after_peak = 1
    y_max = np.argmax(data)
    box_pts = 30
    data1 = np.convolve(data, np.ones(box_pts)/box_pts, mode='same')

    data1=data1[int(box_pts/2):-int(box_pts/2)]
    
    data_min = np.min(data1)
    data_min_pos = np.argmin(data1)+int(box_pts/2)
    if data_min_pos >= len(data1):
        return None, None
    if np.abs(np.average(data))-np.abs(data_min)>=threshold_y:
        try:
            baseline_end = data_min_pos-20
            if baseline_end <= 0:
                baseline_end = 0
            x_baseline = np.linspace(0, baseline_end, baseline_end)
            y_baseline = data[:baseline_end]

            x_event = np.linspace(data_min_pos, len(data), len(data)-data_min_pos) 
            y_event = data[data_min_pos:]
            
            popt_base, perr_base = pltfit.no_err(pltfit.func_const, x=x_baseline, y=y_baseline, presets=[np.average(y_baseline)])

            popt_event, perr_event = pltfit.no_err(pltfit.func_exp, x=x_event, y=y_event, presets=[-1.29409829e+01,-4.82084142e-03,2.73505430e+00, popt_base[0]])
            event_point = [pltfit.func_const(x=x_baseline[-1], p=popt_base),pltfit.func_exp(x=x_event[0], p=popt_event)]
            if popt_event[0]>=0 or popt_event[0]<=-1e3 or event_point[0] <= 0 or event_point[1] <= 0:
                return None, None 
            if area:
                if not (event_point[0] >= area[0] and event_point[0] <= area[1] and event_point[1] >= area[0] and event_point[1] <= area[1]):
                    return None, None 
            if control_plots:
                pltfit.beauty_plot(figsize=[10,10], xlabel='ADC data points', ylabel='ADC units', title=title, fontsize=20)
                plt.plot(data, label='measured data')
                plt.plot(np.linspace(box_pts/2, len(data)-box_pts/2, len(data)-box_pts),data1, alpha=0.8, label='smoothed data')    
                #plt.plot(data_min_pos, data1[data_min_pos], marker='x', color='black')
                plt.plot([x_baseline[-1],x_event[0]], event_point, color='black')
                plt.plot(x_event, pltfit.func_exp(x=x_event, p=popt_event), color='black')
                plt.plot(x_baseline, pltfit.func_const(x=x_baseline, p=popt_base), color='black', label='fit')
                plt.legend()
                if image_path:
                    plt.savefig(image_path)
                plt.close()
                #plt.show()
            print(event_point)
            return event_point[0], event_point[1]
        except:
            return None, None

    else:
        return None, None



def online_analyser(data, threshold_x, threshold_y):
    data_min_pos = np.argmin(data)
    data_max_pos = np.argmax(data)
    if data_min_pos-data_max_pos <= threshold_x and data_min_pos-data_max_pos>0 and data[data_max_pos]-data[data_min_pos]>threshold_y:
        return np.average(data[:data_max_pos]),data[data_min_pos]
    else:
        return None, None
    
